"""
LEKCE 79: Pygame – 2D hry v Pythonu
======================================
pip install pygame

Pygame = knihovna pro 2D hry: okno, grafika, zvuk, vstupy.
Tato lekce postaví kompletní hru – Space Shooter!

Herní smyčka (game loop):
  while hra_bezi:
      1. Zpracuj vstupy (klávesy, myš)
      2. Aktualizuj stav hry (pohyb, kolize)
      3. Vykresli (clear + draw + flip)
      4. Nastav FPS (clock.tick)
"""

import sys
import random
import math
import time

try:
    import pygame
    pygame.init()
    PYGAME_OK = True
except ImportError:
    print("Pygame není nainstalováno: pip install pygame")
    PYGAME_OK = False

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ZÁKLAD – okno, barvy, tvar
# ══════════════════════════════════════════════════════════════

print("=== Pygame základ ===\n")
print("""\
import pygame
pygame.init()

obrazovka = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Moje hra")
hodiny = pygame.time.Clock()

# Barvy (R, G, B)
CERNY  = (0,   0,   0  )
BILY   = (255, 255, 255)
MODRY  = (50,  120, 200)
CERVENY= (220, 50,  50 )

running = True
x, y = 400, 300   # pozice hráče

while running:
    # 1. Události
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # 2. Vstupy
    klavesy = pygame.key.get_pressed()
    if klavesy[pygame.K_LEFT]:  x -= 5
    if klavesy[pygame.K_RIGHT]: x += 5
    if klavesy[pygame.K_UP]:    y -= 5
    if klavesy[pygame.K_DOWN]:  y += 5

    # 3. Kreslení
    obrazovka.fill(CERNY)
    pygame.draw.circle(obrazovka, MODRY, (x, y), 20)
    pygame.draw.rect(obrazovka, CERVENY, (100, 100, 50, 50))

    pygame.display.flip()
    hodiny.tick(60)   # 60 FPS

pygame.quit()
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: KOMPLETNÍ HRA – Space Shooter
# ══════════════════════════════════════════════════════════════

print("=== Space Shooter ===\n")
print("Spusť spustit_hru() pro okno s hrou.\n")

if PYGAME_OK:
    # Konstanty
    SIRKA, VYSKA = 600, 700
    FPS          = 60
    CERNY   = (0, 0, 0)
    BILY    = (255, 255, 255)
    ZELENY  = (50, 200, 80)
    CERVENY = (220, 50, 50)
    ZLATY   = (255, 215, 0)
    MODRY   = (50, 120, 220)
    SEDY    = (100, 100, 100)

    class Hrac(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__()
            # Nakresli loď trojúhelníkem
            self.image = pygame.Surface((40, 50), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, ZELENY,
                                 [(20, 0), (0, 50), (40, 50)])
            pygame.draw.polygon(self.image, BILY,
                                 [(20, 5), (5, 45), (35, 45)], 2)
            self.rect  = self.image.get_rect(center=(SIRKA//2, VYSKA - 80))
            self.rychlost    = 6
            self.hp          = 3
            self.posledni_vyst = 0
            self.cooldown    = 250   # ms mezi výstřely

        def update(self):
            kl = pygame.key.get_pressed()
            if kl[pygame.K_LEFT]  and self.rect.left  > 0:
                self.rect.x -= self.rychlost
            if kl[pygame.K_RIGHT] and self.rect.right < SIRKA:
                self.rect.x += self.rychlost
            if kl[pygame.K_UP]    and self.rect.top   > VYSKA//2:
                self.rect.y -= self.rychlost
            if kl[pygame.K_DOWN]  and self.rect.bottom< VYSKA:
                self.rect.y += self.rychlost

        def muze_strilet(self) -> bool:
            return pygame.time.get_ticks() - self.posledni_vyst > self.cooldown

        def vystrelte(self) -> "Strela":
            self.posledni_vyst = pygame.time.get_ticks()
            return Strela(self.rect.centerx, self.rect.top, -10, ZLATY)

    class Nepritel(pygame.sprite.Sprite):
        def __init__(self, x: int):
            super().__init__()
            self.image = pygame.Surface((36, 30), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, CERVENY,
                                 [(18, 30), (0, 0), (36, 0)])
            pygame.draw.polygon(self.image, BILY,
                                 [(18, 26), (4, 4), (32, 4)], 2)
            self.rect  = self.image.get_rect(
                center=(x, random.randint(-50, -10)))
            self.rychlost = random.uniform(1.5, 3.5)
            self.hp       = 2

        def update(self):
            self.rect.y += self.rychlost
            if self.rect.top > VYSKA:
                self.kill()

    class Strela(pygame.sprite.Sprite):
        def __init__(self, x: int, y: int, vy: int, barva: tuple):
            super().__init__()
            self.image = pygame.Surface((4, 14), pygame.SRCALPHA)
            pygame.draw.rect(self.image, barva, (0, 0, 4, 14),
                              border_radius=2)
            self.rect = self.image.get_rect(center=(x, y))
            self.vy   = vy

        def update(self):
            self.rect.y += self.vy
            if self.rect.bottom < 0 or self.rect.top > VYSKA:
                self.kill()

    class Exploze(pygame.sprite.Sprite):
        def __init__(self, x: int, y: int):
            super().__init__()
            self.cas   = 0
            self.x, self.y = x, y
            self._generuj(0)

        def _generuj(self, cas: int):
            r = max(2, 20 - cas * 2)
            self.image = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            alfa = max(0, 255 - cas * 25)
            barva = (*ZLATY, alfa)
            pygame.draw.circle(self.image, barva, (r, r), r)
            self.rect = self.image.get_rect(center=(self.x, self.y))

        def update(self):
            self.cas += 1
            if self.cas > 10:
                self.kill()
            else:
                self._generuj(self.cas)

    class HvezdnePozadi:
        """Scrollující hvězdné pozadí."""
        def __init__(self):
            self.hvezdy = [
                [random.randint(0, SIRKA), random.randint(0, VYSKA),
                 random.uniform(0.3, 2.0)]
                for _ in range(120)
            ]

        def update_a_kresli(self, obrazovka):
            for hv in self.hvezdy:
                hv[1] += hv[2]
                if hv[1] > VYSKA:
                    hv[1] = 0
                    hv[0] = random.randint(0, SIRKA)
                r    = max(1, int(hv[2]))
                alfa = min(255, int(hv[2] * 120))
                pygame.draw.circle(obrazovka, (alfa, alfa, alfa),
                                    (int(hv[0]), int(hv[1])), r)

    def spust_hru():
        obrazovka = pygame.display.set_mode((SIRKA, VYSKA))
        pygame.display.set_caption("Space Shooter – Pygame")
        hodiny = pygame.time.Clock()
        font_v = pygame.font.SysFont("monospace", 28, bold=True)
        font_m = pygame.font.SysFont("monospace", 18)

        pozadi   = HvezdnePozadi()
        hrac     = Hrac()
        nepratelé = pygame.sprite.Group()
        strely_h = pygame.sprite.Group()
        exploze  = pygame.sprite.Group()
        vse      = pygame.sprite.Group(hrac)

        skore         = 0
        spawn_cas     = pygame.time.get_ticks()
        spawn_interval= 1500   # ms

        running = True
        game_over = False

        while running:
            dt = hodiny.tick(FPS)

            # ── Události ──────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_SPACE and not game_over:
                        if hrac.muze_strilet():
                            strela = hrac.vystrelte()
                            strely_h.add(strela)
                            vse.add(strela)
                    if event.key == pygame.K_r and game_over:
                        spust_hru()
                        return

            if not game_over:
                # ── Spawn nepřátel ────────────────────────────
                ted = pygame.time.get_ticks()
                if ted - spawn_cas > spawn_interval:
                    spawn_cas = ted
                    nep = Nepritel(random.randint(20, SIRKA-20))
                    nepratelé.add(nep)
                    vse.add(nep)
                    spawn_interval = max(400, spawn_interval - 15)

                # ── Update ────────────────────────────────────
                hrac.update()
                nepratelé.update()
                strely_h.update()
                exploze.update()

                # Kolize: střely hráče × nepřátelé
                zásahy = pygame.sprite.groupcollide(
                    strely_h, nepratelé, True, False)
                for strela, zasazeni in zásahy.items():
                    for nep in zasazeni:
                        nep.hp -= 1
                        ex = Exploze(nep.rect.centerx, nep.rect.centery)
                        exploze.add(ex); vse.add(ex)
                        if nep.hp <= 0:
                            nep.kill()
                            skore += 10

                # Kolize: nepřátelé × hráč
                hit = pygame.sprite.spritecollide(hrac, nepratelé, True)
                if hit:
                    hrac.hp -= 1
                    ex = Exploze(hrac.rect.centerx, hrac.rect.centery)
                    exploze.add(ex); vse.add(ex)
                    if hrac.hp <= 0:
                        game_over = True

            # ── Kreslení ──────────────────────────────────────
            obrazovka.fill((5, 5, 20))
            pozadi.update_a_kresli(obrazovka)
            vse.draw(obrazovka)

            # HUD
            skore_txt = font_v.render(f"SKÓRE: {skore}", True, BILY)
            obrazovka.blit(skore_txt, (10, 10))
            hp_txt = font_m.render(f"HP: {'♥ ' * hrac.hp}", True, CERVENY)
            obrazovka.blit(hp_txt, (SIRKA - 120, 12))

            if game_over:
                over = font_v.render("GAME OVER", True, CERVENY)
                restart = font_m.render("[R] Restart  [Esc] Konec", True, SEDY)
                obrazovka.blit(over,    over.get_rect(center=(SIRKA//2, VYSKA//2 - 20)))
                obrazovka.blit(restart, restart.get_rect(center=(SIRKA//2, VYSKA//2 + 20)))

            pygame.display.flip()

        pygame.quit()

    print("Spuštění hry:")
    print("  spust_hru()")
    print()
    print("Ovládání:")
    print("  ← → ↑ ↓   pohyb")
    print("  Mezerník   střílej")
    print("  Esc        konec")
    print("  R          restart (po game over)")

    # Automatické spuštění pokud běžíme přímo
    if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--play":
        spust_hru()

else:
    print("  [Pygame není dostupný – nainstaluj: pip install pygame]")

print("""
=== Pygame API přehled ===

  pygame.display   → okno, fullscreen, titulek
  pygame.event     → myš, klávesnice, zavření
  pygame.draw      → čáry, obdélníky, kruhy, polygony
  pygame.image     → načtení PNG/JPG
  pygame.font      → text
  pygame.mixer     → zvuk (WAV, MP3)
  pygame.sprite    → správa herních objektů a kolize
  pygame.time      → FPS, timing, delay
  pygame.Surface   → grafická plocha (canvas)

  Sprite.kill()    → odstraní sprite ze všech grup
  groupcollide()   → kolize mezi dvěma grupami
  spritecollide()  → kolize sprite × grupa
""")

# TVOJE ÚLOHA:
# 1. Přidej laser beam (nepřetržitá čára místo kuliček).
# 2. Přidej power-up (zelená hvězdička = dočasně 2 střely najednou).
# 3. Přidej highscore – ulož nejlepší skóre do souboru (lekce 13).
# 4. Přidej zvuky: pygame.mixer.Sound("laser.wav").play()
