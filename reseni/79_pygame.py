"""Řešení – Lekce 79: Pygame – 2D hry v Pythonu"""

# vyžaduje: pip install pygame

import sys
import random
import math

# Logika hry – bez spouštění okna (GUI část je v originální lekci)
print("=== Pygame – logická část (bez GUI) ===\n")
print("Pro spuštění okna: python3 79_pygame.py --play\n")

try:
    import pygame
    PYGAME_OK = True
except ImportError:
    PYGAME_OK = False
    print("Pygame není nainstalováno: pip install pygame\n")

# ── Sdílené konstanty ─────────────────────────────────────────
SIRKA, VYSKA = 600, 700
FPS          = 60

# 1. Laser beam – nepřetržitá čára místo kuliček
print("=== 1. Laser beam sprite ===\n")

if PYGAME_OK:
    class LaserBeam(pygame.sprite.Sprite):
        """
        Nepřetržitý laser – kreslí čáru od hráče k hornímu okraji.
        Aktivní dokud je stisknuta klávesa.
        """
        def __init__(self, x: int):
            super().__init__()
            self.x      = x
            self.aktivni = True
            self.sirka_beamu = 4
            self._obnov_image()

        def _obnov_image(self):
            self.image = pygame.Surface((self.sirka_beamu, VYSKA), pygame.SRCALPHA)
            barva = (255, 50, 50, 200)   # červená, poloprůhledná
            pygame.draw.rect(self.image, barva,
                              (0, 0, self.sirka_beamu, VYSKA))
            # Záblesk na konci
            pygame.draw.circle(self.image, (255, 200, 200, 255),
                                (self.sirka_beamu // 2, 0), self.sirka_beamu * 2)
            self.rect = self.image.get_rect(midtop=(self.x, 0))

        def update(self):
            klavesy = pygame.key.get_pressed()
            if not klavesy[pygame.K_SPACE]:
                self.kill()

        def zkontroluj_zasahy(self, nepratelé: pygame.sprite.Group) -> int:
            """Zkontroluje kolizi laseru s nepřáteli. Vrátí počet zasažených."""
            zasazeni = 0
            for nep in list(nepratelé):
                if self.rect.colliderect(nep.rect):
                    nep.hp -= 0.1   # laser způsobuje kontinuální poškození
                    if nep.hp <= 0:
                        nep.kill()
                        zasazeni += 1
            return zasazeni

    # Demo – ověření logiky
    pygame.init()
    laser = LaserBeam(x=300)
    print(f"  LaserBeam: x={laser.x}, image={laser.image.get_size()}")
    print(f"  Laser je aktivní dokud je držena mezerník")
    print(f"  Poškozuje all nepřátele v pruhu šířky {laser.sirka_beamu}px")


# 2. Power-up: zelená hvězdička = dočasně 2 střely najednou
print("\n=== 2. Power-up – dvojitý výstřel ===\n")

if PYGAME_OK:
    ZELENA = (50, 200, 80)
    ZLATA  = (255, 215, 0)
    BILA   = (255, 255, 255)

    class DoubleShootPowerup(pygame.sprite.Sprite):
        """Power-up který dává hráči 2 střely najednou po dobu 10 sekund."""
        TRVANI_MS = 10_000

        def __init__(self, x: int, y: int):
            super().__init__()
            self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
            # Nakresli hvězdičku (8 bodů)
            cx, cy = 12, 12
            for uhel in range(0, 360, 45):
                r_vonkajsi = 10
                r_vnitrni  = 4
                for r, odchylka in [(r_vonkajsi, 0), (r_vnitrni, 22)]:
                    rad = math.radians(uhel + odchylka)
                    px  = cx + r * math.cos(rad)
                    py  = cy + r * math.sin(rad)
                pygame.draw.circle(self.image, ZELENA, (cx, cy), 10)
                pygame.draw.circle(self.image, BILA,   (cx, cy), 10, 2)
            # Hvězdička jako text
            font = pygame.font.SysFont("monospace", 16, bold=True)
            txt  = font.render("★", True, ZLATA)
            self.image.blit(txt, (4, 3))

            self.rect = self.image.get_rect(center=(x, y))
            self.rychlost = 2.5

        def update(self):
            self.rect.y += self.rychlost
            if self.rect.top > VYSKA:
                self.kill()

    class Hrac(pygame.sprite.Sprite):
        """Hráč s podporou power-upů."""
        def __init__(self):
            super().__init__()
            self.image = pygame.Surface((40, 50), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, ZELENA, [(20, 0), (0, 50), (40, 50)])
            self.rect = self.image.get_rect(center=(SIRKA//2, VYSKA - 80))
            self.double_shoot_do   = 0   # timestamp vypršení efektu
            self.posledni_vystrel  = 0
            self.cooldown          = 250
            self.hp                = 3

        @property
        def ma_double_shoot(self) -> bool:
            return pygame.time.get_ticks() < self.double_shoot_do

        def aktivuj_double_shoot(self):
            """Aktivuje double shoot na TRVANI_MS ms."""
            self.double_shoot_do = pygame.time.get_ticks() + DoubleShootPowerup.TRVANI_MS
            print(f"  [Power-up] Double shoot aktivován na 10s!")

        def muze_strilet(self) -> bool:
            return pygame.time.get_ticks() - self.posledni_vystrel > self.cooldown

        def vystrelte(self) -> list:
            """Vrátí 1 nebo 2 střely podle aktivního power-upu."""
            self.posledni_vystrel = pygame.time.get_ticks()
            strely = []

            cx = self.rect.centerx
            cy = self.rect.top

            class Strela(pygame.sprite.Sprite):
                def __init__(self_, x, y):
                    super().__init__()
                    self_.image = pygame.Surface((4, 14), pygame.SRCALPHA)
                    pygame.draw.rect(self_.image, ZLATA, (0, 0, 4, 14), border_radius=2)
                    self_.rect = self_.image.get_rect(center=(x, y))
                    self_.vy   = -10

                def update(self_):
                    self_.rect.y += self_.vy
                    if self_.rect.bottom < 0:
                        self_.kill()

            strely.append(Strela(cx, cy))

            if self.ma_double_shoot:
                strely.append(Strela(cx - 15, cy))  # druhá střela vlevo
                strely.append(Strela(cx + 15, cy))  # třetí střela vpravo

            return strely

        def update(self):
            kl = pygame.key.get_pressed()
            rychlost = 6
            if kl[pygame.K_LEFT]  and self.rect.left  > 0:       self.rect.x -= rychlost
            if kl[pygame.K_RIGHT] and self.rect.right < SIRKA:    self.rect.x += rychlost

    # Demo logika
    hrac = Hrac()
    hrac.aktivuj_double_shoot()
    strely = hrac.vystrelte()
    print(f"  Strely s double shoot: {len(strely)} (normal=1, s powerupem=3)")
    print(f"  Efekt trvá do: {hrac.double_shoot_do}ms")
    pygame.quit()


# 3. Highscore – nejlepší skóre do souboru
print("\n=== 3. Highscore systém ===\n")

import json
from pathlib import Path

HIGHSCORE_SOUBOR = Path("/tmp/space_shooter_highscore.json")

def nacti_highscore() -> list[dict]:
    """Načte tabulku highscore ze souboru."""
    if HIGHSCORE_SOUBOR.exists():
        try:
            return json.loads(HIGHSCORE_SOUBOR.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            pass
    return []

def uloz_highscore(jmeno: str, skore: int, max_zaznamu: int = 10) -> int:
    """
    Přidá skóre do tabulky.
    Vrátí pořadí (1 = nejlepší).
    """
    zaznamy = nacti_highscore()
    zaznamy.append({
        "jmeno": jmeno,
        "skore": skore,
        "datum": __import__("datetime").date.today().isoformat(),
    })
    # Seřaď a ořízni
    zaznamy.sort(key=lambda z: z["skore"], reverse=True)
    zaznamy = zaznamy[:max_zaznamu]
    HIGHSCORE_SOUBOR.write_text(
        json.dumps(zaznamy, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Najdi pořadí
    for i, z in enumerate(zaznamy, 1):
        if z["jmeno"] == jmeno and z["skore"] == skore:
            return i
    return len(zaznamy)

def zobraz_highscore():
    """Vypíše tabulku highscore."""
    zaznamy = nacti_highscore()
    if not zaznamy:
        print("  Tabulka je prázdná.")
        return
    print(f"  {'#':>3}  {'Jméno':<15}  {'Skóre':>8}  {'Datum'}")
    print(f"  {'─'*3}  {'─'*15}  {'─'*8}  {'─'*10}")
    for i, z in enumerate(zaznamy, 1):
        print(f"  {i:>3}. {z['jmeno']:<15}  {z['skore']:>8}  {z['datum']}")

# Demo
import datetime
uloz_highscore("Míša",  1250)
uloz_highscore("Tomáš", 980)
uloz_highscore("Bára",  1100)
uloz_highscore("Ondra", 1500)
uloz_highscore("Míša",  1350)   # nové skóre pro Míšu

print("Highscore tabulka:")
zobraz_highscore()

poradi = uloz_highscore("Klára", 1600)
print(f"\nKlára skórovala 1600 – pořadí: #{poradi}")
zobraz_highscore()

# Úklid
HIGHSCORE_SOUBOR.unlink(missing_ok=True)

print("\n=== Shrnutí ===")
print("  1. LaserBeam sprite   – kontinuální čára, kolize s nepřáteli")
print("  2. DoubleShootPowerup – sbíratelný efekt, 3 střely najednou na 10s")
print("  3. Highscore systém   – JSON soubor, top 10 záznamy, automatické řazení")
print()
print("Spuštění hry s GUI:")
print("  python3 79_pygame.py --play")
