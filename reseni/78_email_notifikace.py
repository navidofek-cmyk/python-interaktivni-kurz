"""Řešení – Lekce 78: Email a notifikace"""

import os
import json
import time
import smtplib
import imaplib
import email
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import date, datetime
from typing import Callable


# ── Sdílená třída z lekce 78 ─────────────────────────────────
class EmailKlient:
    def __init__(self, host: str, port: int, uzivatel: str, heslo: str):
        self.host     = host
        self.port     = port
        self.uzivatel = uzivatel
        self.heslo    = heslo

    def _pripoj(self):
        if self.port == 465:
            return smtplib.SMTP_SSL(self.host, self.port)
        smtp = smtplib.SMTP(self.host, self.port)
        smtp.starttls()
        return smtp

    def posli(self, komu, predmet, text, html=None, prilohy=None) -> bool:
        if isinstance(komu, str):
            komu = [komu]
        msg = MIMEMultipart("alternative") if html else MIMEMultipart()
        msg["From"]    = self.uzivatel
        msg["To"]      = ", ".join(komu)
        msg["Subject"] = predmet
        msg["Date"]    = email.utils.formatdate(localtime=True)
        msg.attach(MIMEText(text, "plain", "utf-8"))
        if html:
            msg.attach(MIMEText(html, "html", "utf-8"))
        for soubor in (prilohy or []):
            if Path(soubor).exists():
                cast = MIMEBase("application", "octet-stream")
                cast.set_payload(Path(soubor).read_bytes())
                encoders.encode_base64(cast)
                cast.add_header("Content-Disposition",
                                 f'attachment; filename="{Path(soubor).name}"')
                msg.attach(cast)
        try:
            with self._pripoj() as smtp:
                smtp.login(self.uzivatel, self.heslo)
                smtp.sendmail(self.uzivatel, komu, msg.as_string())
            return True
        except smtplib.SMTPException as e:
            print(f"  Chyba: {e}")
            return False


# 1. Email s PDF reportem (kombinace s lekcí 77)
print("=== 1. Email s PDF přílohou ===\n")

def posli_report_emailem(
    klient: EmailKlient,
    komu: str,
    studenti: list[dict],
    soubor_pdf: str | None = None,
) -> bool:
    """Pošle email s PDF reportem. Pokud soubor_pdf je None, vytvoří ho."""

    # Vygeneruj PDF report (pokud je reportlab dostupný)
    if soubor_pdf is None:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

            soubor_pdf = "tydenni_report.pdf"
            doc = SimpleDocTemplate(soubor_pdf, pagesize=A4,
                                      leftMargin=20*mm, rightMargin=20*mm,
                                      topMargin=20*mm, bottomMargin=20*mm)
            styles = getSampleStyleSheet()
            obsah = [
                Paragraph(f"Týdenní report – {date.today().strftime('%d.%m.%Y')}",
                          styles["Title"]),
                Spacer(1, 10*mm),
            ]
            data = [["Jméno", "Předmět", "Body"]] + \
                   [[s["jmeno"], s["predmet"], str(s["body"])] for s in studenti]
            tbl = Table(data)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2E86AB")),
                ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
                ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            obsah.append(tbl)
            doc.build(obsah)
        except ImportError:
            # Vytvoř dummy soubor pro demo
            soubor_pdf = "tydenni_report_demo.txt"
            with open(soubor_pdf, "w") as f:
                f.write("TÝDENNÍ REPORT\n\n")
                for s in studenti:
                    f.write(f"{s['jmeno']}: {s['body']} bodů\n")

    # HTML tělo emailu
    radky_html = "".join(
        f"<tr><td>{s['jmeno']}</td><td>{s['predmet']}</td>"
        f"<td style='color:{'green' if s['body'] >= 75 else 'red'}'>{s['body']}</td></tr>"
        for s in studenti
    )
    html = f"""
    <html><body style="font-family:Arial">
    <h2 style="color:#2E86AB">Týdenní report – {date.today().strftime('%d.%m.%Y')}</h2>
    <table border="1" style="border-collapse:collapse;width:100%">
      <tr style="background:#2E86AB;color:white">
        <th>Jméno</th><th>Předmět</th><th>Body</th>
      </tr>
      {radky_html}
    </table>
    <p><em>Viz příloha pro PDF verzi.</em></p>
    </body></html>"""

    text = "\n".join(f"{s['jmeno']}: {s['body']} bodů" for s in studenti)

    ok = klient.posli(
        komu=komu,
        predmet=f"Týdenní report – {date.today().strftime('%d.%m.%Y')}",
        text=text,
        html=html,
        prilohy=[soubor_pdf],
    )

    Path(soubor_pdf).unlink(missing_ok=True)
    return ok

STUDENTI = [
    {"jmeno": "Míša",  "predmet": "Python",      "body": 87.5},
    {"jmeno": "Tomáš", "predmet": "Fyzika",       "body": 92.0},
    {"jmeno": "Bára",  "predmet": "Matematika",   "body": 55.3},
]

print("Kód pro odeslání reportu emailem:")
print("""\
  klient = EmailKlient(
      host="smtp.gmail.com", port=587,
      uzivatel="ja@gmail.com",
      heslo=os.getenv("GMAIL_APP_PASSWORD"),
  )
  ok = posli_report_emailem(
      klient, "sef@skola.cz", studenti, soubor_pdf="report.pdf"
  )
""")
print("  (Bez API klíčů – ukázka struktury kódu)")


# 2. Slack alert do CI/CD pipeline
print("\n=== 2. Slack alert pro CI/CD (selhání buildu) ===\n")

import urllib.request

def posli_slack(webhook_url: str, zprava: str, barva: str = "#2E86AB") -> bool:
    payload = {"attachments": [{
        "color": barva,
        "text":  zprava,
        "ts":    int(time.time()),
    }]}
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        webhook_url, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read() in (b"ok", b"OK")
    except Exception as e:
        print(f"  Slack chyba: {e}")
        return False

def ci_notifikace(webhook_url: str, projekt: str, branch: str,
                   status: str, chyby: list[str] | None = None):
    """Odešle Slack notifikaci při výsledku CI/CD pipeline."""
    ikony  = {"success": "✅", "failure": "🔴", "warning": "⚠️"}
    barvy  = {"success": "#36a64f", "failure": "#ff0000", "warning": "#ffa500"}
    ikona  = ikony.get(status, "📢")
    barva  = barvy.get(status, "#2E86AB")

    zprava = f"{ikona} *CI/CD {status.upper()}* – {projekt} ({branch})\n"
    if chyby:
        zprava += "\n".join(f"  • {ch}" for ch in chyby)
    else:
        zprava += "  Vše proběhlo v pořádku."

    zprava += f"\n  Čas: {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    SLACK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    if SLACK_URL:
        return posli_slack(SLACK_URL, zprava, barva)
    else:
        print(f"  [Simulace Slack] {zprava}")
        return True

# Ukázky volání
ci_notifikace("", "python-kurz", "main", "success")
ci_notifikace("", "python-kurz", "feature/login", "failure",
              chyby=["tests/test_auth.py::test_login FAILED",
                     "ERROR: 3 tests failed"])
ci_notifikace("", "python-kurz", "main", "warning",
              chyby=["Coverage dropped below 80%"])


# 3. IMAP monitor – kontroluje inbox a reaguje na klíčová slova
print("\n=== 3. IMAP inbox monitor ===\n")

class InboxMonitor:
    """Monitoruje inbox a reaguje na klíčová slova."""

    def __init__(self, imap_host: str, uzivatel: str, heslo: str,
                 klicova_slova: dict[str, Callable]):
        """
        klicova_slova: slovník {slovo: callback}
        callback: funkce(predmet, odesilatel) -> None
        """
        self.imap_host    = imap_host
        self.uzivatel     = uzivatel
        self.heslo        = heslo
        self.klicova_slova = {k.lower(): v for k, v in klicova_slova.items()}

    def _parsuj_zpravu(self, data: bytes) -> dict:
        msg     = email.message_from_bytes(data)
        predmet = email.header.decode_header(msg.get("Subject", ""))[0][0]
        if isinstance(predmet, bytes):
            predmet = predmet.decode(errors="replace")
        return {
            "od":      msg.get("From", ""),
            "predmet": predmet,
            "datum":   msg.get("Date", ""),
        }

    def zkontroluj_jednou(self) -> list[dict]:
        """Zkontroluje inbox a vrátí seznam zpracovaných zpráv."""
        zpracovane = []
        try:
            with imaplib.IMAP4_SSL(self.imap_host) as imap:
                imap.login(self.uzivatel, self.heslo)
                imap.select("INBOX")

                # Hledej nepřečtené zprávy
                _, zpravy = imap.search(None, "UNSEEN")
                for msg_id in (zpravy[0].split() if zpravy[0] else []):
                    _, data = imap.fetch(msg_id, "(RFC822)")
                    info = self._parsuj_zpravu(data[0][1])

                    # Zkontroluj klíčová slova v předmětu
                    for slovo, callback in self.klicova_slova.items():
                        if slovo in info["predmet"].lower():
                            print(f"  Nalezeno klíčové slovo '{slovo}' v: {info['predmet']}")
                            callback(info["predmet"], info["od"])
                            zpracovane.append(info)
                            break

                    # Označ jako přečtené
                    imap.store(msg_id, "+FLAGS", "\\Seen")
        except Exception as e:
            print(f"  IMAP chyba: {e}")
        return zpracovane

    def spust_monitor(self, interval_sekund: int = 60, max_iteraci: int = 3):
        """Spustí monitor v cyklu."""
        print(f"  Monitor spuštěn (interval {interval_sekund}s, max {max_iteraci}×)")
        for i in range(max_iteraci):
            print(f"  Kontrola {i+1}/{max_iteraci}...")
            zpracovane = self.zkontroluj_jednou()
            print(f"    Zpracováno zpráv: {len(zpracovane)}")
            if i < max_iteraci - 1:
                time.sleep(interval_sekund)


# Příklad použití (bez reálných credentials)
def on_alert(predmet: str, odesilatel: str):
    print(f"    ALERT: {predmet} od {odesilatel}")
    ci_notifikace("", "monitor", "prod", "warning",
                  chyby=[f"Email alert: {predmet}"])

def on_objednavka(predmet: str, odesilatel: str):
    print(f"    OBJEDNAVKA: {predmet} od {odesilatel}")

monitor = InboxMonitor(
    imap_host="imap.gmail.com",
    uzivatel=os.getenv("GMAIL_USER", ""),
    heslo=os.getenv("GMAIL_APP_PASSWORD", ""),
    klicova_slova={
        "alert":      on_alert,
        "chyba":      on_alert,
        "objednavka": on_objednavka,
        "error":      on_alert,
    }
)

print("InboxMonitor konfigurován:")
print(f"  Klíčová slova: {list(monitor.klicova_slova.keys())}")
print()
print("  Spuštění:")
print("    monitor.spust_monitor(interval_sekund=60)")
print()
print("  Nastav env proměnné:")
print("    export GMAIL_USER='ja@gmail.com'")
print("    export GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx'")
print("    (App Password: Google Account → Bezpečnost → 2FA → Hesla aplikací)")
