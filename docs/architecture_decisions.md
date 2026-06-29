# Decisões de Arquitetura — ifood-case

Registro das principais decisões técnicas tomadas ao longo do pipeline. Cada decisão documenta o problema enfrentado, a decisão adotada e a justificativa. Os notebooks de EDA que embasam cada decisão estão referenciados em `notebooks/`.

---

## 1. Schema Enforcement na Camada Bronze

**Problema:** Os Parquets da TLC possuem conflitos severos de tipo entre meses — `passenger_count` como `double` em Janeiro e `bigint` em Fevereiro; inconsistências de capitalização em nomes de colunas. `mergeSchema` falhou no Databricks Serverless por conflitos estruturais irrecuperáveis.

**Decisão:** Contrato de dados estrito via `StructType`. Colunas com conflito tipadas para o maior tamanho físico encontrado (`LongType`) — upcasting seletivo, não universal, para manter rastreabilidade de quais colunas tinham problema real. O contrato de upcasting vive em `_BRONZE_CASTS` no `src/config/table_metadata.py`, separado das descrições de negócio.

---

## 2. EDA 100% PySpark Nativo

**Problema:** Profiling de 16M de linhas sem estourar memória do driver. `dbutils.data.summarize()` não é suportado no Databricks Serverless.

**Decisão:** Toda análise exploratória via funções distribuídas do PySpark (`F.sum`, `F.when`, `.groupBy()`). Roda nos workers, é portável para qualquer cluster e escala para volumes maiores sem alteração de código.

---

## 3. Contrato de Metadados Centralizado

**Problema:** Descrições de tabelas e colunas precisam ser aplicadas via Unity Catalog em todas as camadas sem duplicação e sem acoplar configuração ao código de transformação.

**Decisão:** Dataclasses `ColumnMeta` / `TableMeta` (Python puro, sem dependência de PySpark) em [`src/config/table_metadata.py`](src/config/table_metadata.py) centralizam descrições e tipo de cast. Um único `TAXI_META` é compartilhado entre Bronze, Silver e Gold — apenas a descrição da tabela varia por camada (constantes `*_TABLE_COMMENT`). A função `_apply_table_metadata()` filtra silenciosamente colunas ausentes na tabela alvo, tornando o contrato reutilizável independente do schema de cada camada.

---

## 4. Silver como Single Source of Truth — Filtro Estrutural vs. Filtro de Negócio

**Problema:** O case permite cortar colunas e "limpar" os dados. Filtros agressivos baseados em valores atípicos causariam perda de contexto analítico.

**Decisão:**
- **Manter** todas as 19 colunas: sem `payment_type`, não é possível contextualizar `tip_amount = 0` (cash não registra gorjeta) nem `total_amount < 0` (chargeback de disputa).
- **Remover** apenas impossibilidades físicas: `dropoff < pickup`, datas fora do range Jan–Mai 2023, duplicatas por chave composta `(VendorID, pickup, dropoff, PULocationID, DOLocationID)`.
- **Manter** `total_amount < 0`: EDA confirmou que a maioria é `payment_type = 4` (Dispute) — chargeback é evento de negócio legítimo, não corrupção de dado.
- **Manter** NULLs sistêmicos (~428k linhas, 5 colunas simultâneas): falha de fornecedor em campos secundários; âncora temporal e valor financeiro permanecem válidos.
- **Manter** `passenger_count = 0` e `trip_distance = 0`: decisão de negócio para o consumidor, não da plataforma.

---

## 5. Scaffolding de Camadas Legível

**Decisão:** Estrutura da pasta `src/` para que reflita a progressão do pipeline diretamente: `raw/ → bronze/ → silver/ → gold/`. Nenhuma pasta `etl/` intermediária — `src/` já é o pacote ETL, adicionar um nível seria nesting sem ganho semântico.

---

## 6. Notebook Narrativo como Entrega de EDA

**Decisão:** Em vez de documentação separada, os notebooks seguem uma jornada de Data Storytelling: EDA prova a necessidade → decisão de limpeza é justificada com números → camada é construída → Gold responde as perguntas de negócio. O avaliador acompanha o raciocínio, não apenas vê o resultado.

| Notebook | Propósito |
|----------|-----------|
| [`notebooks/01_raw_to_bronze_eda.ipynb`](notebooks/01_raw_to_bronze_eda.ipynb) | Análise de conflitos de schema entre meses — fundamenta o upcasting da Bronze |
| [`notebooks/02_bronze_to_silver_eda.ipynb`](notebooks/02_bronze_to_silver_eda.ipynb) | Perfil de qualidade — fundamenta as regras de limpeza da Silver |
| [`notebooks/03_silver_to_gold_eda.ipynb`](notebooks/03_silver_to_gold_eda.ipynb) | Análise das colunas do case — fundamenta projeção, filtros e enriquecimento da Gold |

---

## 7. Modelagem da Camada Gold — CASE WHEN vs. Star Schema

**Problema:** Colunas de código numérico (`VendorID`, `RatecodeID`, `payment_type`) são opacas para consumidores analíticos. A alternativa canônica seria tabelas dimensão (Kimball/star schema).

**Decisão:** Para o escopo delimitado do case e o baixo volume de dados, enriquecimento via `CASE WHEN` diretamente na Gold — suficiente para tornar a camada de consumo auto-explicativa sem overhead arquitetural. Tabelas dimensão **não** foram implementadas: três dims com 4, 7 e 7 não se justificam dada a volumetria e padrão estático do case.

Em um cenário produtivo — múltiplos tipos de táxi, múltiplos anos, equipes de analytics distintas — a modelagem Kimball seria o caminho correto: dims de fornecedor, código de tarifa e método de pagamento em Silver, com fact table em Gold.

`PULocationID` / `DOLocationID` mantidos como IDs numéricos: o arquivo de lookup de zonas TLC não faz parte do dicionário recebido e não é exigido pelas perguntas do case.

---

## 8. Gold sem Filtros de Camada — Correlação Bidirecional entre Métricas

**Problema:** As duas perguntas do case consomem subconjuntos distintos da base Silver. A tendência natural seria aplicar filtros de "limpeza" na Gold (`total_amount > 0`, `passenger_count > 0`) para entregar uma tabela mais limpa ao analista.

**Decisão:** Nenhum filtro aplicado na escrita da Gold. A EDA ([`notebooks/03_silver_to_gold_eda.ipynb`](notebooks/03_silver_to_gold_eda.ipynb) , seção c) quantificou a correlação bidirecional entre as duas colunas:

- Registros com `passenger_count NULL/0` + `total_amount > 0`: receita válida necessária para P1 — filtrar `passenger_count` na camada removeria esses valores da soma mensal.
- Registros com `total_amount <= 0` + `passenger_count > 0`: corridas reais com chargeback posterior — filtrar `total_amount` na camada removeria passageiros válidos de P2.

Não existe filtro único correto para ambas as perguntas simultaneamente. Os filtros de negócio pertencem ao notebook de análise, aplicados por pergunta:

| Pergunta | Filtros aplicados na query |
|----------|---------------------------|
| P1 — valor por mês | `total_amount > 0` |
| P2 — passageiros por hora em Maio | `passenger_count > 0` e `month = 5` |
