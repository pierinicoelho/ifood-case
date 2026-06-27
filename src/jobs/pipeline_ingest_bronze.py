"""
Camada bronze - Ingestão Delta Table
Job responsável por acionar a ingestão dos dados brutos para a Delta Table Bronze.
"""

import sys
import os

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

from src.bronze.ingest_bronze import process_bronze_layer
from src.config.settings import BRONZE_VOLUME_PATH, Tables, TARGET_YEARS, TARGET_MONTHS, TAXI_TYPES, WRITE_MODE_DEFAULT



def run_ingest_bronze_pipeline():
    """
    Orquestra a execução da camada bronze.
    """
    print("Iniciando o Pipeline de Ingestão: Camada Bronze...")
    
    process_bronze_layer(
        spark=spark,
        volume_path=BRONZE_VOLUME_PATH,
        table_name=f"{Tables.SCHEMA}.{Tables.BRONZE_TAXI}",
        taxi_types=TAXI_TYPES,
        years=TARGET_YEARS,
        months=TARGET_MONTHS,
        write_mode=WRITE_MODE_DEFAULT
    )
    
    print("Pipeline da Camada Bronze executado com sucesso!")

if __name__ == "__main__":
    run_ingest_bronze_pipeline()