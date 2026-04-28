"""Řešení – Lekce 83: AWS a cloud SDK – boto3"""

# vyžaduje: pip install boto3 moto[all]

import json
import time
from datetime import datetime, timezone, timedelta

try:
    import boto3
    from moto import mock_aws
    BOTO_OK = True
except ImportError:
    BOTO_OK = False
    print("Instalace: pip install boto3 moto[all]")
    import sys; sys.exit(0)


# 1. S3 lifecycle policy – automatické mazání souborů po 30 dnech
print("=== 1. S3 Lifecycle Policy (auto-mazání po 30 dnech) ===\n")

@mock_aws
def demo_s3_lifecycle():
    s3 = boto3.client("s3", region_name="eu-central-1")

    # Vytvoř bucket
    s3.create_bucket(
        Bucket="python-kurz-lifecycle",
        CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
    )

    # Lifecycle policy: různá pravidla pro různé prefixy
    lifecycle_config = {
        "Rules": [
            {
                "ID":     "smaz-temp-po-7-dnech",
                "Status": "Enabled",
                "Filter": {"Prefix": "temp/"},
                "Expiration": {"Days": 7},
            },
            {
                "ID":     "smaz-logy-po-30-dnech",
                "Status": "Enabled",
                "Filter": {"Prefix": "logy/"},
                "Expiration": {"Days": 30},
            },
            {
                "ID":     "archivuj-stare-po-90-dnech",
                "Status": "Enabled",
                "Filter": {"Prefix": "data/"},
                "Expiration": {"Days": 365},
                "Transitions": [
                    {"Days": 90,  "StorageClass": "STANDARD_IA"},
                    {"Days": 365, "StorageClass": "GLACIER"},
                ],
            },
            {
                "ID":      "smaz-neukoncene-uploady",
                "Status":  "Enabled",
                "Filter":  {"Prefix": ""},
                "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
            },
        ]
    }

    s3.put_bucket_lifecycle_configuration(
        Bucket="python-kurz-lifecycle",
        LifecycleConfiguration=lifecycle_config,
    )
    print("  Lifecycle policy nastavena:")

    # Ověř
    resp = s3.get_bucket_lifecycle_configuration(Bucket="python-kurz-lifecycle")
    for rule in resp["Rules"]:
        print(f"\n  Rule: {rule['ID']}")
        print(f"    Status: {rule['Status']}")
        if "Expiration" in rule:
            print(f"    Smazat po: {rule['Expiration']['Days']} dnech")
        if "Transitions" in rule:
            for t in rule["Transitions"]:
                print(f"    Přesunout po {t['Days']} dnech → {t['StorageClass']}")
        if "AbortIncompleteMultipartUpload" in rule:
            d = rule["AbortIncompleteMultipartUpload"]["DaysAfterInitiation"]
            print(f"    Zruš neukončené uploady po {d} dnech")

    # Nahraj testovací soubory do různých složek
    for prefix in ["temp/", "logy/", "data/"]:
        s3.put_object(
            Bucket="python-kurz-lifecycle",
            Key=f"{prefix}test.txt",
            Body=b"testovaci obsah",
        )

    resp = s3.list_objects_v2(Bucket="python-kurz-lifecycle")
    print(f"\n  Soubory ({resp['KeyCount']}):")
    for obj in resp.get("Contents", []):
        print(f"    {obj['Key']}")

demo_s3_lifecycle()


# 2. Lambda handler + deploy přes boto3
print("\n=== 2. Lambda handler + deploy ===\n")

# Lambda handler funkce (kód který poběží v cloudu)
LAMBDA_KOD = '''
import json
import boto3
from datetime import datetime

def handler(event, context):
    """
    Lambda funkce která:
    - Zpracuje HTTP event z API Gateway
    - Vrátí JSON odpověď
    """
    metoda = event.get("httpMethod", "GET")
    cesta  = event.get("path", "/")
    body   = json.loads(event.get("body") or "{}")

    print(f"[{datetime.now()}] {metoda} {cesta}")

    if cesta == "/health":
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "ok", "timestamp": str(datetime.now())}),
        }

    if metoda == "POST" and cesta == "/studenti":
        jmeno = body.get("jmeno", "")
        body_score = body.get("body", 0)
        if not jmeno:
            return {"statusCode": 400, "body": json.dumps({"error": "jmeno je povinné"})}
        return {
            "statusCode": 201,
            "body": json.dumps({"id": 1, "jmeno": jmeno, "body": body_score}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"zprava": "Lambda funguje!", "metoda": metoda}),
    }
'''

# Lokální test handleru (bez AWS)
print("  Lokální test Lambda handleru:\n")

import types
lambda_modul = types.ModuleType("lambda_handler")
exec(LAMBDA_KOD, lambda_modul.__dict__)
handler_fn = lambda_modul.handler

class MockContext:
    function_name = "python-kurz-fn"
    memory_limit_in_mb = 128
    invoked_function_arn = "arn:aws:lambda:eu-central-1:123:function:python-kurz-fn"

ctx = MockContext()

testy = [
    ({"httpMethod": "GET", "path": "/health", "body": None},       "Health check"),
    ({"httpMethod": "POST", "path": "/studenti", "body": '{"jmeno":"Misa","body":87}'}, "Vytvoř studenta"),
    ({"httpMethod": "POST", "path": "/studenti", "body": '{}'},    "Chybějící jméno"),
]

for event, popis in testy:
    resp = handler_fn(event, ctx)
    body = json.loads(resp["body"])
    print(f"  [{resp['statusCode']}] {popis}: {body}")

# Deploy Lambda přes boto3 (mock)
@mock_aws
def demo_lambda_deploy():
    import zipfile
    import io

    # Zabal kód do ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("lambda_function.py", LAMBDA_KOD)
    zip_bytes = zip_buffer.getvalue()

    # IAM role (mock)
    iam    = boto3.client("iam", region_name="eu-central-1")
    assume_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }]
    })
    role = iam.create_role(
        RoleName="lambda-exec-role",
        AssumeRolePolicyDocument=assume_policy,
    )
    role_arn = role["Role"]["Arn"]

    # Deploy Lambda
    lam = boto3.client("lambda", region_name="eu-central-1")
    resp = lam.create_function(
        FunctionName="python-kurz-fn",
        Runtime="python3.12",
        Role=role_arn,
        Handler="lambda_function.handler",
        Code={"ZipFile": zip_bytes},
        Description="Python kurz Lambda demo",
        Timeout=30,
        MemorySize=128,
        Environment={
            "Variables": {
                "ENV":     "production",
                "VERSION": "1.0.0",
            }
        },
    )
    print(f"\n  Lambda deployována:")
    print(f"    FunctionName: {resp['FunctionName']}")
    print(f"    Runtime:      {resp['Runtime']}")
    print(f"    Handler:      {resp['Handler']}")
    print(f"    Memory:       {resp['MemorySize']} MB")
    print(f"    Timeout:      {resp['Timeout']}s")

    # Vyvolání Lambda
    invoke_resp = lam.invoke(
        FunctionName="python-kurz-fn",
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "httpMethod": "GET",
            "path":       "/health",
            "body":       None,
        }).encode(),
    )
    payload = json.loads(invoke_resp["Payload"].read())
    print(f"\n  Vyvolání Lambda: {payload}")

    # Update kódu
    lam.update_function_code(
        FunctionName="python-kurz-fn",
        ZipFile=zip_bytes,
    )
    print("  Kód aktualizován (update_function_code)")

demo_lambda_deploy()


# 3. DynamoDB TTL – záznamy automaticky expirují
print("\n=== 3. DynamoDB TTL (auto-expirace) ===\n")

@mock_aws
def demo_dynamodb_ttl():
    dynamo = boto3.resource("dynamodb", region_name="eu-central-1")

    # Vytvoř tabulku
    tabulka = dynamo.create_table(
        TableName="Sessions",
        KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "session_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    # Aktivuj TTL na atributu "expire_at"
    boto3.client("dynamodb", region_name="eu-central-1").update_time_to_live(
        TableName="Sessions",
        TimeToLiveSpecification={
            "Enabled":       True,
            "AttributeName": "expire_at",
        },
    )
    print("  TTL aktivován na atributu 'expire_at'")

    # Vložení sessions s různými TTL
    now = int(time.time())
    sessions = [
        {
            "session_id": "sess_abc123",
            "user_id":    "user_1",
            "data":       {"theme": "dark", "lang": "cs"},
            "expire_at":  now + 3600,        # vyprší za 1 hodinu
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "session_id": "sess_def456",
            "user_id":    "user_2",
            "data":       {"theme": "light"},
            "expire_at":  now + 86400,       # vyprší za 24 hodin
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "session_id": "sess_expired",
            "user_id":    "user_3",
            "data":       {},
            "expire_at":  now - 3600,        # již expirovala (1h zpátky)
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    with tabulka.batch_writer() as batch:
        for s in sessions:
            batch.put_item(Item=s)
    print(f"  Vloženo {len(sessions)} sessions")

    # Čtení – v produkci DynamoDB samo smaže expired záznamy
    for s in sessions:
        resp = tabulka.get_item(Key={"session_id": s["session_id"]})
        item = resp.get("Item")
        if item:
            ttl_val    = item.get("expire_at", 0)
            zbyvaji_s  = ttl_val - now
            if zbyvaji_s > 0:
                status = f"aktivní, zbývá {zbyvaji_s}s"
            else:
                status = f"EXPIROVALA před {abs(zbyvaji_s)}s"
            print(f"  {item['session_id']}: {status}")

    # Update TTL – prodloužení session
    tabulka.update_item(
        Key={"session_id": "sess_abc123"},
        UpdateExpression="SET expire_at = :t",
        ExpressionAttributeValues={":t": now + 7200},   # prodloužení na 2h
    )
    print("\n  sess_abc123 prodloužena na 2 hodiny")

    # TTL informace
    ttl_info = boto3.client("dynamodb", region_name="eu-central-1").describe_time_to_live(
        TableName="Sessions"
    )
    ttl_spec = ttl_info["TimeToLiveDescription"]
    print(f"\n  TTL konfigurace:")
    print(f"    Status:     {ttl_spec['TimeToLiveStatus']}")
    print(f"    Atribut:    {ttl_spec.get('AttributeName', 'N/A')}")

demo_dynamodb_ttl()

print("\n=== Shrnutí ===")
print("  1. S3 lifecycle – temp/7d, logy/30d, data→GLACIER/365d")
print("  2. Lambda deploy – ZIP upload, invoke, update_function_code")
print("  3. DynamoDB TTL  – expire_at timestamp, auto-expirace sessions")
