"""Reseni – Lekce 69: Kubernetes – orchestrace kontejneru"""

import json
import textwrap
import subprocess
import sys
from pathlib import Path

try:
    import yaml
    YAML_OK = True
except ImportError:
    import json as yaml
    YAML_OK = False

K8S_DIR = Path("k8s_reseni")
K8S_DIR.mkdir(exist_ok=True)


def uloz_yaml(cesta: Path, data: dict) -> None:
    cesta.parent.mkdir(parents=True, exist_ok=True)
    if YAML_OK:
        import yaml as yaml_mod
        cesta.write_text(yaml_mod.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        cesta.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Vytvoren: {cesta}")


# 1. Deployment s initContainer (ceka na DB)

print("=== Ukol 1: Deployment s initContainer ===\n")

deployment_init = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "python-kurz",
        "namespace": "default",
        "labels": {"app": "python-kurz", "verze": "v2"},
    },
    "spec": {
        "replicas": 3,
        "selector": {"matchLabels": {"app": "python-kurz"}},
        "template": {
            "metadata": {"labels": {"app": "python-kurz"}},
            "spec": {
                # Ukol 1: initContainer ceka na pripravnost DB
                "initContainers": [
                    {
                        "name":  "cekej-na-db",
                        "image": "busybox:1.35",
                        "command": [
                            "sh", "-c",
                            # Opakuje se dokud DB neprijima spojeni
                            "until nc -z postgres-service 5432; do "
                            "echo 'Cekam na PostgreSQL...'; sleep 2; "
                            "done; echo 'DB je ready!'",
                        ],
                    }
                ],
                "containers": [
                    {
                        "name":  "api",
                        "image": "python-kurz:latest",
                        "ports": [{"containerPort": 8000}],
                        "env": [
                            {"name": "DATABASE_URL",
                             "valueFrom": {
                                 "secretKeyRef": {"name": "db-secret", "key": "url"}
                             }},
                            {"name": "DEBUG", "value": "false"},
                        ],
                        "resources": {
                            "requests": {"memory": "128Mi", "cpu": "100m"},
                            "limits":   {"memory": "512Mi", "cpu": "500m"},
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/health", "port": 8000},
                            "initialDelaySeconds": 15,
                            "periodSeconds": 20,
                        },
                        "readinessProbe": {
                            "httpGet": {"path": "/ready", "port": 8000},
                            "initialDelaySeconds": 5,
                            "periodSeconds": 10,
                        },
                    }
                ],
            },
        },
    },
}

uloz_yaml(K8S_DIR / "deployment-s-init.yaml", deployment_init)

print("""
  initContainer se pouziva pro:
    - Cekani na DB/service (nc -z host port)
    - Kopirovaní konfiguracnich souboru
    - Inicializace databaze (migrace)
    - Overeni pritomnosti secrets
""")


# 2. PodDisruptionBudget

print("=== Ukol 2: PodDisruptionBudget ===\n")

pdb = {
    "apiVersion": "policy/v1",
    "kind": "PodDisruptionBudget",
    "metadata": {
        "name": "python-kurz-pdb",
        "namespace": "default",
    },
    "spec": {
        # minAvailable: Vzdy alespon 2 running pody
        "minAvailable": 2,
        "selector": {
            "matchLabels": {"app": "python-kurz"}
        },
    },
}

uloz_yaml(K8S_DIR / "pdb.yaml", pdb)

print("""
  PodDisruptionBudget zajistuje:
    - Behem uzlove udrzby (kubectl drain) zustane bezet alespon 2 pody
    - Kubernetes nemuze z duvodu voluntarniho naruceni smazat vice podu
      kdyz by zbyl mene nez minAvailable
    - Chrání pred vypadky bezi rolling updates

  Alternativa: maxUnavailable: 1
    → vzdy alespon (replicas-1) podu bezi
""")


# 3. Kubernetes Python client – sledovani logu podu

print("=== Ukol 3: Kubernetes Python client – logy podu ===\n")

# vyžaduje: pip install kubernetes

KUBERNETES_LOG_KOD = """\
# vyžaduje: pip install kubernetes

from kubernetes import client, config, watch

def sleduj_logy_podu(
    namespace: str = "default",
    selector: str  = "app=python-kurz",
    kontejner: str | None = None,
):
    \"\"\"Sleduje logy podu v realnem case (jako kubectl logs -f --selector=...).\"\"\"
    # Nacteni kubeconfig
    try:
        config.load_incluster_config()   # uvnitr K8s clusteru
    except Exception:
        config.load_kube_config()        # lokalni ~/.kube/config

    v1 = client.CoreV1Api()

    # Najdi pody dle selektoru
    pody = v1.list_namespaced_pod(namespace=namespace, label_selector=selector)
    if not pody.items:
        print(f"Zadne pody s selector='{selector}' nenalezeny")
        return

    pod_name = pody.items[0].metadata.name
    print(f"Sleduji logy podu: {pod_name}")

    # Stream logu (jako tail -f)
    w = watch.Watch()
    try:
        for event in w.stream(
            v1.read_namespaced_pod_log,
            name=pod_name,
            namespace=namespace,
            container=kontejner,
            follow=True,
            tail_lines=100,
        ):
            print(f"[{pod_name}] {event}")
    except KeyboardInterrupt:
        w.stop()
        print("Sledovani zastaveno")


# Pouziti:
# sleduj_logy_podu(namespace="default", selector="app=python-kurz")

# Alternativa: sledovani vsech podu
def sleduj_vsechny_pody(namespace: str = "default"):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    w  = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, namespace=namespace):
        typ  = event["type"]
        pod  = event["object"].metadata.name
        faze = event["object"].status.phase
        print(f"[{typ}] Pod: {pod} → {faze}")
"""

print(KUBERNETES_LOG_KOD)


# Bonus: Kompletni K8s manifesty pro produkci

print("=== Bonus: Kompletni K8s stack ===\n")

service = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "python-kurz-service"},
    "spec": {
        "selector": {"app": "python-kurz"},
        "ports": [{"protocol": "TCP", "port": 80, "targetPort": 8000}],
        "type": "ClusterIP",
    },
}

hpa = {
    "apiVersion": "autoscaling/v2",
    "kind": "HorizontalPodAutoscaler",
    "metadata": {"name": "python-kurz-hpa"},
    "spec": {
        "scaleTargetRef": {"apiVersion": "apps/v1", "kind": "Deployment", "name": "python-kurz"},
        "minReplicas": 2,
        "maxReplicas": 10,
        "metrics": [
            {"type": "Resource", "resource": {"name": "cpu",
             "target": {"type": "Utilization", "averageUtilization": 70}}}
        ],
    },
}

uloz_yaml(K8S_DIR / "service.yaml", service)
uloz_yaml(K8S_DIR / "hpa.yaml", hpa)

print(f"""
  Kubectl prikazy:
    kubectl apply -f {K8S_DIR}/
    kubectl get pods -l app=python-kurz
    kubectl logs -f -l app=python-kurz
    kubectl describe pdb python-kurz-pdb
    kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
""")

import shutil
shutil.rmtree(K8S_DIR, ignore_errors=True)
print("Demo slozka uklizena.")
