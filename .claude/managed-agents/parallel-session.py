"""
Paralelní spuštění více agentů na různých lekcích.

Každý agent dostane jiný úkol (jinou sekci/lekci) a pracuje souběžně.
Výsledky se sbírají po dokončení všech.

Použití:
  pip install anthropic
  AGENT_ID=agent_xxx ENV_ID=env_xxx python3 parallel-session.py
"""

import asyncio
import os
import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

AGENT_ID = os.environ["AGENT_ID"]
ENV_ID   = os.environ["ENV_ID"]
REPO_URL = "https://github.com/navidofek-cmyk/python-interaktivni-kurz"
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ── Úkoly pro paralelní agenty ────────────────────────────────
UKOLY = [
    {
        "nazev": "lekce-84-audio",
        "zprava": (
            "Přidej lekci 84 o zpracování audia v Pythonu. "
            "Použij knihovny wave (stdlib) a pydub (pip install pydub). "
            "Ukaž: čtení/zápis WAV, generování tónu, mix, vizualizace průběhu v textu. "
            "Dodržuj formát lekcí z CLAUDE.md. "
            "Po přidání aktualizuj POSTUP.md a README badge. "
            "Spusť python3 34_generator_webu.py a git push."
        ),
    },
    {
        "nazev": "lekce-85-gui-tkinter",
        "zprava": (
            "Přidej lekci 85 o GUI s tkinter (vestavěný, žádná instalace). "
            "Ukaž: okno, tlačítka, vstupní pole, canvas kreslení, jednoduchý text editor. "
            "Dodržuj formát lekcí z CLAUDE.md. "
            "Po přidání aktualizuj POSTUP.md a README badge. "
            "Spusť python3 34_generator_webu.py a git push."
        ),
    },
    {
        "nazev": "fix-changelog",
        "zprava": (
            "Aktualizuj CHANGELOG.md. "
            "Přidej sekci [0.3.0] s lekcemi 72–83 které přibyly. "
            "Styl: feat/fix/docs bullet pointy, datum 2026-04-27. "
            "git add CHANGELOG.md && git commit && git push."
        ),
    },
]


async def spust_session(ukol: dict) -> dict:
    """Spustí jednu session pro jeden úkol."""
    print(f"  ▶ Spouštím: {ukol['nazev']}")

    session = await client.beta.sessions.create(
        agent={"type": "agent", "id": AGENT_ID},
        environment_id=ENV_ID,
        title=ukol["nazev"],
        resources=[{
            "type": "github_repository",
            "url": REPO_URL,
            "authorization_token": GH_TOKEN,
            "checkout": {"type": "branch", "name": "main"},
        }] if GH_TOKEN else [],
    )

    # Odešli úkol
    await client.beta.sessions.events.send(
        session_id=session.id,
        events=[{
            "type": "user.message",
            "content": [{"type": "text", "text": ukol["zprava"]}],
        }],
    )

    # Streamuj výstup
    vystup_casti = []
    async with client.beta.sessions.stream(session_id=session.id) as stream:
        async for event in stream:
            if event.type == "agent.message":
                for blok in event.content:
                    if blok.type == "text" and blok.text:
                        vystup_casti.append(blok.text)
            elif event.type == "session.status_idle":
                if event.stop_reason.type != "requires_action":
                    break
            elif event.type == "session.status_terminated":
                break

    return {
        "nazev":   ukol["nazev"],
        "session": session.id,
        "vystup":  "".join(vystup_casti)[-500:],   # poslední část výstupu
    }


async def main():
    print(f"Spouštím {len(UKOLY)} paralelních agentů...\n")

    # Spusť všechny souběžně
    vysledky = await asyncio.gather(
        *[spust_session(u) for u in UKOLY],
        return_exceptions=True,
    )

    print("\n" + "="*60)
    print("VÝSLEDKY")
    print("="*60)
    for vysl in vysledky:
        if isinstance(vysl, Exception):
            print(f"\n✗ Chyba: {vysl}")
        else:
            print(f"\n✓ {vysl['nazev']} [{vysl['session']}]")
            print(f"  {vysl['vystup'][:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
