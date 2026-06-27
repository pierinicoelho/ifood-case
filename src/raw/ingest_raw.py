"""
Camada raw - Ingestão
Ingere dados da url para o volume S3, atchado ao databricks como external volume.
"""

import sys
import os

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

import requests
from pyspark.dbutils import DBUtils

from src.core.utils import log_execution



@log_execution()
def download_taxi_data(spark_session, base_url: str, base_path: str, taxi_type: str, year: str, month: str) -> None:
    """
    Faz o download dos arquivos parquet da web para o volume S3 local.
    
    Args:
        spark_session: SparkSession
        base_url: URL base para baixar os dados
        base_path: Caminho base para salvar os dados
        taxi_type: Tipo de táxi (yellow ou green)
        year: Ano dos dados
        month: Mês dos dados
    Returns:
        None
    """

    dbutils = DBUtils(spark_session)
    file_name = f"{taxi_type}_tripdata_{year}-{month}.parquet"
    download_url = f"{base_url}/{file_name}"
    
    target_dir = f"{base_path}/{taxi_type}"
    target_path = f"{target_dir}/{file_name}"

    dbutils.fs.mkdirs(target_dir)

    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    
    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk: 
                f.write(chunk)