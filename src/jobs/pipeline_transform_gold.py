"""
Camada gold - Transformação Delta Table
Job responsável por acionar a projeção e enriquecimento da Delta Table Silver para a Gold.
"""

import os

project_root = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

from src.gold.transform_gold import process_gold_layer
from src.config.settings import Tables, WRITE_MODE_DEFAULT



def run_transform_gold_pipeline():
    """
    Orquestra a execução da camada gold.
    """

    print("Iniciando o Pipeline de Transformação: Camada Gold...")

    process_gold_layer(
        spark=spark,
        silver_table=f"{Tables.SCHEMA}.{Tables.SILVER_TAXI}",
        table_name=f"{Tables.SCHEMA}.{Tables.GOLD_TAXI}",
        write_mode=WRITE_MODE_DEFAULT
    )

    print("Pipeline da Camada Gold executado com sucesso!")

if __name__ == "__main__":
    run_transform_gold_pipeline()
