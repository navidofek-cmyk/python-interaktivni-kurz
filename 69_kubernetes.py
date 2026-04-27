"""
LEKCE 69: Kubernetes – orchestrace kontejnerů
===============================================
kubectl, helm, kubernetes Python client

K8s = automatická správa Docker kontejnerů v clusteru.
Řeší: škálování, load balancing, self-healing, rolling updates.

Klíčové objekty:
  Pod         – nejmenší jednotka (1+ kontejnerů)
  Deployment  – deklarativní správa Podů (replikace, updates)
  Service     – stabilní síťový endpoint pro Pody
  ConfigMap   – konfigurace (ne citlivá)
  Secret      – citlivá data (hesla, tokeny)
  Ingress     – HTTP routing zvenku do clusterů
  HPA         – Horizontal Pod Autoscaler

Tato lekce generuje K8s manifesty a ukazuje kubectl příkazy.
"""

import json
import yaml    # pip install pyyaml
import textwrap
import subprocess
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Generátor K8s manifestů
# ══════════════════════════════════════════════════════════════

print("=== Kubernetes manifesty ===\n")

K8S_DIR = Path("k8s_demo")
K8S_DIR.mkdir(exist_ok=True)

def uloz_yaml(jmeno: str, manifest: dict):
    soubor = K8S_DIR / jmeno
    try:
        soubor.write_text(yaml.dump(manifest, default_flow_style=False, allow_unicode=True))
    except Exception:
        soubor.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"  ✓ {soubor}")

# ── Namespace ─────────────────────────────────────────────────
uloz_yaml("00-namespace.yaml", {
    "apiVersion": "v1",
    "kind": "Namespace",
    "metadata": {"name": "python-kurz", "labels": {"app": "kurz"}},
})

# ── ConfigMap ─────────────────────────────────────────────────
uloz_yaml("01-configmap.yaml", {
    "apiVersion": "v1",
    "kind": "ConfigMap",
    "metadata": {"name": "app-config", "namespace": "python-kurz"},
    "data": {
        "ENV":            "production",
        "LOG_LEVEL":      "INFO",
        "MAX_STUDENTI":   "1000",
        "DATABASE_HOST":  "postgres-service",
        "REDIS_HOST":     "redis-service",
    },
})

# ── Secret ────────────────────────────────────────────────────
import base64
def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()

uloz_yaml("02-secret.yaml", {
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {"name": "app-secrets", "namespace": "python-kurz"},
    "type": "Opaque",
    "data": {
        "DATABASE_PASSWORD": b64("super-tajne-heslo"),
        "SECRET_KEY":        b64("jwt-signing-key-256bit"),
        "REDIS_PASSWORD":    b64("redis-heslo"),
    },
})

# ── Deployment (hlavní aplikace) ──────────────────────────────
deployment = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "python-kurz-api",
        "namespace": "python-kurz",
        "labels": {"app": "python-kurz", "version": "v1"},
    },
    "spec": {
        "replicas": 3,
        "selector": {"matchLabels": {"app": "python-kurz"}},
        "strategy": {
            "type": "RollingUpdate",
            "rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0},
        },
        "template": {
            "metadata": {"labels": {"app": "python-kurz", "version": "v1"}},
            "spec": {
                "containers": [{
                    "name": "api",
                    "image": "uzivatel/python-kurz:latest",
                    "ports": [{"containerPort": 8000}],
                    "resources": {
                        "requests": {"memory": "128Mi", "cpu": "100m"},
                        "limits":   {"memory": "512Mi", "cpu": "500m"},
                    },
                    "env": [
                        {"name": "ENV",        "valueFrom": {"configMapKeyRef": {"name": "app-config", "key": "ENV"}}},
                        {"name": "LOG_LEVEL",  "valueFrom": {"configMapKeyRef": {"name": "app-config", "key": "LOG_LEVEL"}}},
                        {"name": "SECRET_KEY", "valueFrom": {"secretKeyRef":    {"name": "app-secrets", "key": "SECRET_KEY"}}},
                        {"name": "DB_PASS",    "valueFrom": {"secretKeyRef":    {"name": "app-secrets", "key": "DATABASE_PASSWORD"}}},
                    ],
                    "livenessProbe": {
                        "httpGet": {"path": "/health", "port": 8000},
                        "initialDelaySeconds": 10,
                        "periodSeconds": 30,
                    },
                    "readinessProbe": {
                        "httpGet": {"path": "/ready", "port": 8000},
                        "initialDelaySeconds": 5,
                        "periodSeconds": 10,
                    },
                }],
            },
        },
    },
}
uloz_yaml("03-deployment.yaml", deployment)

# ── Service ───────────────────────────────────────────────────
uloz_yaml("04-service.yaml", {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "python-kurz-service", "namespace": "python-kurz"},
    "spec": {
        "selector": {"app": "python-kurz"},
        "ports": [{"port": 80, "targetPort": 8000, "protocol": "TCP"}],
        "type": "ClusterIP",
    },
})

# ── Ingress ───────────────────────────────────────────────────
uloz_yaml("05-ingress.yaml", {
    "apiVersion": "networking.k8s.io/v1",
    "kind": "Ingress",
    "metadata": {
        "name": "python-kurz-ingress",
        "namespace": "python-kurz",
        "annotations": {
            "nginx.ingress.kubernetes.io/rewrite-target": "/",
            "cert-manager.io/cluster-issuer": "letsencrypt-prod",
        },
    },
    "spec": {
        "tls": [{"hosts": ["kurz.example.com"], "secretName": "kurz-tls"}],
        "rules": [{
            "host": "kurz.example.com",
            "http": {"paths": [{
                "path": "/",
                "pathType": "Prefix",
                "backend": {"service": {"name": "python-kurz-service",
                                        "port": {"number": 80}}},
            }]},
        }],
    },
})

# ── HPA (autoscaling) ─────────────────────────────────────────
uloz_yaml("06-hpa.yaml", {
    "apiVersion": "autoscaling/v2",
    "kind": "HorizontalPodAutoscaler",
    "metadata": {"name": "python-kurz-hpa", "namespace": "python-kurz"},
    "spec": {
        "scaleTargetRef": {"apiVersion": "apps/v1", "kind": "Deployment",
                           "name": "python-kurz-api"},
        "minReplicas": 2,
        "maxReplicas": 10,
        "metrics": [
            {"type": "Resource", "resource": {"name": "cpu",
             "target": {"type": "Utilization", "averageUtilization": 70}}},
            {"type": "Resource", "resource": {"name": "memory",
             "target": {"type": "AverageValue", "averageValue": "400Mi"}}},
        ],
    },
})


# ══════════════════════════════════════════════════════════════
# ČÁST 2: kubectl příkazy
# ══════════════════════════════════════════════════════════════

print("""
=== kubectl – základní příkazy ===

  # Aplikuj všechny manifesty
  kubectl apply -f k8s_demo/

  # Zobraz stav
  kubectl get pods -n python-kurz
  kubectl get deployments -n python-kurz
  kubectl get services -n python-kurz
  kubectl describe pod <pod-name> -n python-kurz

  # Logy
  kubectl logs -f <pod-name> -n python-kurz
  kubectl logs -f -l app=python-kurz -n python-kurz  # všechny

  # Shell v podu
  kubectl exec -it <pod-name> -n python-kurz -- /bin/bash

  # Škálování
  kubectl scale deployment python-kurz-api --replicas=5 -n python-kurz

  # Rolling update (nový image)
  kubectl set image deployment/python-kurz-api api=uzivatel/python-kurz:v2

  # Rollback
  kubectl rollout undo deployment/python-kurz-api -n python-kurz
  kubectl rollout history deployment/python-kurz-api -n python-kurz

  # Port forward (local debug)
  kubectl port-forward svc/python-kurz-service 8080:80 -n python-kurz

  # Delete
  kubectl delete -f k8s_demo/
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Python Kubernetes client
# ══════════════════════════════════════════════════════════════

print("=== Python Kubernetes client ===")
print("""
pip install kubernetes

from kubernetes import client, config

# Načti kubeconfig (~/.kube/config nebo in-cluster)
config.load_kube_config()          # lokální
# config.load_incluster_config()   # uvnitř K8s podu

v1     = client.CoreV1Api()
appsv1 = client.AppsV1Api()

# Vypiš pody
pody = v1.list_namespaced_pod("python-kurz")
for pod in pody.items:
    print(f"  {pod.metadata.name}: {pod.status.phase}")

# Vytvoř deployment programaticky
deployment = client.V1Deployment(
    metadata=client.V1ObjectMeta(name="test"),
    spec=client.V1DeploymentSpec(
        replicas=2,
        selector=client.V1LabelSelector(match_labels={"app": "test"}),
        template=client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "test"}),
            spec=client.V1PodSpec(containers=[
                client.V1Container(name="test", image="nginx:latest")
            ])
        )
    )
)
appsv1.create_namespaced_deployment("default", deployment)

# Watch – sleduj události v reálném čase
from kubernetes import watch
w = watch.Watch()
for event in w.stream(v1.list_namespaced_pod, "python-kurz"):
    print(f"{event['type']}: {event['object'].metadata.name}")
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Helm chart
# ══════════════════════════════════════════════════════════════

HELM_DIR = K8S_DIR / "helm-chart"
HELM_DIR.mkdir(exist_ok=True)

(HELM_DIR / "Chart.yaml").write_text(textwrap.dedent("""\
    apiVersion: v2
    name: python-kurz
    description: Interaktivní Python kurz
    version: 0.1.0
    appVersion: "1.0.0"
"""))

(HELM_DIR / "values.yaml").write_text(textwrap.dedent("""\
    replicaCount: 3
    image:
      repository: uzivatel/python-kurz
      tag: latest
      pullPolicy: IfNotPresent
    service:
      type: ClusterIP
      port: 80
    ingress:
      enabled: true
      host: kurz.example.com
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70
"""))

print(f"\n  ✓ Helm chart: {HELM_DIR}/")
print("""
  # Instalace přes Helm
  helm install python-kurz ./k8s_demo/helm-chart
  helm upgrade python-kurz ./k8s_demo/helm-chart --set replicaCount=5
  helm rollback python-kurz 1
  helm uninstall python-kurz
""")

import shutil
shutil.rmtree(K8S_DIR, ignore_errors=True)

# TVOJE ÚLOHA:
# 1. Přidej do Deployment initContainer který čeká na DB připravenost.
# 2. Napiš PodDisruptionBudget – zajistí min. 2 running pody při maintenance.
# 3. Pomocí kubernetes Python client sleduj logy podu v reálném čase.
