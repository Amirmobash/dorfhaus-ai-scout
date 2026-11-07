"""Nachvollziehbare Modellrechnung und Risikoanalyse."""
from urllib.parse import urlparse

WARNUNGEN = {
    "kernsanierungsbedürftig": 35,
    "abriss": 45,
    "schimmel": 25,
    "feuchtigkeit": 20,
    "sanierungsbedürftig": 20,
    "heizung defekt": 20,
    "dach undicht": 30,
}
POSITIV = ("modernisiert", "renoviert", "gepflegt", "bezugsfertig")

def kaufnebenkosten(preis: float, makler_prozent: float = 0.0, notar_prozent: float = 2.0) -> dict:
    if preis < 0 or makler_prozent < 0 or notar_prozent < 0:
        raise ValueError("Beträge und Prozentsätze müssen positiv sein.")
    steuer = round(preis * 0.065, 2)
    notar = round(preis * notar_prozent / 100, 2)
    makler = round(preis * makler_prozent / 100, 2)
    return {"Grunderwerbsteuer": steuer, "Notar und Grundbuch": notar, "Makler": makler, "Gesamt": round(preis + steuer + notar + makler, 2)}

def monatsrate(darlehen: float, zins: float = 3.5, tilgung: float = 2.0) -> float:
    if min(darlehen, zins, tilgung) < 0:
        raise ValueError("Negative Werte sind nicht zulässig.")
    return round(darlehen * (zins + tilgung) / 1200, 2)

def risiko(text: str) -> dict:
    inhalt = (text or "").casefold()
    treffer = [wort for wort in WARNUNGEN if wort in inhalt]
    punkte = max(0, 70 - sum(WARNUNGEN[wort] for wort in treffer))
    if not treffer and any(w in inhalt for w in POSITIV):
        punkte = 80
    return {"punkte": punkte, "hinweise": treffer, "unsicher": not bool(inhalt.strip())}

def pruefe_url(url: str) -> bool:
    p = urlparse(url.strip())
    return p.scheme in ("https", "http") and bool(p.netloc)
