"""Kostenlose, begrenzte Suche über öffentlich bereitgestellte RSS-Suchergebnisse.

Keine direkte Abfrage der Immobilienportale und kein Umgehen von Zugangssperren.
Die Suchmaschine kann Ergebnisse auslassen; Preis und Zustand bleiben ungeprüft.
"""
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse

QUELLEN = {
    "Sparkassen-Immobilien": "sparkassen-immobilien.de",
    "ImmobilienScout24": "immobilienscout24.de",
    "immowelt": "immowelt.de",
    "Kleinanzeigen": "kleinanzeigen.de",
    "meinestadt.de": "meinestadt.de",
    "VR-Immobilien": "vr-immobilien.de",
}
REGIONEN = ("Mönchengladbach", "Neuss", "Grevenbroich", "Dormagen", "Erkelenz", "Krefeld")
BETRAG = re.compile(r"(?<!\d)(\d{2,3}(?:[. ]\d{3})+|\d{5,6})\s*(?:€|EUR|Euro)", re.I)
HTML = re.compile(r"<[^>]*>")

def preis_aus_text(text):
    fund = BETRAG.search(text or "")
    return int(re.sub(r"\D", "", fund.group(1))) if fund else None

def _host_erlaubt(url, domain):
    host = (urlparse(url).hostname or "").lower()
    return urlparse(url).scheme == "https" and (host == domain or host.endswith("." + domain))

def parse_rss(xml, quelle, domain, budget):
    root = ET.fromstring(xml)
    resultate = []
    for item in root.findall(".//item"):
        titel = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        text = unescape(HTML.sub(" ", item.findtext("description") or "")).strip()
        if not _host_erlaubt(url, domain):
            continue
        preis = preis_aus_text(titel + " " + text)
        if preis is not None and preis > budget:
            continue
        resultate.append({"titel": titel, "url": url, "quelle": quelle,
                          "beschreibung": text, "preis": preis,
                          "status": "Preis nicht bestätigt" if preis is None else "Preis aus Suchtext – prüfen"})
    return resultate

def suche(budget=130000, regionen=None, quellen=None, abruf=None):
    """Maximal sechs Suchanfragen pro Lauf; Statusmeldungen bei Fehlern."""
    regionen = regionen or REGIONEN
    quellen = quellen or QUELLEN
    abruf = abruf or _rss_abrufen
    ergebnisse, status, gesehen = [], [], set()
    for quelle, domain in quellen.items():
        region = " OR ".join('"' + r + '"' for r in regionen[:3])
        abfrage = f"site:{domain} Haus kaufen ({region})"
        adresse = "https://www.bing.com/search?" + urllib.parse.urlencode(
            {"q": abfrage, "format": "rss", "setlang": "de"})
        try:
            daten = parse_rss(abruf(adresse), quelle, domain, budget)
            neu = 0
            for angebot in daten:
                if angebot["url"] not in gesehen:
                    gesehen.add(angebot["url"])
                    ergebnisse.append(angebot)
                    neu += 1
            status.append(f"{quelle}: {neu} mögliche Treffer aus dem Suchindex")
        except Exception as fehler:
            status.append(f"{quelle}: nicht verfügbar ({type(fehler).__name__})")
    return ergebnisse, status

def _rss_abrufen(url):
    anfrage = urllib.request.Request(url, headers={"User-Agent": "DorfHausAIScout/0.2 (privater RSS-Reader)"})
    with urllib.request.urlopen(anfrage, timeout=12) as antwort:
        if antwort.status != 200:
            raise OSError("RSS-Dienst nicht erreichbar")
        daten = antwort.read(500_001)
        if len(daten) > 500_000:
            raise ValueError("RSS-Antwort zu groß")
        return daten
