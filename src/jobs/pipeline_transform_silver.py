"""
Camada silver - Transformação Delta Table
Job responsável por acionar a limpeza estrutural e deduplicação da Delta Table Bronze para a Silver.
"""

import os

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

from src.silver.transform_silver import process_silver_layer
from src.config.settings import Tables, WRITE_MODE_DEFAULT



def run_ingest_silver_pipeline():
    """
    Orquestra a execução da camada silver.
    """
    
    print("Iniciando o Pipeline de Transformação: Camada Silver...")

    process_silver_layer(
        spark=spark,
        bronze_table=f"{Tables.SCHEMA}.{Tables.BRONZE_TAXI}",
        table_name=f"{Tables.SCHEMA}.{Tables.SILVER_TAXI}",
        write_mode=WRITE_MODE_DEFAULT
    )

    print("Pipeline da Camada Silver executado com sucesso!")

if __name__ == "__main__":
    run_ingest_silver_pipeline()
