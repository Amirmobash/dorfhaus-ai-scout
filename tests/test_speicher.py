import sqlite3
from dorfhaus.speicher import speichern


def test_wohnungen_lokal_speichern(tmp_path):
    datei = tmp_path / "objekte.sqlite3"
    speichern([{
        "url": "https://example.org/wohnung-1", "titel": "Wohnung Ramrath",
        "preis": 100000, "ort": "Ramrath", "immobilienart": "Wohnung", "hausgeld": 220,
    }], datei)
    with sqlite3.connect(datei) as db:
        assert db.execute("SELECT immobilienart, hausgeld FROM angebote").fetchone() == ("Wohnung", 220)


def test_migration_von_alter_datenbank(tmp_path):
    datei = tmp_path / "alt.sqlite3"
    with sqlite3.connect(datei) as db:
        db.execute("""CREATE TABLE angebote (url TEXT PRIMARY KEY, titel TEXT,
            preis REAL, wohnflaeche REAL, ort TEXT, beschreibung TEXT,
            quelle TEXT, zuletzt_gesehen TEXT DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("INSERT INTO angebote (url, titel) VALUES ('https://example.org/alt', 'Alt')")
    speichern([{"url": "https://example.org/neu", "titel": "Neu", "immobilienart": "Wohnung"}], datei)
    with sqlite3.connect(datei) as db:
        assert db.execute("SELECT COUNT(*) FROM angebote").fetchone()[0] == 2
        assert db.execute("SELECT immobilienart FROM angebote WHERE titel='Neu'").fetchone()[0] == "Wohnung"
