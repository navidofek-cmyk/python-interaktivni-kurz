"""Řešení – Lekce 14: Kreslení s Turtle

Potrebujes: python3-tk (na Linuxu: sudo apt install python3-tk)
Spust: python3 reseni/14_turtle_grafika.py
"""

import turtle
import random

okno = turtle.Screen()
okno.title("Turtle – reseni")
okno.bgcolor("black")

t = turtle.Turtle()
t.speed(0)
t.pensize(2)

# 1. Kruh pomocí t.circle()
t.penup()
t.goto(-200, 100)
t.pendown()
t.color("cyan")
# t.circle(r) nakreslí kruh poloměru r – turtle ujde 360° v malých krocích
t.circle(50)

# 2. Domeček = čtverec + trojúhelník nahoře
t.penup()
t.goto(0, -50)
t.pendown()
t.color("white")
t.pensize(3)

# Stěny domečku (čtverec)
for _ in range(4):
    t.forward(80)
    t.right(90)

# Střecha (trojúhelník nahoře) – turtle se musí přesunout na levý spodní roh střechy
t.penup()
t.goto(0, 30)    # levý spodní roh střechy = horní levý roh čtverce
t.pendown()
t.color("red")
t.right(0)       # reset natočení – turtle míří doprava

# rovnoramenný trojúhelník: doprava 80, otočit 120°, doprava 80, otočit 120°, zpět
for _ in range(3):
    t.forward(80)
    t.left(120)

# 3. Deset různobarevných čtverců na náhodných místech
barvy = ["red", "orange", "yellow", "green", "cyan", "blue", "violet",
         "pink", "lime", "magenta"]
t.pensize(2)

for barva in barvy:
    t.penup()
    # random.randint() vybere náhodnou souřadnici uvnitř okna
    t.goto(random.randint(-250, 250), random.randint(-200, 200))
    t.pendown()
    t.color(barva)
    for _ in range(4):
        t.forward(40)
        t.right(90)

print("Hotovo! Zavri okno pro ukonceni.")
turtle.done()
