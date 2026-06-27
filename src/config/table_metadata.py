"""
Contratos de metadados (descrições de tabelas e colunas) para aplicação via COMMENT ON no catálogo.
As descrições de colunas seguem o Data Dictionary oficial da TLC (NYC Taxi & Limousine Commission).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColumnMeta:
    name: str
    comment: str


@dataclass(frozen=True)
class TableMeta:
    columns: list[ColumnMeta] = field(default_factory=list)


### Descrições por camada — passadas como parâmetro em cada adapter
BRONZE_TABLE_COMMENT = (
    "Camada Bronze: dados brutos de viagens de táxi amarelo (Yellow Taxi) da NYC TLC, "
    "ingeridos as-is com upcasting de tipos para compatibilidade entre meses. "
    "Fonte: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
)
SILVER_TABLE_COMMENT = (
    "Camada Silver: dados de viagens de táxi amarelo limpos e validados estruturalmente. "
    "Single source of truth para consumo analítico e geração da camada Gold."
)
GOLD_TABLE_COMMENT = (
    "Camada Gold: colunas selecionadas de viagens de táxi amarelo para consumo analítico direto, "
    "conforme requisito do case iFood."
)


### Catálogo único de colunas — compartilhado entre todas as camadas
TAXI_META = TableMeta(
    columns=[
        ColumnMeta("VendorID",               "Código do provedor TPEP que gerou o registro. 1=Creative Mobile Technologies LLC, 2=Curb Mobility LLC, 6=Myle Technologies Inc, 7=Helix."),
        ColumnMeta("tpep_pickup_datetime",    "Data e hora em que o taxímetro foi acionado (início da corrida)."),
        ColumnMeta("tpep_dropoff_datetime",   "Data e hora em que o taxímetro foi desligado (fim da corrida)."),
        ColumnMeta("passenger_count",         "Número de passageiros no veículo, conforme informado pelo motorista."),
        ColumnMeta("trip_distance",           "Distância percorrida na corrida em milhas, conforme registrado pelo taxímetro."),
        ColumnMeta("RatecodeID",              "Código de tarifa vigente ao fim da corrida. 1=Padrão, 2=JFK, 3=Newark, 4=Nassau/Westchester, 5=Tarifa negociada, 6=Corrida em grupo, 99=Nulo/desconhecido."),
        ColumnMeta("store_and_fwd_flag",      "Indica se o registro foi armazenado no veículo antes de ser enviado ao servidor (sem conexão). Y=sim, N=não."),
        ColumnMeta("PULocationID",            "Identificador da zona TLC onde o taxímetro foi acionado (embarque)."),
        ColumnMeta("DOLocationID",            "Identificador da zona TLC onde o taxímetro foi desligado (desembarque)."),
        ColumnMeta("payment_type",            "Código do método de pagamento. 0=Flex Fare, 1=Cartão de crédito, 2=Dinheiro, 3=Sem cobrança, 4=Disputa, 5=Desconhecido, 6=Corrida anulada."),
        ColumnMeta("fare_amount",             "Valor da tarifa calculada pelo taxímetro com base em tempo e distância (em USD)."),
        ColumnMeta("extra",                   "Cobranças extras e sobretaxas diversas (em USD)."),
        ColumnMeta("mta_tax",                 "Imposto MTA acionado automaticamente com base na tarifa metered vigente (em USD)."),
        ColumnMeta("tip_amount",              "Valor da gorjeta em USD. Populado automaticamente para pagamentos com cartão de crédito; gorjetas em dinheiro não são incluídas."),
        ColumnMeta("tolls_amount",            "Valor total de pedágios pagos durante a corrida (em USD)."),
        ColumnMeta("improvement_surcharge",   "Sobretaxa de melhoria cobrada na largada do taxímetro, vigente desde 2015 (em USD)."),
        ColumnMeta("total_amount",            "Valor total cobrado ao passageiro em USD. Não inclui gorjetas em dinheiro."),
        ColumnMeta("congestion_surcharge",    "Valor total cobrado na corrida referente à sobretaxa de congestionamento do Estado de NY (em USD)."),
        ColumnMeta("airport_fee",             "Taxa de embarque cobrada exclusivamente nas origens LaGuardia (LGA) e John F. Kennedy (JFK) (em USD)."),
        ColumnMeta("cbd_congestion_fee",      "Cobrança por corrida na Zona de Alívio de Congestionamento da MTA, vigente a partir de 05/01/2025 (em USD)."),
        ColumnMeta("source_file_path",        "Caminho do arquivo Parquet de origem no volume S3, adicionado pelo pipeline ETL para rastreabilidade."),
        ColumnMeta("etl_ingestion_timestamp", "Timestamp UTC do momento em que o registro foi processado e gravado na camada Bronze pelo pipeline ETL."),
    ]
)
