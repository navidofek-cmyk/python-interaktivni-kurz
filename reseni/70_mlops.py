"""Reseni – Lekce 70: MLOps – strojove uceni v produkci"""

# vyžaduje: pip install scikit-learn numpy pandas joblib scipy

try:
    import numpy as np
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import accuracy_score
    import joblib
    ML_OK = True
except ImportError:
    print("Scikit-learn neni nainstalovano: pip install scikit-learn numpy pandas joblib")
    ML_OK = False

import json
import time
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

if not ML_OK:
    exit()

np.random.seed(42)
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

# Generuj data
X, y = make_classification(n_samples=1000, n_features=10, n_informative=5, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# ExperimentTracker ze zdrojove lekce
@dataclass
class Experiment:
    jmeno:    str
    model:    str
    params:   dict
    metriky:  dict = field(default_factory=dict)
    cas:      str  = field(default_factory=lambda: datetime.now().isoformat())
    _id:      int  = field(default=0, init=False)


class ExperimentTracker:
    def __init__(self, soubor: str | None = None):
        self._experimenty: list[Experiment] = []
        self._soubor = soubor   # Ukol 1: persistovani

        # Nacti existujici experimenty pokud soubor existuje
        if soubor and Path(soubor).exists():
            self._nacti()

    def zaznamenej(self, exp: Experiment) -> None:
        exp._id = len(self._experimenty) + 1
        self._experimenty.append(exp)
        # Ukol 1: Uloz do JSON souboru
        if self._soubor:
            self._uloz()
        print(f"  [Tracker] #{exp._id} {exp.jmeno}: {exp.metriky}")

    def nejlepsi(self, metrika: str = "accuracy") -> Experiment | None:
        if not self._experimenty:
            return None
        return max(self._experimenty, key=lambda e: e.metriky.get(metrika, 0))

    def _uloz(self) -> None:
        """Ukol 1: Ulozi experimenty do JSON souboru."""
        data = [
            {
                "id":     e._id,
                "jmeno":  e.jmeno,
                "model":  e.model,
                "params": e.params,
                "metriky": e.metriky,
                "cas":    e.cas,
            }
            for e in self._experimenty
        ]
        Path(self._soubor).write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _nacti(self) -> None:
        """Nacte experimenty z JSON souboru."""
        data = json.loads(Path(self._soubor).read_text(encoding="utf-8"))
        for d in data:
            exp = Experiment(
                jmeno=d["jmeno"], model=d["model"],
                params=d["params"], metriky=d["metriky"],
            )
            exp._id = d["id"]
            exp.cas = d["cas"]
            self._experimenty.append(exp)
        print(f"  [Tracker] Nacteno {len(self._experimenty)} drivejsich experimentu")


# Ukol 1: Persistovani do JSON

print("=== Ukol 1: ExperimentTracker s JSON persistenci ===\n")

tracker = ExperimentTracker(soubor="models/experimenty.json")

modely_konfig = [
    ("LogisticRegression", LogisticRegression(max_iter=500), {"solver": "lbfgs"}),
    ("RandomForest-100",   RandomForestClassifier(n_estimators=100, random_state=42), {"n_estimators": 100}),
    ("RandomForest-50",    RandomForestClassifier(n_estimators=50, random_state=42), {"n_estimators": 50}),
    ("GradientBoosting",   GradientBoostingClassifier(n_estimators=50, random_state=42), {"n_estimators": 50}),
]

nejlepsi_model = None
nejlepsi_acc   = 0.0

for nazev, clf, params in modely_konfig:
    pipe = Pipeline([("scaler", StandardScaler()), ("clf", clf)])
    pipe.fit(X_train, y_train)
    acc = accuracy_score(y_test, pipe.predict(X_test))

    exp = Experiment(
        jmeno=f"Experiment-{nazev}",
        model=nazev,
        params=params,
        metriky={"accuracy": round(acc, 4)},
    )
    tracker.zaznamenej(exp)

    if acc > nejlepsi_acc:
        nejlepsi_acc   = acc
        nejlepsi_model = (nazev, pipe)

if Path("models/experimenty.json").exists():
    print(f"\n  Experimenty ulozeny do models/experimenty.json")
    with open("models/experimenty.json", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Obsah: {len(data)} experimentu")

nejlepsi_exp = tracker.nejlepsi("accuracy")
print(f"\n  Nejlepsi model: {nejlepsi_exp.model} – accuracy={nejlepsi_exp.metriky['accuracy']}")


# Ukol 2: A/B testing – 50% provozu na model v1, 50% na v2

print("\n=== Ukol 2: A/B testing (50/50) ===\n")


class ABTestingServer:
    """Distribuuje provoz mezi dvema modely."""

    def __init__(self, model_v1, model_v2, split: float = 0.5):
        self.model_v1  = model_v1
        self.model_v2  = model_v2
        self.split     = split
        self._statistiky = {"v1": {"volani": 0, "pozitivni": 0},
                             "v2": {"volani": 0, "pozitivni": 0}}

    def predict(self, features: list[float]) -> dict:
        """50% provozu na v1, 50% na v2."""
        verze = "v1" if random.random() < self.split else "v2"
        model = self.model_v1 if verze == "v1" else self.model_v2

        X = np.array(features).reshape(1, -1)
        pred  = int(model.predict(X)[0])
        proba = float(model.predict_proba(X)[0][pred])

        self._statistiky[verze]["volani"] += 1
        if pred == 1:
            self._statistiky[verze]["pozitivni"] += 1

        return {"verze": verze, "trida": pred, "pravdepodobnost": round(proba, 4)}

    def statistiky(self) -> dict:
        vysl = {}
        for verze, s in self._statistiky.items():
            pozitivni_pct = (s["pozitivni"] / s["volani"] * 100) if s["volani"] > 0 else 0
            vysl[verze] = {**s, "pozitivni_pct": round(pozitivni_pct, 1)}
        return vysl


# Pouziti dvou modelu
lr_pipe = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=500))])
lr_pipe.fit(X_train, y_train)

rf_pipe = Pipeline([("scaler", StandardScaler()), ("clf", RandomForestClassifier(n_estimators=50, random_state=42))])
rf_pipe.fit(X_train, y_train)

ab_server = ABTestingServer(lr_pipe, rf_pipe, split=0.5)

print(f"  Simuluji 100 pozadavku (50/50 A/B split):")
for i in range(100):
    features = list(X_test[i % len(X_test)])
    ab_server.predict(features)

stats = ab_server.statistiky()
for verze, s in stats.items():
    print(f"  Model {verze}: {s['volani']} volani, {s['pozitivni_pct']}% pozitivnich")


# Ukol 3: Feature importance pro RandomForest

print("\n=== Ukol 3: Feature Importance (RandomForest) ===\n")


def vytiskni_feature_importance(
    model_pipeline: Pipeline,
    feature_names: list[str] | None = None,
    top_n: int = 10,
) -> list[tuple[str, float]]:
    """Vypise feature importance z RandomForest/GradientBoosting modelu."""
    clf = model_pipeline.named_steps.get("clf")
    if clf is None or not hasattr(clf, "feature_importances_"):
        print("  Model nema feature_importances_ (pouzij RF nebo GB)")
        return []

    importances = clf.feature_importances_
    n_features   = len(importances)

    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]

    # Seradit dle dulezitosti
    serazene = sorted(
        zip(feature_names, importances),
        key=lambda x: x[1],
        reverse=True,
    )[:top_n]

    max_imp = serazene[0][1] if serazene else 1.0
    for i, (nazev, imp) in enumerate(serazene, 1):
        bar = "#" * int(imp / max_imp * 20)
        print(f"  {i:2d}. {nazev:<15} {imp:.4f}  {bar}")

    return serazene


rf_final = Pipeline([
    ("scaler", StandardScaler()),
    ("clf",    RandomForestClassifier(n_estimators=100, random_state=42)),
])
rf_final.fit(X_train, y_train)

feature_nazvy = [f"prıznak_{i}" for i in range(X_train.shape[1])]
print(f"  Feature importance (top 10 z {X_train.shape[1]} priznaku):")
top_features = vytiskni_feature_importance(rf_final, feature_nazvy, top_n=10)

print(f"\n  Nejdulezitejsi priznak: {top_features[0][0]} ({top_features[0][1]:.4f})")
print(f"  Nejmenej dulezity: {top_features[-1][0]} ({top_features[-1][1]:.4f})")


# Uklid
import shutil
shutil.rmtree("models", ignore_errors=True)
print("\nModels slozka uklizena.")
