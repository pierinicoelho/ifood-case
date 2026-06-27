"""
Camada bronze - Ingestão
Carrega dados do bucket S3, aplica upcasting com schema enforcement e salva como Delta Table.
"""

import sys
import os
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, TimestampType, StringType, DoubleType

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

from src.core.utils import log_execution
from src.config.table_metadata import TAXI_META, BRONZE_TABLE_COMMENT, TableMeta



@log_execution()
def process_bronze_layer(spark, volume_path: str, table_name: str, taxi_types: list, years: list, months: list, write_mode="overwrite") -> None:
    """
    Ingere arquivos Parquet iterativamente, unifica em memória, normaliza tipos 
    via cast e persiste na Tabela Delta Bronze.

    Args:
        spark: SparkSession.
        volume_path: Path do bucket S3.
        table_name: Nome da Delta Table bronze.
        taxi_types: Lista de tipos de táxi.
        years: Lista de anos.
        months: Lista de meses.
        write_mode: Modo de escrita para Delta Table.
    Returns:
        None
    """

    print("Iniciando ingestão unificada em runtime...")

    all_dfs = []

    for t_type in taxi_types:
        for year in years:
            for month in months:
                file_path = f"{volume_path}/{t_type}/{t_type}_tripdata_{year}-{month}.parquet"
                
                if os.path.exists(file_path.replace("dbfs:", "/dbfs")): # Validação simples de existência
                    print(f"Lendo: {file_path}")
                    df_temp = spark.read.parquet(file_path)
                    df_temp = df_temp.withColumn("source_file_path", F.lit(file_path))
                    all_dfs.append(df_temp)
                    
    if not all_dfs:
        raise ValueError("Nenhum arquivo encontrado para processar.")

    df_union = all_dfs[0]
    for df in all_dfs[1:]:
        df_union = df_union.unionByName(df, allowMissingColumns=True)

    df_bronze = df_union.withColumns({
        "VendorID": F.col("VendorID").cast("long"),
        "passenger_count": F.col("passenger_count").cast("long"),
        "RatecodeID": F.col("RatecodeID").cast("long"),
        "PULocationID": F.col("PULocationID").cast("long"),
        "DOLocationID": F.col("DOLocationID").cast("long"),
        "payment_type": F.col("payment_type").cast("long"),
        "etl_ingestion_timestamp": F.current_timestamp()
    })

    print(f"Gravando registros na Delta Table: {table_name}...")

    (
        df_bronze.write
        .format("delta")
        .mode(write_mode)
        .saveAsTable(table_name)
    )
    
    _apply_table_metadata(spark, table_name, TAXI_META, BRONZE_TABLE_COMMENT)

    print("Ingestão Bronze concluída com sucesso!")


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