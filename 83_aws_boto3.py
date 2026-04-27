"""
LEKCE 83: AWS a cloud SDK – boto3
===================================
pip install boto3

boto3 = oficiální Python SDK pro Amazon Web Services.
Přes stejný interface ovládáš S3, Lambda, DynamoDB, SQS, EC2...

Alternativy:
  google-cloud-*   → Google Cloud Platform
  azure-*          → Microsoft Azure
  cloudflare       → Cloudflare Workers/R2/KV

Tato lekce:
  S3       – ukládání souborů (jako disk v cloudu)
  DynamoDB – NoSQL databáze (klíč-hodnota)
  SQS      – fronta zpráv (jako Kafka-lite)
  Lambda   – serverless funkce
  Secrets Manager – správa tajemství
"""

import os
import json
import time
import io
from pathlib import Path
from datetime import datetime, timedelta

# ── Lokální simulace (moto = mock AWS) ───────────────────────
try:
    import boto3
    import moto
    from moto import mock_aws
    BOTO_OK = True
except ImportError:
    BOTO_OK = False

if not BOTO_OK:
    print("Instalace: pip install boto3 moto[all]")
    print("(moto = lokální mock AWS – nepotřebuješ reálný účet)")
    print("\nUkazuji kód – po instalaci spusť znovu.\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: S3 – ukládání souborů
# ══════════════════════════════════════════════════════════════

print("=== S3 – Simple Storage Service ===\n")

if BOTO_OK:
    @mock_aws
    def demo_s3():
        s3 = boto3.client("s3", region_name="eu-central-1")

        # Vytvoř bucket
        s3.create_bucket(
            Bucket="python-kurz-demo",
            CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
        )
        print("  Bucket vytvořen: python-kurz-demo")

        # Upload souboru
        s3.put_object(
            Bucket="python-kurz-demo",
            Key="lekce/01_ahoj_svete.py",
            Body=b'print("Ahoj, světe!")\n',
            ContentType="text/x-python",
            Metadata={"autor": "Míša", "verze": "1.0"},
        )

        # Upload z lokálního souboru
        obsah = json.dumps({"studenti": 42, "lekce": 83}).encode()
        s3.put_object(
            Bucket="python-kurz-demo",
            Key="data/statistiky.json",
            Body=obsah,
        )

        # Upload velkého souboru po částech (multipart)
        velky_soubor = b"x" * (10 * 1024 * 1024)   # 10 MB simulace
        mp = s3.create_multipart_upload(Bucket="python-kurz-demo", Key="velky.bin")
        cast1 = s3.upload_part(Bucket="python-kurz-demo", Key="velky.bin",
                                UploadId=mp["UploadId"], PartNumber=1,
                                Body=velky_soubor[:5*1024*1024])
        cast2 = s3.upload_part(Bucket="python-kurz-demo", Key="velky.bin",
                                UploadId=mp["UploadId"], PartNumber=2,
                                Body=velky_soubor[5*1024*1024:])
        s3.complete_multipart_upload(
            Bucket="python-kurz-demo", Key="velky.bin",
            UploadId=mp["UploadId"],
            MultipartUpload={"Parts": [
                {"PartNumber": 1, "ETag": cast1["ETag"]},
                {"PartNumber": 2, "ETag": cast2["ETag"]},
            ]},
        )

        # List souborů
        resp = s3.list_objects_v2(Bucket="python-kurz-demo")
        print(f"\n  Soubory v bucketu ({resp['KeyCount']}):")
        for obj in resp.get("Contents", []):
            print(f"    {obj['Key']:<40} {obj['Size']:>10,} B")

        # Download
        obj = s3.get_object(Bucket="python-kurz-demo", Key="lekce/01_ahoj_svete.py")
        obsah_stazeny = obj["Body"].read()
        print(f"\n  Staženo: {obsah_stazeny!r}")
        print(f"  Metadata: {obj['Metadata']}")

        # Presigned URL (sdílení souboru bez přístupu k AWS)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "python-kurz-demo", "Key": "lekce/01_ahoj_svete.py"},
            ExpiresIn=3600,   # platný 1 hodinu
        )
        print(f"\n  Presigned URL (1h):\n  {url[:80]}...")

        # Kopírování a mazání
        s3.copy_object(
            Bucket="python-kurz-demo",
            CopySource={"Bucket": "python-kurz-demo", "Key": "data/statistiky.json"},
            Key="backup/statistiky_backup.json",
        )
        s3.delete_object(Bucket="python-kurz-demo", Key="velky.bin")
        print("\n  Copy + Delete hotovo")

    demo_s3()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: DynamoDB – NoSQL databáze
# ══════════════════════════════════════════════════════════════

print("\n=== DynamoDB – NoSQL databáze ===\n")

if BOTO_OK:
    @mock_aws
    def demo_dynamodb():
        dynamo = boto3.resource("dynamodb", region_name="eu-central-1")

        # Vytvoř tabulku
        tabulka = dynamo.create_table(
            TableName="Studenti",
            KeySchema=[
                {"AttributeName": "pk",  "KeyType": "HASH"},   # partition key
                {"AttributeName": "sk",  "KeyType": "RANGE"},  # sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk",  "AttributeType": "S"},
                {"AttributeName": "sk",  "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"  Tabulka: {tabulka.name}")

        # Vložení položek
        studenti = [
            {"pk": "student#1", "sk": "profil", "jmeno": "Míša",
             "vek": 15, "predmety": ["Python", "Math"], "body": 87.5},
            {"pk": "student#2", "sk": "profil", "jmeno": "Tomáš",
             "vek": 16, "predmety": ["Python", "Physics"], "body": 92.0},
            {"pk": "student#1", "sk": "zapis#2024-01",
             "predmet": "Python", "datum": "2024-01-15", "body": 87},
            {"pk": "student#1", "sk": "zapis#2024-02",
             "predmet": "Math",   "datum": "2024-02-20", "body": 91},
        ]

        with tabulka.batch_writer() as batch:
            for s in studenti:
                batch.put_item(Item=s)
        print(f"  Vloženo {len(studenti)} položek")

        # Čtení (GetItem)
        resp = tabulka.get_item(Key={"pk": "student#1", "sk": "profil"})
        student = resp["Item"]
        print(f"\n  Student 1: {student['jmeno']}, {student['body']} bodů")

        # Query – všechny záznamy pro studenta 1
        from boto3.dynamodb.conditions import Key as DKey, Attr
        resp = tabulka.query(
            KeyConditionExpression=DKey("pk").eq("student#1"),
        )
        print(f"\n  Záznamy pro student#1 ({resp['Count']}):")
        for item in resp["Items"]:
            print(f"    sk={item['sk']}", end="  ")
            if "predmet" in item:
                print(f"predmet={item['predmet']}, body={item['body']}")
            else:
                print(f"jmeno={item['jmeno']}")

        # Podmíněný update (atomický)
        tabulka.update_item(
            Key={"pk": "student#1", "sk": "profil"},
            UpdateExpression="SET body = :b, #v = #v + :inc",
            ExpressionAttributeValues={":b": 90.0, ":inc": 1},
            ExpressionAttributeNames={"#v": "verze"},
            ConditionExpression=Attr("body").lt(95),   # jen pokud body < 95
        )
        print("\n  Conditional update proběhl")

        # Scan (celá tabulka – pozor na výkon!)
        resp = tabulka.scan(FilterExpression=Attr("vek").gte(15))
        print(f"\n  Scan (vek>=15): {resp['Count']} položek")

    demo_dynamodb()


# ══════════════════════════════════════════════════════════════
# ČÁST 3: SQS – fronta zpráv
# ══════════════════════════════════════════════════════════════

print("\n=== SQS – Simple Queue Service ===\n")

if BOTO_OK:
    @mock_aws
    def demo_sqs():
        sqs = boto3.client("sqs", region_name="eu-central-1")

        # Vytvoř frontu (Standard i FIFO)
        fronta = sqs.create_queue(
            QueueName="python-kurz-fronta",
            Attributes={
                "VisibilityTimeout": "30",
                "MessageRetentionPeriod": "86400",   # 24h
            },
        )
        url = fronta["QueueUrl"]
        print(f"  Fronta: {url.split('/')[-1]}")

        # Odešli zprávy
        ukoly = [
            {"typ": "email",  "komu": "misa@k.cz",  "predmet": "Výsledky"},
            {"typ": "report", "format": "pdf",       "student_id": 1},
            {"typ": "backup", "tabulka": "studenti", "ts": time.time()},
        ]
        for ukol in ukoly:
            sqs.send_message(
                QueueUrl=url,
                MessageBody=json.dumps(ukol, ensure_ascii=False),
                MessageAttributes={
                    "typ": {"StringValue": ukol["typ"], "DataType": "String"},
                },
            )
        print(f"  Odesláno {len(ukoly)} zpráv")

        # Přijmi a zpracuj
        print("\n  Zpracování fronty:")
        while True:
            resp = sqs.receive_message(
                QueueUrl=url,
                MaxNumberOfMessages=2,
                WaitTimeSeconds=1,         # long polling
                MessageAttributeNames=["All"],
            )
            zpravy = resp.get("Messages", [])
            if not zpravy:
                break

            for zp in zpravy:
                data = json.loads(zp["Body"])
                typ  = zp.get("MessageAttributes", {}).get("typ", {}).get("StringValue", "?")
                print(f"    [{typ}] {json.dumps(data)[:60]}")

                # Potvrd zpracování (smaže zprávu)
                sqs.delete_message(
                    QueueUrl=url,
                    ReceiptHandle=zp["ReceiptHandle"],
                )

    demo_sqs()


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Secrets Manager
# ══════════════════════════════════════════════════════════════

print("\n=== Secrets Manager ===\n")

if BOTO_OK:
    @mock_aws
    def demo_secrets():
        sm = boto3.client("secretsmanager", region_name="eu-central-1")

        # Ulož tajemství
        sm.create_secret(
            Name="python-kurz/db-credentials",
            SecretString=json.dumps({
                "username": "admin",
                "password": "super-tajne-heslo",
                "host": "db.example.com",
                "port": 5432,
            }),
        )
        print("  Tajemství uloženo")

        # Načti
        resp = sm.get_secret_value(SecretName="python-kurz/db-credentials")
        creds = json.loads(resp["SecretString"])
        print(f"  DB host: {creds['host']}:{creds['port']}")
        print(f"  Uživatel: {creds['username']}")
        print(f"  Heslo: {'*' * len(creds['password'])}")

    demo_secrets()

print("""
=== Kdy co v AWS ===

  S3          → soubory, obrázky, zálohy, statický web
  DynamoDB    → NoSQL, serverless, automatické škálování
  RDS         → PostgreSQL/MySQL jako managed service
  SQS         → fronty mezi mikroslužbami
  SNS         → push notifikace (email, SMS, webhooks)
  Lambda      → serverless funkce (platíš jen za spuštění)
  EC2         → virtuální servery
  ECS/EKS     → Docker kontejnery / Kubernetes
  CloudFront  → CDN
  Route 53    → DNS

  Lokální vývoj:
    moto        → mock AWS (pip install moto[all])
    LocalStack  → plný AWS emulátor (docker run localstack/localstack)
""")

# TVOJE ÚLOHA:
# 1. Přidej S3 lifecycle policy – automatické mazání souborů po 30 dnech.
# 2. Napiš Lambda handler funkci a deploy ji přes boto3.
# 3. Přidej DynamoDB TTL – záznamy automaticky expirují po N sekundách.
