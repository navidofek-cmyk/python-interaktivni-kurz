"""
LEKCE 78: Email a notifikace
==============================
Standardní knihovny: smtplib, imaplib, email
Volitelné: pip install sendgrid slack-sdk

Odesílání emailů, čtení příchozích, Slack notifikace.
Vše co potřebuješ pro automatizované reporty a alerty.
"""

import smtplib
import imaplib
import email
import os
import json
import time
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ODESÍLÁNÍ EMAILU – smtplib
# ══════════════════════════════════════════════════════════════

print("=== Odesílání emailu – smtplib ===\n")

class EmailKlient:
    """Wrapper pro smtplib s podporou HTML, příloh a retry."""

    def __init__(self, host: str, port: int,
                 uzivatel: str, heslo: str):
        self.host     = host
        self.port     = port
        self.uzivatel = uzivatel
        self.heslo    = heslo

    def _pripoj(self) -> smtplib.SMTP_SSL | smtplib.SMTP:
        if self.port == 465:
            return smtplib.SMTP_SSL(self.host, self.port)
        smtp = smtplib.SMTP(self.host, self.port)
        smtp.starttls()    # port 587
        return smtp

    def posli(
        self,
        komu:     str | list[str],
        predmet:  str,
        text:     str,
        html:     str | None = None,
        prilohy:  list[Path] | None = None,
    ) -> bool:
        """Odešle email. Vrátí True pokud úspěch."""
        if isinstance(komu, str):
            komu = [komu]

        msg = MIMEMultipart("alternative") if html else MIMEMultipart()
        msg["From"]    = self.uzivatel
        msg["To"]      = ", ".join(komu)
        msg["Subject"] = predmet
        msg["Date"]    = email.utils.formatdate(localtime=True)

        # Textová část
        msg.attach(MIMEText(text, "plain", "utf-8"))
        if html:
            msg.attach(MIMEText(html, "html", "utf-8"))

        # Přílohy
        for soubor in (prilohy or []):
            if soubor.exists():
                cast = MIMEBase("application", "octet-stream")
                cast.set_payload(soubor.read_bytes())
                encoders.encode_base64(cast)
                cast.add_header("Content-Disposition",
                                 f'attachment; filename="{soubor.name}"')
                msg.attach(cast)

        try:
            with self._pripoj() as smtp:
                smtp.login(self.uzivatel, self.heslo)
                smtp.sendmail(self.uzivatel, komu, msg.as_string())
            return True
        except smtplib.SMTPException as e:
            print(f"  Chyba odesílání: {e}")
            return False

    def posli_html_report(self, komu: str, predmet: str,
                           data: list[dict]) -> bool:
        """Odešle tabulkový report jako HTML email."""
        hlavicky = list(data[0].keys()) if data else []
        radky_html = "".join(
            "<tr>" + "".join(f"<td style='padding:6px;border:1px solid #ddd'>{r.get(h,'')}</td>"
                              for h in hlavicky) + "</tr>"
            for r in data
        )
        html = f"""
        <html><body style="font-family:Arial,sans-serif">
        <h2 style="color:#2E86AB">{predmet}</h2>
        <p>Generováno: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        <table style="border-collapse:collapse;width:100%">
          <tr>{''.join(f'<th style="background:#2E86AB;color:white;padding:8px">{h}</th>' for h in hlavicky)}</tr>
          {radky_html}
        </table>
        </body></html>"""
        text = "\n".join(str(r) for r in data)
        return self.posli(komu, predmet, text, html)

# Konfigurace pro různé poskytovatele
KONFIGURACE = {
    "gmail": {
        "host": "smtp.gmail.com", "port": 587,
        "poznamka": "Potřebuješ App Password (ne heslo účtu): "
                    "Google Account → Security → 2FA → App passwords",
    },
    "outlook": {
        "host": "smtp.office365.com", "port": 587,
        "poznamka": "Funguje s normálním heslem",
    },
    "seznam": {
        "host": "smtp.seznam.cz", "port": 465,
        "poznamka": "SSL na portu 465",
    },
    "sendgrid": {
        "host": "smtp.sendgrid.net", "port": 587,
        "uzivatel": "apikey",
        "poznamka": "Heslo = API klíč ze SendGrid. Ideální pro produkci.",
    },
}

print("Podporované SMTP servery:")
for nazev, cfg in KONFIGURACE.items():
    print(f"  {nazev:<12} {cfg['host']}:{cfg['port']}  – {cfg['poznamka']}")

# Příklad použití (simulace bez odesílání)
print("\nPříklad kódu:")
print("""\
  klient = EmailKlient(
      host="smtp.gmail.com", port=587,
      uzivatel="ja@gmail.com",
      heslo=os.getenv("GMAIL_APP_PASSWORD"),
  )

  # Prostý text
  klient.posli("komu@example.com", "Test", "Ahoj z Pythonu!")

  # HTML email s přílohou
  klient.posli(
      komu="komu@example.com",
      predmet="Týdenní report",
      text="Viz příloha.",
      html="<h1>Report</h1><p>Viz tabulka níže...</p>",
      prilohy=[Path("report.pdf")],
  )

  # HTML tabulkový report
  klient.posli_html_report(
      komu="sef@example.com",
      predmet="Výsledky studentů",
      data=[{"Jméno": "Míša", "Body": 87}, {"Jméno": "Tomáš", "Body": 92}],
  )
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: ČTENÍ EMAILŮ – imaplib
# ══════════════════════════════════════════════════════════════

print("=== Čtení emailů – imaplib ===\n")
print("""\
import imaplib, email

with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
    imap.login("ja@gmail.com", os.getenv("GMAIL_APP_PASSWORD"))
    imap.select("INBOX")

    # Hledej nepřečtené emaily od určitého odesilatele
    _, zpravy = imap.search(None, 'FROM "boss@company.com" UNSEEN')

    for msg_id in zpravy[0].split():
        _, data = imap.fetch(msg_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        predmet = email.header.decode_header(msg["Subject"])[0][0]
        if isinstance(predmet, bytes):
            predmet = predmet.decode()

        print(f"Od: {msg['From']}")
        print(f"Předmět: {predmet}")
        print(f"Datum: {msg['Date']}")

        # Tělo emailu
        if msg.is_multipart():
            for cast in msg.walk():
                if cast.get_content_type() == "text/plain":
                    telo = cast.get_payload(decode=True).decode()
                    print(telo[:200])
        else:
            telo = msg.get_payload(decode=True).decode()
            print(telo[:200])

        # Označ jako přečtený
        imap.store(msg_id, "+FLAGS", "\\\\Seen")
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: SLACK NOTIFIKACE – Incoming Webhooks
# ══════════════════════════════════════════════════════════════

print("=== Slack – Incoming Webhooks ===\n")

def posli_slack(webhook_url: str, zprava: str,
                kanal: str | None = None,
                barva: str = "#2E86AB") -> bool:
    """Odešle zprávu do Slacku přes Incoming Webhook (žádná knihovna)."""
    payload = {
        "text": zprava,
        "attachments": [{
            "color": barva,
            "text":  zprava,
            "ts":    int(time.time()),
        }],
    }
    if kanal:
        payload["channel"] = kanal

    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        webhook_url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read() == b"ok"
    except Exception as e:
        print(f"  Slack chyba: {e}")
        return False

def posli_slack_alert(webhook_url: str, titulek: str,
                       zprava: str, uroven: str = "info") -> bool:
    """Slack alert s barvou podle závažnosti."""
    barvy = {"info": "#36a64f", "warning": "#ffa500", "error": "#ff0000"}
    barva = barvy.get(uroven, "#2E86AB")
    ikony = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}
    ikona = ikony.get(uroven, "📢")
    return posli_slack(webhook_url, f"{ikona} *{titulek}*\n{zprava}", barva=barva)

SLACK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
if SLACK_URL:
    print("Odesílám Slack notifikaci...")
    posli_slack_alert(SLACK_URL, "Deploy hotov", "v2.3.1 nasazen na prod.", "info")
    print("✓ Odesláno")
else:
    print("Nastavení Slacku:")
    print("  1. Slack API → Create App → Incoming Webhooks")
    print("  2. export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'")
    print("\nPříklad volání:")
    print("  posli_slack_alert(url, 'Deploy hotov', 'v2.3.1 na prod', 'info')")
    print("  posli_slack_alert(url, 'Chyba DB',     'Timeout 30s',   'error')")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: AUTOMATIZOVANÝ REPORT – kombinace všeho
# ══════════════════════════════════════════════════════════════

print("\n=== Automatizovaný report (ukázka architektury) ===\n")
print("""\
import schedule   # pip install schedule

def tydeni_report():
    # 1. Načti data z DB
    studenti = db.query("SELECT * FROM studenti")

    # 2. Vygeneruj Excel
    excel_soubor = Path("report_tyden.xlsx")
    generuj_excel(studenti, excel_soubor)

    # 3. Odešli emailem
    klient = EmailKlient(host="smtp.gmail.com", port=587,
                          uzivatel=..., heslo=...)
    klient.posli(
        komu=["sef@skola.cz", "asistent@skola.cz"],
        predmet=f"Týdenní report – {date.today()}",
        text="Viz příloha.",
        prilohy=[excel_soubor],
    )

    # 4. Notifikuj Slack
    posli_slack_alert(SLACK_URL, "Report odeslán",
                       f"{len(studenti)} studentů, {excel_soubor.stat().st_size//1024} KB")

# Spusť každý pátek v 17:00
schedule.every().friday.at("17:00").do(tydeni_report)

while True:
    schedule.run_pending()
    time.sleep(60)
""")

# TVOJE ÚLOHA:
# 1. Napiš skript který pošle email s přiloženým PDF reportem (kombinuj lekci 77).
# 2. Přidej Slack alert do CI/CD pipeline z lekce 75 (na selhání buildu).
# 3. Napiš IMAP monitor který každou minutu kontroluje inbox a reaguje na klíčová slova.
