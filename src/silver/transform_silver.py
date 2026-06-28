"""
Camada silver - Transformação
Lê da Delta Table bronze, aplica limpeza estrutural e deduplicação, e persiste como Delta Table Silver particionada.
"""

import os
import pyspark.sql.functions as F
from pyspark.sql import Window

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

from src.core.utils import log_execution
from src.config.table_metadata import TAXI_META, SILVER_TABLE_COMMENT, TableMeta
from src.config.settings import DATE_MIN, DATE_MAX



_DEDUP_KEY = ["VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID"]


@log_execution()
def process_silver_layer(spark, bronze_table: str, table_name: str, write_mode: str = "overwrite") -> None:
    """
    Lê da Delta Table bronze, aplica limpeza estrutural, deduplicação e particionamento
    por ano e mês, e persiste na Delta Table Silver.

    Regras aplicadas (estruturais — sem filtros de negócio):
        - Dedup por chave composta, mantendo o registro mais antigo por etl_ingestion_timestamp
        - Remove viagens no tempo (tpep_dropoff_datetime < tpep_pickup_datetime)
        - Remove registros com tpep_pickup_datetime fora do range configurado em settings.py

    Args:
        spark: SparkSession.
        bronze_table: Nome qualificado da Delta Table bronze (schema.tabela).
        table_name: Nome qualificado da Delta Table silver (schema.tabela).
        write_mode: Modo de escrita para Delta Table.
    Returns:
        None
    """

    print(f"Lendo da tabela Bronze: {bronze_table}...")
    df_bronze = spark.table(bronze_table)

    df_silver = _dedup(df_bronze)
    df_silver = _remove_structural_anomalies(df_silver)
    df_silver = _add_partition_columns(df_silver)

    print(f"Gravando registros na Delta Table Silver: {table_name}...")

    (
        df_silver.write
        .format("delta")
        .mode(write_mode)
        .partitionBy("year", "month")
        .saveAsTable(table_name)
    )

    _apply_table_metadata(spark, table_name, TAXI_META, SILVER_TABLE_COMMENT)


def _dedup(df):
    """
    Remove duplicatas pela chave composta, mantendo o registro mais antigo por etl_ingestion_timestamp.
    """

    window = Window.partitionBy(*_DEDUP_KEY).orderBy(F.col("etl_ingestion_timestamp"))
    return (
        df
        .withColumn("_rn", F.row_number().over(window))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )


def _remove_structural_anomalies(df):
    """
    Remove impossibilidades físicas: viagens no tempo e datas fora do range de ingestão configurado.
    """

    return (
        df
        .filter(F.col("tpep_dropoff_datetime") >= F.col("tpep_pickup_datetime"))
        .filter(
            (F.col("tpep_pickup_datetime") >= DATE_MIN) &
            (F.col("tpep_pickup_datetime") <  DATE_MAX)
        )
    )


def _add_partition_columns(df):
    """
    Deriva colunas year e month de tpep_pickup_datetime para particionamento físico da tabela.
    """
    
    return (
        df
        .withColumn("year",  F.year(F.col("tpep_pickup_datetime")))
        .withColumn("month", F.month(F.col("tpep_pickup_datetime")))
    )


def _apply_table_metadata(spark, table_name: str, meta: TableMeta, table_comment: str) -> None:
    """
    Aplica descrições de tabela e colunas via COMMENT ON no catálogo do Databricks (Unity Catalog).
    Colunas presentes em meta mas ausentes na tabela são ignoradas silenciosamente.
    """

    spark.sql(f"COMMENT ON TABLE {table_name} IS '{table_comment.replace(chr(39), chr(92) + chr(39))}'")

    existing_cols = {field.name for field in spark.table(table_name).schema.fields}

    for col in meta.columns:
        if col.name not in existing_cols:
            continue
        safe_col_comment = col.comment.replace("'", "\\'")
        spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col.name} COMMENT '{safe_col_comment}'")