"""
LEKCE 14: Kreslení s Turtle
=============================
Turtle je želva, která kreslí čáry! Otevře se grafické okno.
Spusť a sleduj co se děje.

Potřebuješ: python3-tk (na Linuxu: sudo apt install python3-tk)
"""

import turtle
import random

t = turtle.Turtle()
t.speed(5)          # rychlost (1=pomalu, 10=rychle, 0=max)

okno = turtle.Screen()
okno.title("Kresliaci želva")
okno.bgcolor("black")
t.color("white")

print("Kreslím čtverec...")
t.pensize(3)
for _ in range(4):
    t.forward(100)
    t.right(90)

t.penup()
t.goto(-200, 0)
t.pendown()

print("Kreslím trojúhelník...")
t.color("yellow")
for _ in range(3):
    t.forward(100)
    t.left(120)

t.penup()
t.goto(100, 100)
t.pendown()

print("Kreslím hvězdu...")
t.color("red")
t.pensize(2)
for _ in range(5):
    t.forward(100)
    t.right(144)

t.penup()
t.goto(0, -150)
t.pendown()

print("Kreslím duhovou spirálu...")
barvy = ["red", "orange", "yellow", "green", "cyan", "blue", "violet"]
t.speed(0)
for i in range(200):
    t.color(barvy[i % len(barvy)])
    t.forward(i * 0.5)
    t.right(91)

print("Hotovo! Zavři okno pro ukončení.")
turtle.done()

# TVOJE ÚLOHA:
# 1. Zkus nakreslit kruh: t.circle(50)
# 2. Nakresli domeček (čtverec + trojúhelník nahoře).
# 3. Nakresli 10 různobarevných čtverců na náhodných místech.
#    Nápověda: t.goto(random.randint(-200,200), random.randint(-200,200))
