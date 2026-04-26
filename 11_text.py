"""
LEKCE 11: Kouzla s textem
===========================
Text (string) má spoustu šikovných triků!
"""

veta = "Ahoj, jmenuji se Python!"

print(len(veta))              # délka textu
print(veta.upper())           # VELKÁ PÍSMENA
print(veta.lower())           # malá písmena
print(veta.replace("Python", "Míša"))   # nahraď slovo
print(veta.startswith("Ahoj"))          # True/False
print(veta.count("i"))        # kolikrát se vyskytuje písmeno

print("\n--- Řezání textu ---")
slovo = "programování"
print(slovo[0])       # první písmeno
print(slovo[-1])      # poslední písmeno
print(slovo[0:7])     # prvních 7 písmen
print(slovo[::-1])    # text pozpátku!

print("\n--- Rozdělení a spojení ---")
veta2 = "jablko,banán,jahoda,meloun"
seznam = veta2.split(",")     # rozdělí podle čárky
print(seznam)

zpet = " | ".join(seznam)     # spojí jinak
print(zpet)

print("\n=== Tajná zpráva ===")
zprava = input("Napiš zprávu: ")
print("Pozpátku:    ", zprava[::-1])
print("Velká:       ", zprava.upper())
print("Počet písmen:", len(zprava.replace(" ", "")))

# Zjistí, jestli je zpráva palindrom (čte se stejně oběma směry)
cistá = zprava.lower().replace(" ", "")
if cistá == cistá[::-1]:
    print("Je to PALINDROM! (čte se stejně pozpátku)")
else:
    print("Není palindrom.")

# TVOJE ÚLOHA:
# 1. Zjisti, kolikrát se písmeno "a" vyskytuje ve větě "Kamarád má rád jahody."
# 2. Napiš program, který přijme jméno a zobrazí ho:
#    - velkými písmeny
#    - s tečkami mezi písmeny: M.í.š.a
# 3. Zjisti, jestli zadané slovo začíná a končí stejným písmenem.
