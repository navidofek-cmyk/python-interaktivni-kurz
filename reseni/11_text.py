"""Řešení – Lekce 11: Kouzla s textem"""

# 1. Kolikrát se písmeno "a" vyskytuje ve větě?
veta = "Kamarad ma rad jahody."
# str.count() projde celý řetězec a sečte výskyty daného podřetězce
pocet_a = veta.count("a")
print(f"Písmeno 'a' se ve větě '{veta}' vyskytuje {pocet_a}×")

# 2. Program, který zobrazí jméno velkými písmeny a s tečkami mezi písmeny
jmeno = "Míša"   # input() nahrazeno: "Zadej své jméno"

jmeno_velke = jmeno.upper()
# ".".join() vloží tečku mezi každý znak – výsledek: M.í.š.a
jmeno_tecky = ".".join(jmeno)

print(f"Velká písmena:       {jmeno_velke}")
print(f"S tečkami:           {jmeno_tecky}")

# 3. Zjisti, jestli zadané slovo začíná a končí stejným písmenem
slovo = "kajak"   # input() nahrazeno: "Zadej slovo"
# lower() zajistí, že porovnáváme bez ohledu na velikost písmen
prvni = slovo[0].lower()
posledni = slovo[-1].lower()

if prvni == posledni:
    print(f"Slovo '{slovo}' začíná i končí písmenem '{prvni}'.")
else:
    print(f"Slovo '{slovo}' začíná '{prvni}' a končí '{posledni}' – neshodují se.")

# Bonus: ověření palindromu (z lekce)
zprava = "racecar"   # input() nahrazeno: "Napiš zprávu"
cista = zprava.lower().replace(" ", "")
# [::-1] obrátí pořadí znaků – pythonický způsob reversního slicingu
if cista == cista[::-1]:
    print(f"'{zprava}' JE palindrom!")
else:
    print(f"'{zprava}' není palindrom.")
