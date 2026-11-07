"""Lokale SQLite-Speicherung mit Schema-Migration für Wohnungen."""
import sqlite3
from pathlib import Path

FELDER = ("titel", "preis", "wohnflaeche", "ort", "url", "beschreibung", "quelle", "immobilienart", "hausgeld")


def speichern(angebote, datei="dorfhaus.sqlite3"):
    verbindung = sqlite3.connect(str(Path(datei)))
    try:
        verbindung.execute("""CREATE TABLE IF NOT EXISTS angebote (
            url TEXT PRIMARY KEY, titel TEXT, preis REAL, wohnflaeche REAL,
            ort TEXT, beschreibung TEXT, quelle TEXT,
            zuletzt_gesehen TEXT DEFAULT CURRENT_TIMESTAMP,
            immobilienart TEXT DEFAULT 'Unklar', hausgeld REAL)""")
        spalten = {zeile[1] for zeile in verbindung.execute("PRAGMA table_info(angebote)")}
        if "immobilienart" not in spalten:
            verbindung.execute("ALTER TABLE angebote ADD COLUMN immobilienart TEXT DEFAULT 'Unklar'")
        if "hausgeld" not in spalten:
            verbindung.execute("ALTER TABLE angebote ADD COLUMN hausgeld REAL")
        for angebot in angebote:
            verbindung.execute("""INSERT INTO angebote
                (url, titel, preis, wohnflaeche, ort, beschreibung, quelle, immobilienart, hausgeld)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                titel=excluded.titel, preis=excluded.preis,
                wohnflaeche=excluded.wohnflaeche, ort=excluded.ort,
                beschreibung=excluded.beschreibung, quelle=excluded.quelle,
                immobilienart=excluded.immobilienart, hausgeld=excluded.hausgeld,
                zuletzt_gesehen=CURRENT_TIMESTAMP""", (
                    angebot["url"], angebot.get("titel", ""), angebot.get("preis"),
                    angebot.get("wohnflaeche"), angebot.get("ort") or angebot.get("ortshinweise", ""),
                    angebot.get("beschreibung", ""), angebot.get("quelle", ""),
                    angebot.get("immobilienart", "Unklar"), angebot.get("hausgeld"),
                ))
        verbindung.commit()
    finally:
        verbindung.close()
