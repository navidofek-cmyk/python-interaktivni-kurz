"""Řešení – Lekce 16: Hra – Chytání hvězd (Turtle)

Rozšíření: zlá hvězda (červená) ubírá body, uložení high score.
Potrebujes: python3-tk (na Linuxu: sudo apt install python3-tk)
Spust: python3 reseni/16_projekt_turtle_hra.py
"""

import turtle
import random
import time

SOUBOR_HS = "reseni_highscore.txt"


def nacti_high_score():
    """Načte high score ze souboru; vrátí 0 pokud neexistuje."""
    try:
        with open(SOUBOR_HS, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def uloz_high_score(skore):
    """Uloží skóre pokud překonalo rekord."""
    if skore > nacti_high_score():
        with open(SOUBOR_HS, "w", encoding="utf-8") as f:
            f.write(str(skore))


# ── Nastavení okna ────────────────────────────────────────────────────────────
okno = turtle.Screen()
okno.title("Chytani hvezd")
okno.bgcolor("#1a1a2e")
okno.setup(width=600, height=500)
# tracer(0) vypne automatické překreslování – my voláme update() ručně pro plynulost
okno.tracer(0)

# ── Košík ─────────────────────────────────────────────────────────────────────
kosik = turtle.Turtle()
kosik.shape("square")
kosik.shapesize(stretch_wid=1, stretch_len=3)
kosik.color("#e94560")
kosik.penup()
kosik.goto(0, -200)


def doleva():
    x = kosik.xcor()
    if x > -250:
        kosik.setx(x - 30)


def doprava():
    x = kosik.xcor()
    if x < 250:
        kosik.setx(x + 30)


okno.listen()
okno.onkeypress(doleva, "Left")
okno.onkeypress(doprava, "Right")
okno.onkeypress(doleva, "a")
okno.onkeypress(doprava, "d")

# ── Skóre ─────────────────────────────────────────────────────────────────────
skore_turtle = turtle.Turtle()
skore_turtle.hideturtle()
skore_turtle.penup()
skore_turtle.color("white")
skore_turtle.goto(-270, 210)
skore = 0
miss = 0
high_score = nacti_high_score()


def zobraz_skore():
    skore_turtle.clear()
    skore_turtle.write(
        f"Skore: {skore}   Zmeškal: {miss}/5   HS: {high_score}",
        font=("Arial", 13, "bold")
    )


zobraz_skore()

# ── Hvězdy ────────────────────────────────────────────────────────────────────
barvy_hvezd = ["yellow", "white", "cyan", "orange", "lime"]


def nova_hvezda(zla=False):
    """Vytvoří hvězdu. Zlá hvězda je červená a ubírá body."""
    h = turtle.Turtle()
    h.shape("circle")
    h.shapesize(0.8)
    # zlá hvězda je vizuálně odlišena červenou barvou
    h.color("red" if zla else random.choice(barvy_hvezd))
    h.penup()
    h.goto(random.randint(-270, 270), 230)
    h.zla = zla   # vlastní atribut pro rozlišení druhu hvězdy
    return h


hvezdy = [nova_hvezda() for _ in range(3)]
# Rozšíření 1: přidáme jednu zlou hvězdu hned na začátek
hvezdy.append(nova_hvezda(zla=True))

# ── Herní smyčka ──────────────────────────────────────────────────────────────
rychlost = 4
cas_start = time.time()

while miss < 5:
    okno.update()
    time.sleep(0.016)   # ~60 fps

    for h in hvezdy:
        h.sety(h.ycor() - rychlost)

        # chycení hvězdy
        if (abs(h.xcor() - kosik.xcor()) < 55 and
                abs(h.ycor() - kosik.ycor()) < 20):
            if h.zla:
                # Rozšíření 1: zlá hvězda odečte bod
                skore = max(0, skore - 1)
            else:
                skore += 1
            zobraz_skore()
            h.goto(random.randint(-270, 270), 230)

        # propadla dolů
        elif h.ycor() < -240:
            if not h.zla:
                miss += 1
            zobraz_skore()
            h.goto(random.randint(-270, 270), 230)

    # každých 10 bodů přidej hvězdu a zrychli
    if skore > 0 and skore % 10 == 0 and len(hvezdy) < 8:
        hvezdy.append(nova_hvezda())
        hvezdy.append(nova_hvezda(zla=True))  # přidáme i zlou
        rychlost += 0.5

cas_hry = round(time.time() - cas_start, 1)

# Rozšíření 3: uložení high score
uloz_high_score(skore)

# ── Konec hry ─────────────────────────────────────────────────────────────────
for h in hvezdy:
    h.hideturtle()
kosik.hideturtle()

konec = turtle.Turtle()
konec.hideturtle()
konec.penup()
konec.color("white")
konec.goto(0, 30)
konec.write("KONEC HRY!", align="center", font=("Arial", 28, "bold"))
konec.goto(0, -20)
konec.write(f"Skore: {skore}   Cas: {cas_hry}s",
            align="center", font=("Arial", 18, "normal"))
konec.goto(0, -60)
konec.write("Zavri okno pro ukonceni.", align="center",
            font=("Arial", 12, "normal"))

turtle.done()
