"""
Camada raw - Ingestão S3
Job para ingestão dos dados brutos a partir da fonte pública do TLC para volume S3.
"""

import sys
import os

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

from pyspark.sql import SparkSession

from src.config.settings import BRONZE_VOLUME_PATH, TLC_BASE_URL, TARGET_YEARS, TARGET_MONTHS, TAXI_TYPES
from src.ingestion.ingest_raw import download_taxi_data



def run_ingest_raw_pipeline():
    """
    Orquestra a execução da camada raw.
    """
    
    spark = SparkSession.builder.getOrCreate()
    
    print("Iniciando o Pipeline de Ingestão (Camada raw)")
    
    for t_type in TAXI_TYPES:
        for year in TARGET_YEARS:
            for month in TARGET_MONTHS:
                download_taxi_data(
                    spark_session=spark,
                    base_url=TLC_BASE_URL,
                    base_path=BRONZE_VOLUME_PATH,
                    taxi_type=t_type,
                    year=year,
                    month=month
                )
            
    print("Pipeline da Camada raw Concluído!")

if __name__ == "__main__":
    run_ingest_raw_pipeline()