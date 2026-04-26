"""
PROJEKT: Hra – Chytání hvězd (Turtle)
=======================================
Pohybuj košíkem a chytej padající hvězdy!
Otevře se grafické okno.

Ovládání: ← → šipky (nebo A D)
"""

import turtle
import random
import time

# ── Nastavení okna ───────────────────────────────────────────────────────────
okno = turtle.Screen()
okno.title("Chytání hvězd ⭐")
okno.bgcolor("#1a1a2e")
okno.setup(width=600, height=500)
okno.tracer(0)  # ručně řídíme překreslování – plynulost

# ── Košík ────────────────────────────────────────────────────────────────────
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

# ── Skóre ────────────────────────────────────────────────────────────────────
skore_turtle = turtle.Turtle()
skore_turtle.hideturtle()
skore_turtle.penup()
skore_turtle.color("white")
skore_turtle.goto(-270, 210)
skore = 0
miss = 0

def zobraz_skore():
    skore_turtle.clear()
    skore_turtle.write(f"⭐ Skóre: {skore}   ❌ Zmeškal: {miss}/5",
                       font=("Arial", 14, "bold"))

zobraz_skore()

# ── Hvězdy ───────────────────────────────────────────────────────────────────
barvy_hvezd = ["yellow", "white", "cyan", "orange", "lime"]

def nova_hvezda():
    h = turtle.Turtle()
    h.shape("circle")
    h.shapesize(0.8)
    h.color(random.choice(barvy_hvezd))
    h.penup()
    h.goto(random.randint(-270, 270), 230)
    return h

hvezdy = [nova_hvezda() for _ in range(3)]

# ── Herní smyčka ─────────────────────────────────────────────────────────────
rychlost = 4
cas_start = time.time()

while miss < 5:
    okno.update()
    time.sleep(0.016)   # ~60 fps

    for h in hvezdy:
        h.sety(h.ycor() - rychlost)

        # chycení
        if (abs(h.xcor() - kosik.xcor()) < 55 and
                abs(h.ycor() - kosik.ycor()) < 20):
            skore += 1
            zobraz_skore()
            h.goto(random.randint(-270, 270), 230)

        # propadla dolů
        elif h.ycor() < -240:
            miss += 1
            zobraz_skore()
            h.goto(random.randint(-270, 270), 230)

    # každých 10 bodů přidej hvězdu a zrychli
    if skore > 0 and skore % 10 == 0 and len(hvezdy) < 7:
        hvezdy.append(nova_hvezda())
        rychlost += 0.5

cas_hry = round(time.time() - cas_start, 1)

# ── Konec hry ────────────────────────────────────────────────────────────────
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
konec.write(f"Skóre: {skore}   Čas: {cas_hry}s",
            align="center", font=("Arial", 18, "normal"))
konec.goto(0, -60)
konec.write("Zavři okno pro ukončení.", align="center",
            font=("Arial", 12, "normal"))

turtle.done()

# ROZŠÍŘENÍ:
# 1. Přidej "zlou hvězdu" (červenou), která ubírá body.
# 2. Přidej zvukový efekt při chycení (import winsound nebo playsound).
# 3. Ulož high score do souboru highscore.txt.
