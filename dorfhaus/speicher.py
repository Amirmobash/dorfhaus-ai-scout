"""Lokale SQLite-Speicherung; keine Übertragung an externe Dienste."""
import sqlite3
from pathlib import Path

FELDER = ("titel", "preis", "wohnflaeche", "ort", "url", "beschreibung", "quelle")

def speichern(angebote, datei="dorfhaus.sqlite3"):
    verbindung = sqlite3.connect(str(Path(datei)))
    try:
        verbindung.execute("""CREATE TABLE IF NOT EXISTS angebote (
            url TEXT PRIMARY KEY, titel TEXT, preis REAL, wohnflaeche REAL,
            ort TEXT, beschreibung TEXT, quelle TEXT, zuletzt_gesehen TEXT DEFAULT CURRENT_TIMESTAMP)""")
        for a in angebote:
            verbindung.execute("""INSERT INTO angebote (url,titel,preis,wohnflaeche,ort,beschreibung,quelle)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET
                titel=excluded.titel, preis=excluded.preis,
                wohnflaeche=excluded.wohnflaeche, ort=excluded.ort,
                beschreibung=excluded.beschreibung, quelle=excluded.quelle,
                zuletzt_gesehen=CURRENT_TIMESTAMP""",
                (a["url"], a["titel"], a["preis"], a["wohnflaeche"], a["ort"], a["beschreibung"], a["quelle"]))
        verbindung.commit()
    finally:
        verbindung.close()
