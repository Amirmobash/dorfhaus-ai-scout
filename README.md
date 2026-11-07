# DorfHaus AI Scout 🏡

**Immobilien intelligent vergleichen – Region zwischen Köln und Düsseldorf.**

Ein quelloffenes, lokal ausführbares Werkzeug zur strukturierten Bewertung von Wohnhäusern in Nordrhein-Westfalen.

**Projekt von Amirmobash.**

## Funktionen
- Kaufnebenkosten in NRW und monatliche Finanzierungsrate berechnen
- Immobilienangebote aus CSV importieren und dauerhaft in SQLite speichern
- Hinweise auf Sanierungsrisiken erkennen und begründet bewerten
- Angebote nach Preis, Wohnfläche und Zustand filtern
- Originalanzeigen direkt öffnen
- Daten lokal halten – keine persönlichen Angaben im Repository

**Wichtig:** Die Schaltfläche „Immobilien jetzt suchen“ liest öffentlich zugängliche Bing-RSS-Suchergebnisse zu Immobilienportalen. Sie durchsucht **nicht** die Immobilienportale selbst. Die Ergebnisse sind unvollständig, möglicherweise veraltet und keine verifizierten Kaufangebote. Es werden keine Zugangsbeschränkungen umgangen.

## Schnellstart
Python 3.11 oder neuer installieren.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Unter Windows alternativ `start.bat` doppelklicken. Der Starter erstellt eine virtuelle Umgebung und installiert die kostenlosen Python-Pakete automatisch. Falls Python fehlt, fragt er vor einer kostenlosen Installation über winget um Erlaubnis. Es wird kein Cloud-Dienst benötigt.

## CSV-Import
Spalten: `titel,preis,wohnflaeche,ort,url,beschreibung,quelle`. Eine Beispieldatei liegt unter `beispiele/angebote.csv`. Alle Beispiele sind fiktiv.

## Qualität
```bash
pip install pytest
pytest -q
```

## Hinweise
Steuersätze und Zinssätze sind veränderbare Modellannahmen, keine verbindlichen Angebote. Immobilien müssen vor einem Kauf unabhängig geprüft werden.

## Datenschutz
Keine Namen von Arbeitgebern, Hochschulen, Bankverbindungen, privaten Adressen oder Zugangsdaten in öffentliche Dateien aufnehmen. Lokale Datenbanken sind von Git ausgeschlossen.

## Roadmap
1. Erlaubte Schnittstellen und Angebotsimporte für Sparkassen-Immobilien priorisieren.
2. Weitere Portale über dokumentierte, zulässige Adapter anbinden.
3. Preisverläufe, Dubletten und Benachrichtigungen ergänzen.
4. Optionales Hosting mit Zugriffsschutz.

## Inspiration
- [Fredy](https://github.com/orangecoding/fredy) – Quellenadapter und Benachrichtigungen
- [wohnung-notifier-bot](https://github.com/alice17/wohnung-notifier-bot) – Mehrquellensuche
- [ImmoScout Python Client](https://github.com/wiestju/immoscout) – strukturierte Immobilienmodelle

Keine Fremdquelltexte übernommen.

Lizenz: MIT. Copyright (c) 2026 Amirmobash.
