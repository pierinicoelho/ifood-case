"""
Camada gold - Transformação
Lê da Delta Table silver, projeta colunas analíticas, deriva pickup_hour e enriquece
colunas de código numérico com descrições legíveis, e persiste como Delta Table Gold particionada.
"""

import os
import pyspark.sql.functions as F

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

from src.core.utils import log_execution
from src.config.table_metadata import TAXI_META, GOLD_TABLE_COMMENT, TableMeta


_GOLD_COLS = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "total_amount",
    "RatecodeID",
    "payment_type",
    "year",
    "month",
]


@log_execution()
def process_gold_layer(spark, silver_table: str, table_name: str, write_mode: str = "overwrite") -> None:
    """
    Lê da Delta Table silver, projeta colunas analíticas, deriva pickup_hour e enriquece
    colunas de código numérico com descrições legíveis via CASE WHEN, e persiste na Delta Table Gold.
    Sem filtros de camada, mantem a base de dados completa para análises exploratórias e agregações temporais.

    Args:
        spark: SparkSession.
        silver_table: Nome qualificado da Delta Table silver (schema.tabela).
        table_name: Nome qualificado da Delta Table gold (schema.tabela).
        write_mode: Modo de escrita para Delta Table.
    Returns:
        None
    """

    print(f"Lendo da tabela Silver: {silver_table}...")
    df_silver = spark.table(silver_table)

    df_gold = _project_columns(df_silver)
    df_gold = _add_derived_columns(df_gold)
    df_gold = _enrich_code_columns(df_gold)

    print(f"Gravando registros na Delta Table Gold: {table_name}...")

    (
        df_gold.write
        .format("delta")
        .mode(write_mode)
        .partitionBy("year", "month")
        .saveAsTable(table_name)
    )

    _apply_table_metadata(spark, table_name, TAXI_META, GOLD_TABLE_COMMENT)


def _project_columns(df):
    """
    Projeta as colunas definidas em _GOLD_COLS, reduzindo o schema para 
    apenas as colunas analíticas necessárias para a camada gold.
    """

    return df.select(*_GOLD_COLS)


def _add_derived_columns(df):
    """
    Deriva pickup_hour de tpep_pickup_datetime para suporte a agregações temporais por hora.
    """
    
    return df.withColumn("pickup_hour", F.hour(F.col("tpep_pickup_datetime")))


def _enrich_code_columns(df):
    """
    Adiciona descrições legíveis para colunas de código numérico via CASE WHEN.
    Torna a camada de consumo auto-explicativa sem depender de joins externos.
    """

    return (
        df
        .withColumn(
            "vendor_desc",
            F.when(F.col("VendorID") == 1, "Creative Mobile Technologies (CMT)")
            .when(F.col("VendorID") == 2, "VeriFone Inc.")
            .otherwise(F.concat(F.lit("Outro/Inválido: "), F.col("VendorID").cast("string")))
        )
        .withColumn(
            "ratecode_desc",
            F.when(F.col("RatecodeID") == 1, "Standard rate")
            .when(F.col("RatecodeID") == 2, "JFK")
            .when(F.col("RatecodeID") == 3, "Newark")
            .when(F.col("RatecodeID") == 4, "Nassau or Westchester")
            .when(F.col("RatecodeID") == 5, "Negotiated fare")
            .when(F.col("RatecodeID") == 6, "Group ride")
            .otherwise(F.concat(F.lit("Outro/Inválido: "), F.col("RatecodeID").cast("string")))
        )
        .withColumn(
            "payment_desc",
            F.when(F.col("payment_type") == 0, "Flex Fare trip")
            .when(F.col("payment_type") == 1, "Credit card")
            .when(F.col("payment_type") == 2, "Cash")
            .when(F.col("payment_type") == 3, "No charge")
            .when(F.col("payment_type") == 4, "Dispute")
            .when(F.col("payment_type") == 5, "Unknown")
            .when(F.col("payment_type") == 6, "Voided trip")
            .otherwise(F.concat(F.lit("Outro/Inválido: "), F.col("payment_type").cast("string")))
        )
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
