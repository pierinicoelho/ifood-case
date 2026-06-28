"""
Configurações de path, schemas e constantes.
"""

### Configurações de path
RAW_VOLUME_PATH = "/Volumes/workspace/ifood_taxi_case/landingzone_raw_taxis"

### URL base do NYC Taxi and Limousine Commission (TLC)
TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

### Regras de negócio para ingestão
TARGET_YEARS = ["2023"]
TARGET_MONTHS = ["01", "02", "03", "04", "05"]
TAXI_TYPES = ["yellow"]

### Range de datas válido para a camada Silver (derivado dos targets acima)
DATE_MIN = f"{TARGET_YEARS[0]}-{TARGET_MONTHS[0]}-01"
DATE_MAX = f"{TARGET_YEARS[0]}-{int(TARGET_MONTHS[-1]) + 1:02d}-01"

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