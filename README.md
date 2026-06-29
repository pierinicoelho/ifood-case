# ifood-case — Data Architecture

Pipeline de dados para o case técnico de Data Architect iFood, utilizando dados de corridas de táxi amarelo da cidade de Nova York (Jan–Mai 2023). Implementa uma arquitetura Lakehouse medallion em Databricks com Delta Lake.

---

## Pré-requisitos

- Databricks (Community Edition ou superior)
- AWS S3 com bucket e volume configurados → [docs/infrastructure_setup.md](docs/infrastructure_setup.md)
- Python 3.10+

---

## Estrutura do Repositório

```
ifood-case/
├─ src/
│   ├─ raw/          # Download dos Parquets TLC para o volume S3
│   ├─ bronze/       # Schema enforcement + ingestão Delta Table
│   ├─ silver/       # Limpeza estrutural (dedup, datas, anomalias)
│   ├─ gold/         # Projeção analítica + enriquecimento CASE WHEN
│   ├─ config/       # Settings globais, nomes de tabelas e metadados
│   ├─ core/         # Utilitários compartilhados (decorator de log)
│   └─ jobs/         # Entry points dos pipelines por camada
├─ analysis/         # Respostas às perguntas do case (P1 e P2)
├─ notebooks/        # EDAs de suporte às decisões de modelagem
├─ docs/             # Documentação técnica detalhada
└─ requirements.txt
```

---

## Como Importar o Repositório no Databricks

1. No workspace Databricks, acesse **Workspace → Repos → Add Repo**
2. Cole a URL do repositório: `https://github.com/pierinicoelho/ifood-case`
3. Após o clone, os arquivos de `src/` estarão disponíveis no caminho do Repo e podem ser referenciados normalmente nos jobs e notebooks

---

## Configuração

Antes de executar, ajuste [`src/config/settings.py`](src/config/settings.py) conforme seu ambiente:

```python
RAW_VOLUME_PATH = "/Volumes/<catalog>/<schema>/landingzone_raw_taxis"  # volume S3 no Databricks
Tables.SCHEMA   = "ifood_taxi_case"   # schema criado no Databricks
TARGET_YEARS    = ["2023"]
TARGET_MONTHS   = ["01", "02", "03", "04", "05"]
```

---

> **Pré-requisito de infraestrutura:** antes de executar os jobs, certifique-se de ter criado o bucket S3, o perfil IAM e o volume no Databricks conforme descrito em [docs/infrastructure_setup.md](docs/infrastructure_setup.md).

## Como Executar

Execute os jobs na sequência abaixo em um cluster Databricks (via notebook `%run` ou como script anexado ao job):

| Ordem | Job | Descrição |
|-------|-----|-----------|
| 1 | [`src/jobs/pipeline_ingest_raw.py`](src/jobs/pipeline_ingest_raw.py) | Download dos Parquets TLC para o volume S3 |
| 2 | [`src/jobs/pipeline_ingest_bronze.py`](src/jobs/pipeline_ingest_bronze.py) | Ingestão com schema enforcement → Delta Table Bronze |
| 3 | [`src/jobs/pipeline_transform_silver.py`](src/jobs/pipeline_transform_silver.py) | Limpeza estrutural → Delta Table Silver |
| 4 | [`src/jobs/pipeline_transform_gold.py`](src/jobs/pipeline_transform_gold.py) | Projeção analítica → Delta Table Gold |

> Para ajustar o período de ingestão (anos/meses) ou adicionar novos tipos de táxi, edite apenas `src/config/settings.py` — os pipelines escalam automaticamente.

---

## Decisões Técnicas

A solução segue o padrão **Lakehouse Medallion** (Raw → Bronze → Silver → Gold) sobre Delta Lake. As decisões de arquitetura estão documentadas em [docs/architecture_decisions.md](docs/architecture_decisions.md); os notebooks de EDA que as fundamentam estão em `notebooks/`.

| Camada | Decisão principal |
|--------|-------------------|
| **Bronze** | Upcasting seletivo por contrato de tipos ([`table_metadata.py`](table_metadata.py)) — compatibilidade entre meses com schemas divergentes |
| **Silver** | Single Source of Truth — 19 colunas preservadas; removidas apenas impossibilidades físicas (dedup, datas inválidas) |
| **Gold** | Projeção para 13 colunas analíticas + enriquecimento via `CASE WHEN` (sem star schema para o escopo do case) |
| **Geral** | Particionamento físico por `year/month`; metadados via Unity Catalog (`COMMENT ON TABLE`); escrita idempotente (`overwrite`) |

---

## Respostas às Perguntas do Case

### Pergunta 1 — Valor Total Recebido por Mês (Jan–Mai 2023)

> [`analysis/P1_total_amount_by_month.ipynb`](analysis/P1_total_amount_by_month.ipynb)

Perspectivas analisadas:
- ticket médio por corrida por mes, e media dos meses
- receita total por mês, e média dos totais mensais

Filtro aplicado: `total_amount > 0` — exclui chargebacks (`payment_type = 4`) e corridas sem cobrança.

### Pergunta 2 — Média de Passageiros por Hora em Maio de 2023

> [`analysis/P2_avg_passengers_by_hour.ipynb`](analysis/P2_avg_passengers_by_hour.ipynb)

`AVG(passenger_count)` agrupado por `pickup_hour`, restrito a Maio de 2023.

Filtro: `passenger_count > 0` — exclui batch sistêmico (~102k registros com campos secundários nulos) e corridas registradas sem passageiro (~60k).
Padrão identificado: madrugada concentra corridas compartilhadas (~1,45 pass./corrida); rush matinal tem menor média (~1,26).
