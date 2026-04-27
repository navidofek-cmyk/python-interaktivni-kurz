"""
LEKCE 86: tkinter – desktop GUI
==================================
Vestavěné – žádná instalace!
(Linux: sudo apt install python3-tk pokud chybí)

tkinter = Tk interface pro Python. Základní widget toolkit.
Funguje na Windows, Mac, Linux.

Moderní alternativy:
  PyQt6 / PySide6  – bohatší, Qt framework
  wx Python        – nativní widgety
  Dear PyGui       – GPU-akcelerované
  Textual          – TUI (terminálové GUI)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import sys

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní okno a widgety
# ══════════════════════════════════════════════════════════════

print("=== tkinter – základní demo ===\n")
print("Spuštění jednotlivých demo oken:")
print("  demo_zaklad()     – widgety")
print("  demo_layout()     – rozmístění")
print("  demo_canvas()     – kreslení")
print("  demo_texteditor() – mini textový editor")
print()

def demo_zaklad():
    root = tk.Tk()
    root.title("Základní widgety")
    root.geometry("400x500")
    root.resizable(True, True)

    # StringVar – reaktivní proměnná navázaná na widget
    jmeno_var   = tk.StringVar()
    slider_var  = tk.DoubleVar(value=50)
    check_var   = tk.BooleanVar(value=False)
    radio_var   = tk.StringVar(value="Python")

    # Label
    tk.Label(root, text="Tvoje jméno:", font=("Arial", 11)).pack(pady=(15, 2))

    # Entry (textové pole)
    entry = tk.Entry(root, textvariable=jmeno_var, width=30, font=("Arial", 12))
    entry.pack()
    entry.focus()

    # Button
    def pozdrav():
        jmeno = jmeno_var.get().strip()
        if jmeno:
            messagebox.showinfo("Pozdrav", f"Ahoj, {jmeno}! 🐍")
        else:
            messagebox.showwarning("Pozor", "Zadej své jméno!")

    tk.Button(root, text="Pozdrav!", command=pozdrav,
               bg="#2E86AB", fg="white", font=("Arial", 11),
               padx=10, pady=5).pack(pady=10)

    # Scale (slider)
    tk.Label(root, text="Věk:", font=("Arial", 11)).pack()
    frame_slider = tk.Frame(root)
    frame_slider.pack()
    tk.Scale(frame_slider, from_=0, to=100, orient=tk.HORIZONTAL,
              variable=slider_var, length=200).pack(side=tk.LEFT)
    tk.Label(frame_slider, textvariable=slider_var, width=4).pack(side=tk.LEFT)

    # Checkbutton
    tk.Checkbutton(root, text="Souhlasím s podmínkami",
                    variable=check_var).pack(pady=5)

    # Radiobuttons
    tk.Label(root, text="Oblíbený jazyk:", font=("Arial", 11)).pack(pady=(10, 2))
    for lang in ["Python", "JavaScript", "Rust", "Go"]:
        tk.Radiobutton(root, text=lang, variable=radio_var,
                        value=lang).pack(anchor=tk.W, padx=50)

    # Combobox (ttk)
    tk.Label(root, text="Předmět:", font=("Arial", 11)).pack(pady=(10, 2))
    combo = ttk.Combobox(root, values=["Python", "Matematika", "Fyzika", "Informatika"],
                          state="readonly", width=25)
    combo.current(0)
    combo.pack()

    # Status bar
    status = tk.Label(root, text="Připraveno", bd=1, relief=tk.SUNKEN,
                       anchor=tk.W, bg="#f0f0f0")
    status.pack(side=tk.BOTTOM, fill=tk.X)

    def aktualizuj_status(*args):
        status.config(text=f"Jazyk: {radio_var.get()}  |  Věk: {int(slider_var.get())}")

    radio_var.trace_add("write", aktualizuj_status)
    slider_var.trace_add("write", aktualizuj_status)

    root.mainloop()


def demo_layout():
    """Ukázka grid layoutu – formulář."""
    root = tk.Tk()
    root.title("Grid Layout – Formulář")
    root.geometry("380x300")

    pole = {}
    for i, (label, placeholder) in enumerate([
        ("Jméno:", "Zadej jméno"),
        ("Email:", "user@example.com"),
        ("Telefon:", "+420 ..."),
        ("Město:", "Praha"),
    ]):
        tk.Label(root, text=label, anchor="e").grid(
            row=i, column=0, padx=10, pady=8, sticky="e")
        var = tk.StringVar()
        e = tk.Entry(root, textvariable=var, width=28)
        e.insert(0, placeholder)
        e.config(fg="grey")

        def on_focus_in(event, entry=e, ph=placeholder):
            if entry.get() == ph:
                entry.delete(0, tk.END)
                entry.config(fg="black")

        def on_focus_out(event, entry=e, ph=placeholder):
            if not entry.get():
                entry.insert(0, ph)
                entry.config(fg="grey")

        e.bind("<FocusIn>",  on_focus_in)
        e.bind("<FocusOut>", on_focus_out)
        e.grid(row=i, column=1, padx=10, pady=8)
        pole[label] = var

    def odeslat():
        data = {k.rstrip(":"): v.get() for k, v in pole.items()}
        messagebox.showinfo("Odesláno", "\n".join(f"{k}: {v}" for k, v in data.items()))

    tk.Button(root, text="Odeslat formulář", command=odeslat,
               bg="#3fb950", fg="white", padx=15, pady=6).grid(
        row=4, column=0, columnspan=2, pady=15)

    root.mainloop()


def demo_canvas():
    """Kreslení na Canvas – interaktivní."""
    root = tk.Tk()
    root.title("Canvas – Kreslení")
    root.geometry("600x500")

    aktualni_barva = tk.StringVar(value="#2E86AB")
    tloustka = tk.IntVar(value=3)

    # Toolbar
    toolbar = tk.Frame(root, bg="#f0f0f0", pady=5)
    toolbar.pack(fill=tk.X)

    def vyber_barvu():
        barva = colorchooser.askcolor(color=aktualni_barva.get())[1]
        if barva:
            aktualni_barva.set(barva)
            btn_barva.config(bg=barva)

    btn_barva = tk.Button(toolbar, text="  Barva  ", bg=aktualni_barva.get(),
                           command=vyber_barvu)
    btn_barva.pack(side=tk.LEFT, padx=5)

    tk.Label(toolbar, text="Tloušťka:", bg="#f0f0f0").pack(side=tk.LEFT)
    tk.Scale(toolbar, from_=1, to=20, orient=tk.HORIZONTAL,
              variable=tloustka, length=100, bg="#f0f0f0").pack(side=tk.LEFT)

    def vymaz():
        canvas.delete("all")

    tk.Button(toolbar, text="Vymazat", command=vymaz).pack(side=tk.LEFT, padx=5)

    # Canvas
    canvas = tk.Canvas(root, bg="white", cursor="crosshair")
    canvas.pack(fill=tk.BOTH, expand=True)

    predchozi = [None, None]

    def zacni_kreslit(event):
        predchozi[0], predchozi[1] = event.x, event.y

    def kresli(event):
        if predchozi[0] is not None:
            canvas.create_line(
                predchozi[0], predchozi[1], event.x, event.y,
                fill=aktualni_barva.get(), width=tloustka.get(),
                capstyle=tk.ROUND, smooth=True,
            )
        predchozi[0], predchozi[1] = event.x, event.y

    canvas.bind("<Button-1>",  zacni_kreslit)
    canvas.bind("<B1-Motion>", kresli)

    root.mainloop()


def demo_texteditor():
    """Mini textový editor s menu."""
    root = tk.Tk()
    root.title("Mini Textový Editor")
    root.geometry("700x500")

    aktualni_soubor = [None]

    # Menu
    menubar = tk.Menu(root)
    soubor_menu = tk.Menu(menubar, tearoff=0)

    def novy():
        text.delete("1.0", tk.END)
        aktualni_soubor[0] = None
        root.title("Nový soubor – Editor")

    def otevri():
        cesta = filedialog.askopenfilename(
            filetypes=[("Python", "*.py"), ("Text", "*.txt"), ("Vše", "*.*")])
        if cesta:
            with open(cesta, "r", encoding="utf-8") as f:
                text.delete("1.0", tk.END)
                text.insert("1.0", f.read())
            aktualni_soubor[0] = cesta
            root.title(f"{cesta} – Editor")

    def uloz():
        if aktualni_soubor[0]:
            with open(aktualni_soubor[0], "w", encoding="utf-8") as f:
                f.write(text.get("1.0", tk.END))
        else:
            uloz_jako()

    def uloz_jako():
        cesta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Python", "*.py")])
        if cesta:
            aktualni_soubor[0] = cesta
            uloz()
            root.title(f"{cesta} – Editor")

    soubor_menu.add_command(label="Nový",      command=novy,     accelerator="Ctrl+N")
    soubor_menu.add_command(label="Otevřít…",  command=otevri,   accelerator="Ctrl+O")
    soubor_menu.add_separator()
    soubor_menu.add_command(label="Uložit",    command=uloz,     accelerator="Ctrl+S")
    soubor_menu.add_command(label="Uložit jako…", command=uloz_jako)
    soubor_menu.add_separator()
    soubor_menu.add_command(label="Konec",     command=root.quit)
    menubar.add_cascade(label="Soubor", menu=soubor_menu)
    root.config(menu=menubar)

    # Klávesové zkratky
    root.bind("<Control-n>", lambda e: novy())
    root.bind("<Control-o>", lambda e: otevri())
    root.bind("<Control-s>", lambda e: uloz())

    # Hlavní widget
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text = tk.Text(frame, yscrollcommand=scrollbar.set,
                    font=("Courier", 12), undo=True,
                    wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4",
                    insertbackground="white", selectbackground="#264f78",
                    padx=5, pady=5)
    text.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=text.yview)

    text.insert("1.0", '# Vítej v mini textovém editoru!\nprint("Ahoj!")\n')

    # Status bar
    status = tk.Label(root, text="Ln 1, Col 1", bd=1, relief=tk.SUNKEN,
                       anchor=tk.W, bg="#007acc", fg="white")
    status.pack(side=tk.BOTTOM, fill=tk.X)

    def aktualizuj_status(event=None):
        pos  = text.index(tk.INSERT)
        ln, col = pos.split(".")
        n_znaku = len(text.get("1.0", tk.END)) - 1
        status.config(text=f"Ln {ln}, Col {int(col)+1}  |  Znaků: {n_znaku}")

    text.bind("<KeyRelease>", aktualizuj_status)
    text.bind("<Button-1>",   aktualizuj_status)

    root.mainloop()


# Spusť konkrétní demo nebo zobraz výběr
if __name__ == "__main__":
    print("Vyber demo:")
    print("  1) Základní widgety")
    print("  2) Grid formulář")
    print("  3) Canvas kreslení")
    print("  4) Textový editor")

    volba = input("\nVolba (1-4): ").strip()
    demoa = {"1": demo_zaklad, "2": demo_layout,
              "3": demo_canvas, "4": demo_texteditor}
    if volba in demoa:
        demoa[volba]()
    else:
        print("Spusť: python3 86_tkinter.py")

# TVOJE ÚLOHA:
# 1. Přidej do textového editoru funkci "Najít a nahradit" (Ctrl+H).
# 2. Napiš kalkulačku s tlačítky 0-9 + operátory.
# 3. Přidej do canvas možnost kreslení obdélníků a kruhů (výběr nástroje).
