# Configuração de Infraestrutura — ifood-case

Guia de configuração do ambiente necessário para executar o pipeline. Cobre a criação do bucket S3, perfil IAM, integração com Databricks e configuração do schema.

---

## 1. Criação do Bucket S3

1) Caso ainda não possua uma conta na AWS, é necessário cria-la através do link: https://signin.aws.amazon.com/signup?request_type=register
2) Após cadastrar (ou caso ja tenha conta), realizar login na AWS e acessar a opçao [Buckets](https://us-east-1.console.aws.amazon.com/s3/)
3) Selecionar a opçao "Create Bucket"
4) Preencha o nome do bucket (ex: case-ifood), preenhcher demais opçoes e clicar em "Create Bucket"

---

## 2. Criação do Perfil IAM e Geração do ARN

1) Va até a opçao [IAM-Roles](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/roles) no console da AWS
2) Selecione a opçao "Create Role""
3) Selecione a opçao "AWS account" e clique em "Next"
4) Marque apenas a opçao "AmazonS3ExpressFullAccess" e clique "Next"
5) Preencha o nome e descriçao do Role e clique em "Create Role"
6) No dashboard de [IAM-Roles](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/roles), selecione o Role criado
7) Copie o ARN do Role, voce irá utiliza-lo na etapa 4

---

## 3. Criação do Schema no Databricks

Com o volume configurado, crie o schema que receberá as Delta Tables:

```sql
CREATE SCHEMA IF NOT EXISTS ifood_taxi_case;
```

O nome do schema deve coincidir com `Tables.SCHEMA` em `src/config/settings.py`.

---

## 4. Configuração do Volume no Databricks

Com o schema criado e o ARN em mãos:
1) Na UI do databricks, dentro da barra lateral selecione a opçao "Catalog"
2) Abra o workspace e selecione seu schmema (definido na etapa 3)
3) Clique na opçao "+" e selecione "create a volume"

   3.1) Peencha o nome do volume (ex: landing_zone_raw)

   3.2) Marque a opçao "External location" e clique em "Select external location" > "Create a new external location"

   3.3) Na nova janela que abrirá, marque a opçao "Create a new external location manually"

   3.4) Preencha com o nome do volume, "Storage Type" será S3, URL sera s3://{nome-do-bucket}

   3.5) Na opçao "Storage credential", selecione "Create new storage credential",  preencha com o ARN copiado na etapa 2 e clique em "Create"

4) Abrirá uma janela com um bloco dentro de "Trust policy", voce deve copia-lo. NAO FECHE ESTA CAIXA!
5) Abra uma nova aba para [IAM-Roles](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/roles) e selecione o role criado na etapa 2
6) Selecione a aba "Trusted entities", e clique em "Edit trust policy"
7) Apague todo o conteudo e cole o json copiado no passo [4], depois clique em "Update policy"
8) Volte a aba do passo [4] e clique em "IAM role configured"
9) Pronto, seu volume foi criado

---

## 5. Atualização do `settings.py`

Após configurar a infraestrutura, atualize os valores em `src/config/settings.py`:

```python
RAW_VOLUME_PATH = "/Volumes/<catalog>/<schema_volume>/landingzone_raw_taxis"

class Tables:
    SCHEMA = "ifood_taxi_case"   # schema criado no passo 4
```

---

## 6. Instalação de Dependências no Cluster

No cluster Databricks, instale o pacote adicional listado em `requirements.txt`:

```
matplotlib
```

> PySpark e Delta Lake são fornecidos pelo runtime do Databricks — não requerem instalação manual.
