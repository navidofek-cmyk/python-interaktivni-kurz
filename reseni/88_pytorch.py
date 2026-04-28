"""Řešení – Lekce 88: PyTorch – neuronové sítě"""

# vyžaduje: pip install torch

import time
import math
import random

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_OK = True
    print(f"PyTorch {torch.__version__}  |  CUDA: {torch.cuda.is_available()}")
except ImportError:
    print("PyTorch není nainstalováno: pip install torch")
    import sys; sys.exit(0)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}\n")


# 1. Batch normalization – porovnání konvergence se/bez BN
print("=== 1. Batch normalization – porovnání konvergence ===\n")

X = torch.tensor([[0.,0.], [0.,1.], [1.,0.], [1.,1.]])
y = torch.tensor([[0.], [1.], [1.], [0.]])

class SiteXOR_BezBN(nn.Module):
    """XOR síť bez Batch Normalization."""
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid(),
        )
    def forward(self, x):
        return self.net(x)

class SiteXOR_SBN(nn.Module):
    """XOR síť s Batch Normalization."""
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 8),
            nn.BatchNorm1d(8),   # <- BN po každé lineární vrstvě
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid(),
        )
    def forward(self, x):
        return self.net(x)

def trenuj(model: nn.Module, X: torch.Tensor, y: torch.Tensor,
           epochy: int = 500) -> tuple[list[float], int]:
    """Trénuje model, vrátí (ztráty, epochu kdy dosáhla 100% accuracy)."""
    kriterium = nn.BCELoss()
    optimizer  = optim.Adam(model.parameters(), lr=0.05)
    ztráty     = []
    converged  = -1

    for epoch in range(epochy):
        pred = model(X)
        loss = kriterium(pred, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        ztráty.append(loss.item())

        if converged == -1:
            acc = ((pred > 0.5).float() == y).float().mean().item()
            if acc == 1.0:
                converged = epoch

    return ztráty, converged

torch.manual_seed(42)
model_bez = SiteXOR_BezBN()
torch.manual_seed(42)
model_s   = SiteXOR_SBN()

ztráty_bez, conv_bez = trenuj(model_bez, X, y)
ztráty_s,   conv_s   = trenuj(model_s, X, y)

print(f"  Bez BatchNorm: finální loss={ztráty_bez[-1]:.4f}, "
      f"converged epoch={conv_bez if conv_bez>=0 else 'nedosáhla'}")
print(f"  S BatchNorm:   finální loss={ztráty_s[-1]:.4f}, "
      f"converged epoch={conv_s if conv_s>=0 else 'nedosáhla'}")

# Textová vizualizace ztráty (každých 50 epoch)
print("\n  Průběh ztráty (každých 50 epoch):")
print(f"  {'Epocha':>6} {'Bez BN':>10} {'S BN':>10} {'Rychlejší':>12}")
for i in range(0, 500, 50):
    bez = ztráty_bez[i]
    s   = ztráty_s[i]
    lp  = "BN  ✓" if s < bez * 0.95 else "bez BN ✓" if bez < s * 0.95 else "stejné"
    print(f"  {i:>6}  {bez:>10.4f}  {s:>10.4f}  {lp:>12}")


# 2. Jednoduché CNN pro MNIST (struktura bez stahování dat)
print("\n=== 2. CNN pro MNIST ===\n")

class MnistCNN(nn.Module):
    """
    Konvoluční neuronová síť pro klasifikaci MNIST číslic.
    Vstup: (N, 1, 28, 28) – šedotónové obrázky 28x28
    Výstup: (N, 10) – pravděpodobnosti pro 10 číslic
    """
    def __init__(self):
        super().__init__()

        # Konvoluční bloky
        self.features = nn.Sequential(
            # Blok 1: 1→32 kanálů, kernel 3x3
            nn.Conv2d(1, 32, kernel_size=3, padding=1),  # 28x28
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),                           # 14x14

            # Blok 2: 32→64 kanálů
            nn.Conv2d(32, 64, kernel_size=3, padding=1), # 14x14
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),                           # 7x7

            # Blok 3: 64→128 kanálů
            nn.Conv2d(64, 128, kernel_size=3, padding=1),# 7x7
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )

        # Klasifikační hlava
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 7 * 7, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 10),    # 10 číslic (0-9)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.features(x)
        return self.classifier(features)

# Vytvoř model a ověř rozměry
cnn = MnistCNN()
testovaci_vstup = torch.randn(8, 1, 28, 28)   # batch 8 obrázků
s_features      = testovaci_vstup
with torch.no_grad():
    vystup = cnn(testovaci_vstup)

print(f"  Vstup:  {testovaci_vstup.shape}")
print(f"  Výstup: {vystup.shape}  (8 obrázků × 10 tříd)")
print(f"  Parametrů: {sum(p.numel() for p in cnn.parameters()):,}")

# Demo trénování na syntetických datech (MNIST bez stahování)
print("\n  Demo trénování na syntetických datech (1 epocha):")
synth_X = torch.randn(32, 1, 28, 28)
synth_y = torch.randint(0, 10, (32,))

kriterium_cnn = nn.CrossEntropyLoss()
optimizer_cnn = optim.Adam(cnn.parameters(), lr=0.001)

cnn.train()
pred_cnn = cnn(synth_X)
loss_cnn = kriterium_cnn(pred_cnn, synth_y)
optimizer_cnn.zero_grad()
loss_cnn.backward()
optimizer_cnn.step()

acc = (pred_cnn.argmax(1) == synth_y).float().mean()
print(f"  Loss: {loss_cnn.item():.4f}  Acc: {acc.item():.2%} (náhodná data)")

print("""
  Pro trénování na reálném MNIST:
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_data = datasets.MNIST('.', train=True, download=True, transform=transform)
    loader = DataLoader(train_data, batch_size=64, shuffle=True)

    for epoch in range(10):
        for X_batch, y_batch in loader:
            pred = cnn(X_batch)
            loss = kriterium(pred, y_batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
""")


# 3. Vizualizace trénovací křivky (ASCII art místo matplotlib)
print("=== 3. Vizualizace trénovací křivky (ASCII) ===\n")

def vizualizuj_krivku(ztráty: list[float],
                       titulek: str = "Trénovací křivka",
                       sirka: int = 60,
                       vyska: int = 12):
    """ASCII vizualizace trénovací křivky (loss vs epocha)."""
    if not ztráty:
        return

    # Downsample na šířku
    krok = max(1, len(ztráty) // sirka)
    body = ztráty[::krok][:sirka]

    min_val = min(body)
    max_val = max(body)
    rozah   = max_val - min_val or 1

    print(f"  {titulek}")
    print(f"  Max loss: {max_val:.4f}")

    for radek in range(vyska, 0, -1):
        prah = min_val + (radek / vyska) * rozah
        line = ""
        for val in body:
            line += "█" if val >= prah else " "
        if radek == vyska:
            print(f"  {max_val:.3f} |{line}|")
        elif radek == 1:
            print(f"  {min_val:.3f} |{line}|")
        elif radek == vyska // 2:
            mid = min_val + rozah / 2
            print(f"  {mid:.3f} |{line}|")
        else:
            print(f"         |{line}|")

    print(f"         +" + "-" * len(body) + "+")
    print(f"         0{' '*(len(body)//2-1)}epochy{' '*(len(body)//2-5)}{len(ztráty)}")

# Vizualizuj ztráty z XOR experimentů
print("  Model bez BN:")
vizualizuj_krivku(ztráty_bez[::5], "XOR bez BatchNorm")
print("\n  Model s BN:")
vizualizuj_krivku(ztráty_s[::5], "XOR s BatchNorm")

print("\n=== Shrnutí ===")
print("  1. BatchNorm porovnání – ztráta po epochách, epocha konvergence")
print("  2. MnistCNN – 3 konvoluční bloky, BatchNorm, Dropout, 10 tříd")
print("  3. ASCII vizualizace – trénovací křivka bez matplotlib")
