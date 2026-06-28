"""
Contratos de metadados (descrições de tabelas e colunas) para aplicação via COMMENT ON no catálogo.
Separados por camada, descriçoes utilizadas globalmente e upcasting de tipos para compatibilidade entre meses na camada Bronze.
As descrições de colunas seguem o Data Dictionary oficial da TLC (NYC Taxi & Limousine Commission).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColumnMeta:
    """
    Classe base para descrição de tabelas e colunas.
    cast_to: tipo alvo para upcasting na camada Bronze (ex: "long", "double"). None = sem cast.
    """

    name: str
    comment: str
    cast_to: str | None = None


@dataclass(frozen=True)
class TableMeta:
    """
    Catalogo unificado de colunas compartilhado entre todas as camadas.
    Descrição de tabela varia por camada e é passada como parâmetro no adapter.
    """

    columns: list[ColumnMeta] = field(default_factory=list)


BRONZE_TABLE_COMMENT = (
    "Camada Bronze: dados brutos de viagens de táxi amarelo (Yellow Taxi) da NYC TLC, "
    "ingeridos as-is com upcasting de tipos para compatibilidade entre meses. "
    "Fonte: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf"
)
SILVER_TABLE_COMMENT = (
    "Camada Silver: dados de viagens de táxi amarelo limpos e validados estruturalmente. "
    "Single source of truth para consumo analítico e geração da camada Gold."
)
GOLD_TABLE_COMMENT = (
    "Camada Gold: colunas selecionadas de viagens de táxi amarelo para consumo analítico direto, "
    "conforme requisito do case iFood."
)

### Upcasting de tipos para compatibilidade entre meses na camada Bronze.
_BRONZE_CASTS: dict[str, str] = {
    "VendorID":        "long",
    "passenger_count": "long",
    "RatecodeID":      "long",
    "PULocationID":    "long",
    "DOLocationID":    "long",
}


def _col(name: str, comment: str) -> ColumnMeta:
    return ColumnMeta(name=name, comment=comment, cast_to=_BRONZE_CASTS.get(name))


TAXI_META = TableMeta(
    columns=[
        _col("VendorID",               "Código do provedor TPEP que gerou o registro. 1=Creative Mobile Technologies LLC, 2=Curb Mobility LLC, 6=Myle Technologies Inc, 7=Helix."),
        _col("tpep_pickup_datetime",    "Data e hora em que o taxímetro foi acionado (início da corrida)."),
        _col("tpep_dropoff_datetime",   "Data e hora em que o taxímetro foi desligado (fim da corrida)."),
        _col("passenger_count",         "Número de passageiros no veículo, conforme informado pelo motorista."),
        _col("trip_distance",           "Distância percorrida na corrida em milhas, conforme registrado pelo taxímetro."),
        _col("RatecodeID",              "Código de tarifa vigente ao fim da corrida. 1=Padrão, 2=JFK, 3=Newark, 4=Nassau/Westchester, 5=Tarifa negociada, 6=Corrida em grupo, 99=Nulo/desconhecido."),
        _col("store_and_fwd_flag",      "Indica se o registro foi armazenado no veículo antes de ser enviado ao servidor (sem conexão). Y=sim, N=não."),
        _col("PULocationID",            "Identificador da zona TLC onde o taxímetro foi acionado (embarque)."),
        _col("DOLocationID",            "Identificador da zona TLC onde o taxímetro foi desligado (desembarque)."),
        _col("payment_type",            "Código do método de pagamento. 0=Flex Fare, 1=Cartão de crédito, 2=Dinheiro, 3=Sem cobrança, 4=Disputa, 5=Desconhecido, 6=Corrida anulada."),
        _col("fare_amount",             "Valor da tarifa calculada pelo taxímetro com base em tempo e distância (em USD)."),
        _col("extra",                   "Cobranças extras e sobretaxas diversas (em USD)."),
        _col("mta_tax",                 "Imposto MTA acionado automaticamente com base na tarifa metered vigente (em USD)."),
        _col("tip_amount",              "Valor da gorjeta em USD. Populado automaticamente para pagamentos com cartão de crédito; gorjetas em dinheiro não são incluídas."),
        _col("tolls_amount",            "Valor total de pedágios pagos durante a corrida (em USD)."),
        _col("improvement_surcharge",   "Sobretaxa de melhoria cobrada na largada do taxímetro, vigente desde 2015 (em USD)."),
        _col("total_amount",            "Valor total cobrado ao passageiro em USD. Não inclui gorjetas em dinheiro."),
        _col("congestion_surcharge",    "Valor total cobrado na corrida referente à sobretaxa de congestionamento do Estado de NY (em USD)."),
        _col("airport_fee",             "Taxa de embarque cobrada exclusivamente nas origens LaGuardia (LGA) e John F. Kennedy (JFK) (em USD)."),
        _col("cbd_congestion_fee",      "Cobrança por corrida na Zona de Alívio de Congestionamento da MTA, vigente a partir de 05/01/2025 (em USD)."),
        _col("source_file_path",        "Caminho do arquivo Parquet de origem no volume S3, adicionado pelo pipeline ETL para rastreabilidade."),
        _col("etl_ingestion_timestamp", "Timestamp UTC do momento em que o registro foi processado e gravado na camada Bronze pelo pipeline ETL."),
    ]
)
