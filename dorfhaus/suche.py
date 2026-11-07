"""Begrenzte, kostenlose Immobilien-Indexsuche ohne Portal-Scraping.

Bing-RSS kann unvollständig sein. Treffer sind keine verifizierten Angebote.
"""
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse

QUELLEN = {
    "Sparkassen-Immobilien": "sparkassen-immobilien.de",
    "VON POLL IMMOBILIEN": "von-poll.com",
    "ImmobilienScout24": "immobilienscout24.de",
    "immowelt": "immowelt.de",
    "Kleinanzeigen": "kleinanzeigen.de",
    "meinestadt.de": "meinestadt.de",
    "VR-Immobilien": "vr-immobilien.de",
}
# Eine Ortsnennung im Suchtext ist kein amtlicher Standortnachweis.
DORF_REGIONEN = (
    "Ramrath", "Frixheim", "Anstel", "Nettesheim", "Butzheim",
    "Oekoven", "Deelen", "Evinghoven", "Villau", "Ückinghoven",
    "Delrath", "Nievenheim", "Stürzelberg", "Roggendorf", "Worringen",
)
REGIONEN = DORF_REGIONEN
BETRAG = re.compile(
    r"(?<!\d)(\d{2,3}(?:[. ]\d{3})+|\d{5,6})\s*(?:€|EUR|Euro)",
    re.I,
)
BETRAG_VORNE = re.compile(r"€\s*(\d{2,3}(?:[. ]\d{3})+|\d{5,6})", re.I)
HTML = re.compile(r"<[^>]*>")
HAUS = re.compile(r"\b(?:haus|einfamilienhaus|reihenhaus|doppelhaushälfte|bungalow|zweifamilienhaus|wohnhaus)\b", re.I)
WOHNUNG = re.compile(r"\b(?:wohnung|eigentumswohnung|erdgeschosswohnung|dachgeschosswohnung|maisonette|apartment|etw)\b", re.I)
SANIERUNG = (
    "kernsanierungsbedürftig", "sanierungsbedürftig", "renovierungsbedürftig",
    "modernisierungsbedürftig", "handwerkerobjekt", "abriss", "abbruchreif",
    "unbewohnbar", "entkernt", "baulich abgängig", "dach undicht",
    "heizung defekt", "schimmel", "feuchtigkeit",
)
WOHNUNG_HINWEISE = ("sonderumlage", "hausgeld", "instandhaltungsrücklage", "vermietet", "erbpacht")


def preis_aus_text(text):
    """Ungeprüfter Preis aus Überschrift oder Snippet, niemals ein Kaufpreisnachweis."""
    text = text or ""
    fund = BETRAG.search(text) or BETRAG_VORNE.search(text)
    return int(re.sub(r"\D", "", fund.group(1))) if fund else None


def erkenne_art(titel, beschreibung=""):
    for text in (titel, beschreibung):
        if HAUS.search(text or ""):
            return "Haus"
        if WOHNUNG.search(text or ""):
            return "Wohnung"
    return "Unklar"


def ausschlussgruende(text, ohne_fachwerk=True, ohne_sanierung=True):
    """Konservative Textsignale; fehlende Angaben beweisen keinen guten Zustand."""
    text = (text or "").casefold()
    gruende = []
    if ohne_fachwerk and "fachwerk" in text:
        gruende.append("Fachwerk-Hinweis")
    if ohne_sanierung:
        gruende += [wort for wort in SANIERUNG if wort in text]
    return gruende


def ort_passt(text, regionen):
    return bool(_ortstreffer(text or "", regionen))


def _host_erlaubt(url, domain):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == domain or host.endswith("." + domain))


def _ortstreffer(text, regionen):
    return [ort for ort in regionen if re.search(r"(?<!\w)" + re.escape(ort) + r"(?!\w)", text, re.I)]


def parse_rss(xml, quelle, domain, budget, immobilienart="Beides", regionen=None,
              nur_regionen=False, ohne_fachwerk=False, ohne_sanierung=False):
    """RSS-Ergebnisse filtern; fehlende Preise bleiben ausdrücklich ungeprüft."""
    if immobilienart not in ("Haus", "Wohnung", "Beides"):
        raise ValueError("Unbekannte Immobilienart")
    root = ET.fromstring(xml)
    resultate = []
    for item in root.findall(".//item"):
        titel = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        beschreibung = unescape(HTML.sub(" ", item.findtext("description") or "")).strip()
        if not _host_erlaubt(url, domain):
            continue
        art = erkenne_art(titel, beschreibung)
        if immobilienart != "Beides" and art != immobilienart:
            continue
        text = titel + " " + beschreibung
        ortstreffer = _ortstreffer(text, regionen or ())
        if nur_regionen and not ortstreffer:
            continue
        inhalt = text.casefold()
        if ausschlussgruende(text, ohne_fachwerk, ohne_sanierung):
            continue
        sanierung = [wort for wort in SANIERUNG if wort in inhalt]
        preis = preis_aus_text(titel)
        if preis is None:
            preis = preis_aus_text(beschreibung)
        if preis is not None and preis > budget:
            continue
        hinweise = [wort for wort in WOHNUNG_HINWEISE if wort in inhalt] if art == "Wohnung" else []
        resultate.append({
            "titel": titel, "url": url, "quelle": quelle,
            "beschreibung": beschreibung, "preis": preis, "immobilienart": art,
            "ortshinweise": ", ".join(ortstreffer), "sanierungshinweise": sanierung,
            "hinweise": hinweise,
            "status": "Preis unbekannt – nicht als Budgettreffer bestätigt" if preis is None
                      else "Preis aus Suchindex – Originalanzeige prüfen",
        })
    return resultate


def _rss_abrufen(url):
    anfrage = urllib.request.Request(url, headers={"User-Agent": "DorfHausAIScout/0.3 (privater RSS-Reader)"})
    with urllib.request.urlopen(anfrage, timeout=10) as antwort:
        if antwort.status != 200:
            raise OSError("RSS-Dienst nicht erreichbar")
        daten = antwort.read(500_001)
        if len(daten) > 500_000:
            raise ValueError("RSS-Antwort zu groß")
        return daten


def suche(budget=120000, regionen=None, quellen=None, abruf=None, immobilienart="Beides",
          nur_regionen=False, ohne_fachwerk=False, ohne_sanierung=False):
    """Maximal zwei Abfragen je Portal (Haus/Wohnung); keine vollständige Marktsuche."""
    regionen = DORF_REGIONEN[:8] if regionen is None else tuple(regionen)
    quellen = QUELLEN if quellen is None else quellen
    abruf = _rss_abrufen if abruf is None else abruf
    arten = ("Haus", "Wohnung") if immobilienart == "Beides" else (immobilienart,)
    if not regionen and nur_regionen:
        return [], ["Bitte mindestens einen Ort auswählen."]
    ergebnisse, status, gesehen = [], [], set()
    for quelle, domain in quellen.items():
        zaehler = 0
        for art in arten:
            ortsuche = " OR ".join('"' + r.replace('"', '') + '"' for r in regionen[:12])
            wort = '"Haus kaufen"' if art == "Haus" else '"Wohnung kaufen"'
            abfrage = f"site:{domain} {wort} ({ortsuche})" if ortsuche else f"site:{domain} {wort}"
            adresse = "https://www.bing.com/search?" + urllib.parse.urlencode(
                {"q": abfrage, "format": "rss", "setlang": "de"})
            try:
                daten = parse_rss(abruf(adresse), quelle, domain, budget,
                                  immobilienart=art, regionen=regionen,
                                  nur_regionen=nur_regionen, ohne_fachwerk=ohne_fachwerk,
                                  ohne_sanierung=ohne_sanierung)
                for angebot in daten:
                    if angebot["url"] not in gesehen:
                        gesehen.add(angebot["url"])
                        ergebnisse.append(angebot)
                        zaehler += 1
            except Exception as fehler:
                status.append(f"{quelle} ({art}): Suchindex nicht verfügbar ({type(fehler).__name__})")
        status.append(f"{quelle}: {zaehler} potenzielle Treffer")
    return ergebnisse, status
