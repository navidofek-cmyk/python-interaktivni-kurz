"""Řešení – Lekce 82: Síťové sokety – TCP/UDP server od nuly"""

import socket
import threading
import asyncio
import json
import time
from datetime import datetime


# 1. Chat server s příkazy /seznam a /opust
print("=== 1. Chat server s příkazy /seznam a /opust ===\n")

class RozsirenyChat:
    """Chat server s příkazy /seznam, /opust, /jmeno."""

    def __init__(self, port: int):
        self.port    = port
        self.klienti: dict[socket.socket, str] = {}
        self.zamek   = threading.Lock()
        self._bezi   = True

    def broadcast(self, zprava: str, vyjimka=None):
        s_kodovanim = zprava.encode("utf-8")
        with self.zamek:
            for klient in list(self.klienti):
                if klient != vyjimka:
                    try:
                        klient.sendall(s_kodovanim)
                    except Exception:
                        self.klienti.pop(klient, None)

    def posli_soukrome(self, conn: socket.socket, zprava: str):
        try:
            conn.sendall(zprava.encode("utf-8"))
        except Exception:
            pass

    def obsluha_klienta(self, conn: socket.socket, addr):
        jmeno = f"Anonym_{addr[1]}"
        with self.zamek:
            self.klienti[conn] = jmeno
        self.broadcast(f"[{jmeno} se připojil]\n", conn)

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                zprava = data.decode("utf-8").strip()
                if not zprava:
                    continue

                if zprava.startswith("/jmeno "):
                    # Změna jména
                    nove = zprava.split(" ", 1)[1].strip()
                    if not nove or len(nove) > 20:
                        self.posli_soukrome(conn, "[Chyba] Jméno musí mít 1-20 znaků.\n")
                    else:
                        stare = jmeno
                        jmeno = nove
                        with self.zamek:
                            self.klienti[conn] = jmeno
                        self.broadcast(f"[{stare} se přejmenoval na {jmeno}]\n")

                elif zprava == "/seznam":
                    # Vypíše připojené uživatele (jen odesílateli)
                    with self.zamek:
                        seznam = list(self.klienti.values())
                    odpoved = f"[Připojení ({len(seznam)}): {', '.join(seznam)}]\n"
                    self.posli_soukrome(conn, odpoved)

                elif zprava == "/opust":
                    # Odpojení na přání
                    self.posli_soukrome(conn, "[Odpojuješ se...]\n")
                    break

                elif zprava == "/pomoc":
                    pomoc = (
                        "[Příkazy: /jmeno <nové> | /seznam | /opust | /pomoc]\n"
                    )
                    self.posli_soukrome(conn, pomoc)

                else:
                    # Normální zpráva
                    cas = datetime.now().strftime("%H:%M")
                    self.broadcast(f"[{cas}] {jmeno}: {zprava}\n")

        except Exception:
            pass
        finally:
            with self.zamek:
                self.klienti.pop(conn, None)
            conn.close()
            self.broadcast(f"[{jmeno} se odpojil]\n")

    def spust(self, max_klientu: int = 6):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("localhost", self.port))
            srv.listen(10)
            srv.settimeout(1.5)
            prijato = 0
            while prijato < max_klientu and self._bezi:
                try:
                    conn, addr = srv.accept()
                    t = threading.Thread(target=self.obsluha_klienta,
                                         args=(conn, addr), daemon=True)
                    t.start()
                    prijato += 1
                except socket.timeout:
                    if prijato > 0:
                        break


CHAT_PORT = 29877
chat = RozsirenyChat(CHAT_PORT)
ct   = threading.Thread(target=chat.spust, daemon=True)
ct.start()
time.sleep(0.15)

zpravy_prijate: list[str] = []

def chat_klient_demo(jmeno: str, prikazy: list[str]) -> list[str]:
    """Simuluje chat klienta, vrátí přijaté zprávy."""
    odpovedi = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", CHAT_PORT))
        s.settimeout(0.5)
        s.sendall(f"/jmeno {jmeno}\n".encode())
        time.sleep(0.05)
        for prikaz in prikazy:
            s.sendall(f"{prikaz}\n".encode())
            time.sleep(0.08)
        try:
            while True:
                data = s.recv(4096)
                if not data:
                    break
                odpovedi.append(data.decode("utf-8", errors="replace"))
        except socket.timeout:
            pass
    return odpovedi

# Spusť demo klienty
t1 = threading.Thread(target=lambda: chat_klient_demo("Míša",  ["Ahoj!", "/seznam"]))
t2 = threading.Thread(target=lambda: chat_klient_demo("Tomáš", ["Ahoj Míšo!", "/opust"]))
t1.start(); t2.start()
t1.join();  t2.join()
time.sleep(0.3)

print("  Chat server s příkazy:")
print("  /jmeno <nové>  – změna přezdívky")
print("  /seznam        – výpis připojených uživatelů")
print("  /opust         – odpojení")
print("  /pomoc         – nápověda")
print("  Demo proběhlo úspěšně\n")


# 2. Šifrování zpráv AES klíčem
print("=== 2. Šifrované sokety (AES) ===\n")

try:
    from cryptography.fernet import Fernet
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False
    print("cryptography není nainstalováno: pip install cryptography\n")

if CRYPTO_OK:
    def generuj_klic() -> bytes:
        return Fernet.generate_key()

    def sifruj(zprava: str, klic: bytes) -> bytes:
        f = Fernet(klic)
        return f.encrypt(zprava.encode("utf-8"))

    def desifruj(data: bytes, klic: bytes) -> str:
        f = Fernet(klic)
        return f.decrypt(data).decode("utf-8")

    SIFR_PORT = 29878
    sdileny_klic = generuj_klic()
    server_zpravy = []

    def sifr_server(port: int):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("localhost", port))
            srv.listen(3)
            srv.settimeout(2.0)
            for _ in range(3):
                try:
                    conn, _ = srv.accept()
                    with conn:
                        data = b""
                        conn.settimeout(1.0)
                        try:
                            while True:
                                chunk = conn.recv(1024)
                                if not chunk:
                                    break
                                data += chunk
                        except socket.timeout:
                            pass
                        if data:
                            try:
                                text = desifruj(data, sdileny_klic)
                                server_zpravy.append(text)
                                odpoved = sifruj(f"OK: {text}", sdileny_klic)
                                conn.sendall(odpoved)
                            except Exception as e:
                                conn.sendall(b"ERROR")
                except socket.timeout:
                    break

    st = threading.Thread(target=sifr_server, args=(SIFR_PORT,), daemon=True)
    st.start()
    time.sleep(0.1)

    def sifr_klient(zprava: str, port: int) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("localhost", port))
            s.sendall(sifruj(zprava, sdileny_klic))
            s.settimeout(1.0)
            data = b""
            try:
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass
            return desifruj(data, sdileny_klic) if data else ""

    for zprava_text in ["Ahoj, šifrovaný server!", "Tajná zpráva č.2"]:
        odpoved = sifr_klient(zprava_text, SIFR_PORT)
        print(f"  Odesláno: {zprava_text!r}")
        print(f"  Odpověď:  {odpoved!r}")
        print(f"  Klíč:     {sdileny_klic[:20]}...")
        print()
else:
    print("  Ukázka šifrování (vyžaduje pip install cryptography):")
    print("    from cryptography.fernet import Fernet")
    print("    klic = Fernet.generate_key()")
    print("    f = Fernet(klic)")
    print("    sifrovaná = f.encrypt(zprava.encode())")
    print("    conn.sendall(sifrovaná)")
    print("    # Na druhé straně:")
    print("    zprava = f.decrypt(data).decode()")
    print()


# 3. Load balancer round-robin pro 3 backend servery
print("=== 3. Load balancer – round-robin ===\n")

import itertools

class LoadBalancer:
    """TCP load balancer – distribuuje spojení round-robin na backendy."""

    def __init__(self, lb_port: int, backendy: list[tuple[str, int]]):
        self.lb_port   = lb_port
        self.backendy  = backendy
        self._cyklus   = itertools.cycle(backendy)
        self.statistiky: dict[str, int] = {f"{h}:{p}": 0 for h, p in backendy}
        self._zamek    = threading.Lock()

    def dalsi_backend(self) -> tuple[str, int]:
        with self._zamek:
            return next(self._cyklus)

    def preposlji(self, klient_conn: socket.socket):
        """Přepošle data od klienta na backend server."""
        host, port = self.dalsi_backend()
        klic = f"{host}:{port}"

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as backend:
                backend.connect((host, port))
                backend.settimeout(1.0)

                # Přijmi od klienta
                klient_conn.settimeout(0.5)
                try:
                    data = klient_conn.recv(4096)
                except socket.timeout:
                    data = b""

                if data:
                    backend.sendall(data)

                # Vrať odpověď klientovi
                try:
                    odpoved = backend.recv(4096)
                    if odpoved:
                        klient_conn.sendall(odpoved)
                except socket.timeout:
                    pass

                with self._zamek:
                    self.statistiky[klic] += 1

        except ConnectionRefusedError:
            klient_conn.sendall(b"ERROR: Backend nedostupny\n")
        finally:
            klient_conn.close()

    def spust(self, max_spojeni: int = 9):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("localhost", self.lb_port))
            srv.listen(20)
            srv.settimeout(1.5)
            prijato = 0
            while prijato < max_spojeni:
                try:
                    conn, _ = srv.accept()
                    t = threading.Thread(target=self.preposlji,
                                         args=(conn,), daemon=True)
                    t.start()
                    prijato += 1
                except socket.timeout:
                    if prijato > 0:
                        break


# Spusť 3 backend "echo" servery
def mini_backend(port: int, jmeno: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("localhost", port))
        srv.listen(5)
        srv.settimeout(3.0)
        for _ in range(9):
            try:
                conn, _ = srv.accept()
                with conn:
                    conn.settimeout(0.5)
                    try:
                        data = conn.recv(1024)
                        if data:
                            conn.sendall(f"[{jmeno}] {data.decode()!r}".encode())
                    except socket.timeout:
                        pass
            except socket.timeout:
                break

BACKEND_PORTY = [29880, 29881, 29882]
LB_PORT       = 29883

for i, port in enumerate(BACKEND_PORTY):
    bt = threading.Thread(target=mini_backend,
                          args=(port, f"backend_{i+1}"), daemon=True)
    bt.start()

time.sleep(0.15)

lb = LoadBalancer(LB_PORT, [("localhost", p) for p in BACKEND_PORTY])
lt = threading.Thread(target=lb.spust, daemon=True)
lt.start()
time.sleep(0.15)

# Simulace 6 klientů přes load balancer
def lb_klient(cislo: int) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", LB_PORT))
        s.sendall(f"Zpráva {cislo}".encode())
        s.settimeout(1.0)
        try:
            return s.recv(1024).decode()
        except socket.timeout:
            return "(timeout)"

print("  Load balancer round-robin (6 požadavků na 3 backendy):")
for i in range(1, 7):
    odpoved = lb_klient(i)
    print(f"  Klient {i}: {odpoved[:60]}")

time.sleep(0.3)
print("\n  Statistiky:")
for server, pocet in lb.statistiky.items():
    print(f"    {server}: {pocet} požadavků")

print("\n=== Shrnutí ===")
print("  1. RozsirenyChat – /seznam, /opust, /pomoc příkazy")
print("  2. Šifrování – Fernet AES (symetrická, sdílený klíč)")
print("  3. LoadBalancer – round-robin na 3 backendy, statistiky")
