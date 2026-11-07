from urllib.parse import parse_qs, urlparse
from dorfhaus.suche import (ausschlussgruende, erkenne_art, ort_passt,
                             parse_rss, preis_aus_text, suche)

RSS = b"""<rss><channel><item><title>Haus 119.000 Euro</title>
<link>https://www.sparkassen-immobilien.de/angebot/123</link>
<description>Gepflegt</description></item>
<item><title>Haus 190.000 Euro</title>
<link>https://www.sparkassen-immobilien.de/angebot/456</link>
<description>Zu teuer</description></item>
<item><title>Fremdseite 90.000 Euro</title>
<link>https://evil.example/haus</link><description>Test</description></item>
</channel></rss>"""

WOHNUNGEN = b"""<rss><channel>
<item><title>Eigentumswohnung Ramrath 99.000 Euro</title>
<link>https://www.von-poll.com/de/expose/wohnung-1</link>
<description>Gepflegt, Hausgeld 200 Euro</description></item>
<item><title>Haus Ramrath 80.000 Euro</title>
<link>https://www.von-poll.com/de/expose/haus-2</link>
<description>Fachwerk, Kernsanierungsbeduerftig</description></item>
<item><title>Wohnung Frixheim 130.000 Euro</title>
<link>https://www.von-poll.com/de/expose/wohnung-3</link>
<description>Bezugsfertig</description></item>
<item><title>Wohnung Grevenbroich 70.000 Euro</title>
<link>https://www.von-poll.com/de/expose/wohnung-4</link>
<description>Gepflegt</description></item>
<item><title>Haus Ramrath 80.000 Euro</title>
<link>https://von-poll.com.evil.example/de/expose/betrug</link>
<description>Gepflegt</description></item>
</channel></rss>"""


def test_preis():
    assert preis_aus_text("119.000 Euro") == 119000
    assert preis_aus_text("€ 98.500") == 98500
    assert preis_aus_text("Preis auf Anfrage") is None


def test_filter():
    treffer = parse_rss(RSS, "Sparkasse", "sparkassen-immobilien.de", 130000)
    assert len(treffer) == 1
    assert treffer[0]["preis"] == 119000


def test_abruf():
    treffer, status = suche(quellen={"Sparkasse": "sparkassen-immobilien.de"}, abruf=lambda _: RSS)
    assert len(treffer) == 1
    assert len(status) == 1


def test_wohnung_mit_ortsfilter_und_preis():
    treffer = parse_rss(WOHNUNGEN, "VON POLL", "von-poll.com", 120000,
                        immobilienart="Wohnung", regionen=["Ramrath", "Frixheim"],
                        nur_regionen=True, ohne_fachwerk=True, ohne_sanierung=True)
    assert len(treffer) == 1
    assert treffer[0]["immobilienart"] == "Wohnung"
    assert treffer[0]["preis"] == 99000
    assert "hausgeld" in treffer[0]["hinweise"]


def test_fachwerk_hard_filter():
    treffer = parse_rss(WOHNUNGEN, "VON POLL", "von-poll.com", 120000,
                        immobilienart="Haus", regionen=["Ramrath"],
                        nur_regionen=True, ohne_fachwerk=True, ohne_sanierung=True)
    assert treffer == []


def test_suchbegriff_und_deduplizierung():
    angefragt = []
    def abruf(url):
        angefragt.append(parse_qs(urlparse(url).query)["q"][0])
        return WOHNUNGEN
    treffer, status = suche(budget=120000, regionen=["Ramrath", "Frixheim"],
                           quellen={"VON POLL": "von-poll.com"}, abruf=abruf,
                           immobilienart="Beides", nur_regionen=True,
                           ohne_fachwerk=True, ohne_sanierung=True)
    assert len(treffer) == 1
    assert len(angefragt) == 2
    assert any('"Wohnung kaufen"' in s for s in angefragt)
    assert any('"Haus kaufen"' in s for s in angefragt)
    assert all("Ramrath" in s and "Frixheim" in s for s in angefragt)
    assert status[-1] == "VON POLL: 1 potenzielle Treffer"


def test_unknown_price_must_not_claim_budget():
    xml = b"""<rss><channel><item><title>Wohnung Ramrath</title>
<link>https://www.von-poll.com/de/wohnung</link><description>Gepflegt</description></item></channel></rss>"""
    treffer = parse_rss(xml, "VON POLL", "von-poll.com", 120000,
                        immobilienart="Wohnung", regionen=["Ramrath"], nur_regionen=True)
    assert len(treffer) == 1
    assert treffer[0]["preis"] is None
    assert "unbekannt" in treffer[0]["status"]


def test_erkennung_und_ort():
    assert erkenne_art("Maisonette in Ramrath") == "Wohnung"
    assert erkenne_art("Bungalow in Frixheim") == "Haus"
    assert ort_passt("Rommerskirchen-Ramrath", ["Ramrath"])
    assert not ort_passt("Rommerskirchen", ["Ramrath"])
    assert ausschlussgruende("Fachwerkhaus", True, False)
    assert ausschlussgruende("Handwerkerobjekt", False, True)
