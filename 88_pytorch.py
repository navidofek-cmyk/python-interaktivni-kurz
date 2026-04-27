"""
LEKCE 88: PyTorch – neuronové sítě
=====================================
pip install torch torchvision

PyTorch = framework pro deep learning od Meta.
Tensor = N-dimenzionální pole (jako NumPy, ale s GPU podporou a autograd).

Autograd = automatický výpočet gradientů → základ trénování sítí.

Použití:
  Klasifikace obrázků, textu, zvuku
  Generativní modely (GAN, Diffusion)
  Reinforcement learning
  Jazykové modely (transformers)
"""

import time
import math
import random

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_OK = True
    print(f"PyTorch {torch.__version__}  |  CUDA: {torch.cuda.is_available()}")
except ImportError:
    print("PyTorch není nainstalováno: pip install torch")
    TORCH_OK = False

if not TORCH_OK:
    exit()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Tensory – základ všeho
# ══════════════════════════════════════════════════════════════

print("=== Tensory ===\n")

# Vytvoření
a = torch.tensor([1.0, 2.0, 3.0, 4.0])
b = torch.zeros(3, 4)
c = torch.ones(2, 3)
d = torch.randn(3, 3)   # normální rozdělení

print(f"a = {a}")
print(f"b.shape = {b.shape}  dtype = {b.dtype}")
print(f"d:\n{d.round(decimals=3)}")

# Operace (broadcastují jako NumPy)
print(f"\na + 10 = {a + 10}")
print(f"a * a  = {a * a}")
print(f"a @ a  = {torch.dot(a, a):.1f}  (skalární součin)")

# Tvar
x = torch.randn(12)
print(f"\nreshape (12,) → (3,4):\n{x.reshape(3, 4).round(decimals=2)}")

# Převod NumPy ↔ Tensor
import numpy as np
np_arr = np.array([1.0, 2.0, 3.0])
tensor  = torch.from_numpy(np_arr)
zpet    = tensor.numpy()
print(f"\nNumPy → Tensor → NumPy: {zpet}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Autograd – automatické derivace
# ══════════════════════════════════════════════════════════════

print("\n=== Autograd ===\n")

# requires_grad=True = sleduj operace pro backprop
x = torch.tensor(2.0, requires_grad=True)
y = x ** 3 + 2 * x          # y = x³ + 2x

y.backward()                  # spočítej dy/dx
print(f"x = {x.item()}")
print(f"y = x³ + 2x = {y.item()}")
print(f"dy/dx = 3x² + 2 = {x.grad.item()}  (analyticky: {3*4+2})")

# Gradient descent krok za krokem
print("\n  Gradient descent: hledám minimum f(x) = x² - 4x + 5")
x = torch.tensor(0.0, requires_grad=True)
lr = 0.1

for krok in range(20):
    y = x**2 - 4*x + 5     # minimum je x=2, f(2)=1

    y.backward()
    with torch.no_grad():
        x -= lr * x.grad
    x.grad.zero_()

    if krok % 5 == 0:
        print(f"  krok {krok:2d}: x={x.item():.4f}  f(x)={y.item():.4f}")

print(f"  Nalezené minimum: x={x.item():.4f}  (analyticky: x=2.0)")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Neuronová síť – klasifikace
# ══════════════════════════════════════════════════════════════

print("\n=== Neuronová síť – XOR problém ===\n")

# XOR nelze řešit přímkou → potřebujeme alespoň 1 skrytou vrstvu
X = torch.tensor([[0.,0.], [0.,1.], [1.,0.], [1.,1.]])
y = torch.tensor([[0.], [1.], [1.], [0.]])   # XOR labely

class SiteXOR(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 4),       # vstup → skrytá vrstva
            nn.ReLU(),             # aktivační funkce
            nn.Linear(4, 1),       # skrytá vrstva → výstup
            nn.Sigmoid(),          # 0–1 pravděpodobnost
        )

    def forward(self, x):
        return self.net(x)

model = SiteXOR().to(device)
X, y  = X.to(device), y.to(device)

# Trénování
kriterium = nn.BCELoss()          # Binary Cross Entropy
optimizer  = optim.Adam(model.parameters(), lr=0.01)

print("Trénování (1000 epoch):")
for epoch in range(1001):
    pred = model(X)
    loss = kriterium(pred, y)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 200 == 0:
        acc = ((pred > 0.5).float() == y).float().mean().item()
        print(f"  Epoch {epoch:4d}: loss={loss.item():.4f}  accuracy={acc:.0%}")

# Výsledky
print("\nPředpovědi po trénování:")
with torch.no_grad():
    for vstup, ocekavany in zip(X, y):
        p = model(vstup.unsqueeze(0)).item()
        pred_label = 1 if p > 0.5 else 0
        ok = "✓" if pred_label == int(ocekavany.item()) else "✗"
        print(f"  {ok} [{vstup[0].int().item()}, {vstup[1].int().item()}]"
              f" → p={p:.3f} (predikce={pred_label})")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Regrese – předpověď bodu na křivce
# ══════════════════════════════════════════════════════════════

print("\n=== Regrese – fit sinusoidy ===\n")

# Generuj data: y = sin(x) + šum
torch.manual_seed(42)
X_reg = torch.linspace(0, 2*math.pi, 100).unsqueeze(1)
y_reg = torch.sin(X_reg) + 0.1 * torch.randn_like(X_reg)

class Regresni(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.net(x)

reg_model = Regresni()
reg_opt   = optim.Adam(reg_model.parameters(), lr=0.01)
mse       = nn.MSELoss()

for epoch in range(2001):
    pred = reg_model(X_reg)
    loss = mse(pred, y_reg)
    reg_opt.zero_grad()
    loss.backward()
    reg_opt.step()

with torch.no_grad():
    pred_test = reg_model(X_reg)
    final_mse = mse(pred_test, y_reg).item()
    print(f"  Finální MSE: {final_mse:.6f}  (čím blíže 0, tím lepší fit)")

    # Textová vizualizace fitu
    x_pts = [0, math.pi/2, math.pi, 3*math.pi/2, 2*math.pi]
    print("\n  Porovnání sin(x) vs síť:")
    for x_val in x_pts:
        x_t      = torch.tensor([[x_val]])
        pred_val = reg_model(x_t).item()
        skutecny = math.sin(x_val)
        print(f"  x={x_val:.2f}  sin(x)={skutecny:+.3f}  síť={pred_val:+.3f}  "
              f"Δ={abs(pred_val-skutecny):.4f}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Uložení a načtení modelu
# ══════════════════════════════════════════════════════════════

print("\n=== Uložení modelu ===\n")

import tempfile, os
with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
    cesta = f.name

torch.save(model.state_dict(), cesta)
print(f"  Uloženo: {cesta}  ({os.path.getsize(cesta):,} B)")

# Načtení
model2 = SiteXOR()
model2.load_state_dict(torch.load(cesta, weights_only=True))
model2.eval()
print(f"  Načteno. Testovací predikce: "
      f"{model2(torch.tensor([[1.,1.]])).item():.4f}  (XOR(1,1)=0)")
os.unlink(cesta)

print("""
=== PyTorch vs TensorFlow ===

  PyTorch     → dynamický graf, intuitivnější debugging,
                výzkum a produkce, LLM komunita (HuggingFace)
  TensorFlow  → statický graf, dobré pro deployment (TFLite, TF Serving)
  JAX         → funkcionální, XLA JIT, Google DeepMind
  scikit-learn→ klasické ML (ne deep learning)

  Doporučení: začni s PyTorch pro deep learning,
              scikit-learn pro klasické ML (lekce 70).
""")

# TVOJE ÚLOHA:
# 1. Přidej batch normalization (nn.BatchNorm1d) do SiteXOR a porovnej konvergenci.
# 2. Napiš jednoduché CNN pro MNIST (torchvision.datasets.MNIST).
# 3. Vizualizuj trénovací křivku (loss vs epoch) pomocí matplotlib (lekce 55).
