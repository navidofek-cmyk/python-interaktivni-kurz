"""
LEKCE 70: MLOps – strojové učení v produkci
=============================================
pip install scikit-learn numpy pandas joblib

MLOps = DevOps pro ML. Automatizace celého ML životního cyklu:
  Data → Training → Evaluation → Serving → Monitoring → zpět

Problémy bez MLOps:
  "U mě model funguje" (jako "U mě kód běží")
  Model degraduje v čase (data drift)
  Nelze reprodukovat experimenty
  Serving je pomalý / nespolehlivý

Nástroje:
  MLflow      – tracking experimentů, model registry
  DVC         – verzování dat (jako git pro data)
  Seldon/BentoML – model serving
  Evidently   – monitoring modelu
  Feast       – feature store
"""

try:
    import numpy as np
    from sklearn.datasets import make_classification, load_iris
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import (classification_report, confusion_matrix,
                                  roc_auc_score, accuracy_score)
    import joblib
    ML_OK = True
except ImportError:
    print("Chybí závislosti: pip install scikit-learn numpy pandas joblib")
    ML_OK = False

import json
import time
import random
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

if not ML_OK:
    exit()

np.random.seed(42)

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Experiment tracking (MLflow simulace)
# ══════════════════════════════════════════════════════════════

print("=== Experiment Tracking ===\n")

@dataclass
class Run:
    run_id:     str = field(default_factory=lambda: hashlib.md5(
        str(time.time()).encode()).hexdigest()[:8])
    experiment: str = "default"
    params:     dict = field(default_factory=dict)
    metriky:    dict = field(default_factory=dict)
    artefakty:  list = field(default_factory=list)
    zacatek:    str = field(default_factory=lambda: datetime.now().isoformat())
    konec:      str | None = None
    stav:       str = "RUNNING"

    def log_param(self, klic: str, hodnota: Any):
        self.params[klic] = hodnota

    def log_metric(self, klic: str, hodnota: float):
        self.metriky[klic] = round(hodnota, 4)

    def log_artifact(self, cesta: str):
        self.artefakty.append(cesta)

    def end(self):
        self.konec = datetime.now().isoformat()
        self.stav  = "FINISHED"

class ExperimentTracker:
    def __init__(self, nazev: str = "kurz-ml"):
        self.nazev = nazev
        self.runs:  list[Run] = []

    def start_run(self) -> Run:
        run = Run(experiment=self.nazev)
        self.runs.append(run)
        return run

    def nejlepsi(self, metrika: str) -> Run | None:
        dokoncene = [r for r in self.runs if r.stav == "FINISHED"]
        if not dokoncene:
            return None
        return max(dokoncene, key=lambda r: r.metriky.get(metrika, 0))

    def zobraz(self):
        print(f"\n{'Run ID':<10} {'Model':<25} {'Accuracy':>10} {'AUC':>8} {'Čas (s)':>8}")
        print("─" * 65)
        for r in self.runs:
            model = r.params.get("model", "?")
            acc   = r.metriky.get("accuracy", 0)
            auc   = r.metriky.get("auc", 0)
            cas   = r.metriky.get("training_time_s", 0)
            print(f"  {r.run_id:<10} {model:<25} {acc:>10.4f} {auc:>8.4f} {cas:>8.2f}")

tracker = ExperimentTracker("klasifikace-studentu")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Training pipeline
# ══════════════════════════════════════════════════════════════

print("=== Training Pipeline ===\n")

# Syntetická data: předpovídáme úspěch studenta
X, y = make_classification(
    n_samples=1000, n_features=10, n_informative=5,
    n_redundant=2, random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Feature names pro interpretabilitu
feature_names = [f"feature_{i}" for i in range(X.shape[1])]

# Vyzkoušej více modelů
modely = {
    "LogisticRegression": LogisticRegression(max_iter=1000, C=1.0),
    "RandomForest(100)":  RandomForestClassifier(n_estimators=100, random_state=42),
    "RandomForest(200)":  RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42),
    "GradientBoosting":   GradientBoostingClassifier(n_estimators=100, random_state=42),
}

nejlepsi_model = None
nejlepsi_auc   = 0

for nazev, model in modely.items():
    run = tracker.start_run()

    # Pipeline: preprocessing + model
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  model),
    ])

    # Trénování
    t0 = time.perf_counter()
    pipeline.fit(X_train, y_train)
    trenovaci_cas = time.perf_counter() - t0

    # Evaluace
    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    # Zaloguj vše
    run.log_param("model", nazev)
    run.log_param("scaler", "StandardScaler")
    for k, v in model.get_params().items():
        if k in ("n_estimators", "max_depth", "C", "max_iter"):
            run.log_param(k, v)
    run.log_metric("accuracy", acc)
    run.log_metric("auc", auc)
    run.log_metric("training_time_s", trenovaci_cas)
    run.end()

    if auc > nejlepsi_auc:
        nejlepsi_auc   = auc
        nejlepsi_model = (nazev, pipeline)

tracker.zobraz()
print(f"\nNejlepší model: {nejlepsi_model[0]} (AUC={nejlepsi_auc:.4f})")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Model registry a versioning
# ══════════════════════════════════════════════════════════════

print("\n=== Model Registry ===\n")

@dataclass
class ModelVersion:
    nazev:    str
    verze:    int
    auc:      float
    accuracy: float
    soubor:   str
    stage:    str = "Staging"   # Staging / Production / Archived
    vytvoreno: str = field(default_factory=lambda: datetime.now().isoformat())

class ModelRegistry:
    def __init__(self):
        self._modely: dict[str, list[ModelVersion]] = {}

    def registruj(self, nazev: str, model, metriky: dict) -> ModelVersion:
        verze = len(self._modely.get(nazev, [])) + 1
        soubor = f"models/{nazev}_v{verze}.pkl"
        Path("models").mkdir(exist_ok=True)
        joblib.dump(model, soubor)

        mv = ModelVersion(
            nazev=nazev, verze=verze,
            auc=metriky.get("auc", 0),
            accuracy=metriky.get("accuracy", 0),
            soubor=soubor,
        )
        self._modely.setdefault(nazev, []).append(mv)
        print(f"  Zaregistrován: {nazev} v{verze}  (AUC={mv.auc:.4f})")
        return mv

    def propaguj(self, nazev: str, verze: int, stage: str):
        for mv in self._modely.get(nazev, []):
            if mv.verze == verze:
                mv.stage = stage
                print(f"  {nazev} v{verze} → {stage}")
                return
        raise KeyError(f"Model {nazev} v{verze} nenalezen")

    def ziskej_produkci(self, nazev: str) -> ModelVersion | None:
        for mv in reversed(self._modely.get(nazev, [])):
            if mv.stage == "Production":
                return mv
        return None

    def nacti(self, mv: ModelVersion):
        return joblib.load(mv.soubor)

registry = ModelRegistry()
nejlepsi_run = tracker.nejlepsi("auc")

# Zaregistruj nejlepší model
mv = registry.registruj(
    "student-uspech",
    nejlepsi_model[1],
    nejlepsi_run.metriky if nejlepsi_run else {"auc": nejlepsi_auc},
)
registry.propaguj("student-uspech", 1, "Production")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Model serving (REST endpoint)
# ══════════════════════════════════════════════════════════════

print("\n=== Model Serving ===\n")

class ModelServer:
    def __init__(self, registry: ModelRegistry, nazev: str):
        self.registry = registry
        self.nazev    = nazev
        self._model   = None
        self._metriky = {"predikce": 0, "chyby": 0, "celkovy_cas": 0.0}

    def _nacti_model(self):
        mv = self.registry.ziskej_produkci(self.nazev)
        if mv:
            self._model = self.registry.nacti(mv)
            print(f"  Načten model: {mv.nazev} v{mv.verze} (AUC={mv.auc:.4f})")

    def predict(self, features: list[float]) -> dict:
        if not self._model:
            self._nacti_model()

        t0 = time.perf_counter()
        try:
            X = np.array(features).reshape(1, -1)
            trida     = int(self._model.predict(X)[0])
            pravdepodobnost = float(self._model.predict_proba(X)[0][trida])

            self._metriky["predikce"] += 1
            self._metriky["celkovy_cas"] += time.perf_counter() - t0

            return {
                "trida": trida,
                "pravdepodobnost": round(pravdepodobnost, 4),
                "latence_ms": round((time.perf_counter() - t0) * 1000, 2),
            }
        except Exception as e:
            self._metriky["chyby"] += 1
            raise

    def zdravi(self) -> dict:
        n = self._metriky["predikce"]
        prumer_latence = (self._metriky["celkovy_cas"] / n * 1000) if n > 0 else 0
        return {
            "status": "OK",
            "predikce": n,
            "chyby":    self._metriky["chyby"],
            "prumerna_latence_ms": round(prumer_latence, 2),
        }

server = ModelServer(registry, "student-uspech")

# Simuluj produkční provoz
print("Produkční predikce:")
for i in range(5):
    features = list(np.random.randn(10))
    vysledek = server.predict(features)
    print(f"  Požadavek {i+1}: třída={vysledek['trida']} "
          f"p={vysledek['pravdepodobnost']:.3f} "
          f"latence={vysledek['latence_ms']}ms")

print(f"\nZdraví serveru: {server.zdravi()}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Data drift monitoring
# ══════════════════════════════════════════════════════════════

print("\n=== Data Drift Monitoring ===\n")

from scipy import stats as scipy_stats

def detekuj_drift(trenovaci_data: np.ndarray, produkcni_data: np.ndarray,
                   alfa: float = 0.05) -> dict:
    """Kolmogorov-Smirnov test pro každý feature."""
    vysledky = {}
    for i in range(trenovaci_data.shape[1]):
        stat, p_hodnota = scipy_stats.ks_2samp(
            trenovaci_data[:, i], produkcni_data[:, i]
        )
        drift_detekovan = p_hodnota < alfa
        vysledky[f"feature_{i}"] = {
            "ks_stat": round(stat, 4),
            "p_value": round(p_hodnota, 4),
            "drift":   drift_detekovan,
        }
    return vysledky

try:
    from scipy import stats as scipy_stats
    # Simuluj drift v produkčních datech (posun distribuce)
    X_prod_bez_driftu = X_test + np.random.randn(*X_test.shape) * 0.1
    X_prod_s_driftem  = X_test.copy()
    X_prod_s_driftem[:, :3] += 2.0   # drift v prvních 3 features

    print("Monitoring bez driftu:")
    vysl = detekuj_drift(X_train, X_prod_bez_driftu)
    n_drift = sum(1 for v in vysl.values() if v["drift"])
    print(f"  Features s driftem: {n_drift}/{len(vysl)}")

    print("\nMonitoring s driftem (features 0,1,2 posunuty o +2):")
    vysl2 = detekuj_drift(X_train, X_prod_s_driftem)
    for feat, info in list(vysl2.items())[:5]:
        ikona = "⚠" if info["drift"] else "✓"
        print(f"  {ikona} {feat}: KS={info['ks_stat']:.3f} p={info['p_value']:.4f}")

    n_drift2 = sum(1 for v in vysl2.values() if v["drift"])
    print(f"\n  Celkem drift: {n_drift2}/{len(vysl2)} features → {'ALERT!' if n_drift2 > 2 else 'OK'}")
except ImportError:
    print("  scipy není nainstalováno – drift monitoring přeskočen")
    print("  pip install scipy")


# Úklid
import shutil
shutil.rmtree("models", ignore_errors=True)

print("""
=== MLOps stack ===

  Tracking:      MLflow, Weights & Biases, Neptune
  Data version.: DVC (Data Version Control)
  Feature store: Feast, Tecton
  Training:      Kubeflow Pipelines, Airflow, Prefect
  Serving:       BentoML, Seldon, TorchServe, TF Serving
  Monitoring:    Evidently, Arize, WhyLogs
  Orchestrace:   Kubernetes + Helm

  Minimální MLOps stack pro začátek:
    MLflow + scikit-learn + FastAPI + Docker + Grafana
""")

# TVOJE ÚLOHA:
# 1. Přidej do ExperimentTracker ukládání do JSON souboru (persistent tracking).
# 2. Napiš A/B testing – 50% provozu jde na model v1, 50% na v2.
# 3. Implementuj feature importance výpis pro RandomForest model.
