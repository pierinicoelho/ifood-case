"""
Configurações de path, schemas e constantes.
"""

### Configurações de path
BRONZE_VOLUME_PATH = "/Volumes/workspace/ifood_taxi_case/volume_bronze_taxis"

### URL base do NYC Taxi and Limousine Commission (TLC)
TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

### Regras de negócio para ingestão
TARGET_YEARS = ["2023"]
TARGET_MONTHS = ["01", "02", "03", "04", "05"]
TAXI_TYPES = ["yellow"]

### Entrypoint para nomes das tabelas (Delta Tables)
class Tables:
    """
    Namespace estático para nomes de tabelas.
    """
    SCHEMA = "ifood_taxi_case"
    BRONZE_TAXI = "taxi_bronze"
    SILVER_TAXI = "taxi_silver"
    GOLD_METRICS = "gold_ifood_metrics"

### Modo de escrita padrão do pipeline, em DeltaTables
WRITE_MODE_DEFAULT = "overwrite"