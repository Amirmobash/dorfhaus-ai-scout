from dorfhaus.suche import parse_rss, preis_aus_text, suche

RSS = b"""<rss><channel><item><title>Haus 119.000 Euro</title>
<link>https://www.sparkassen-immobilien.de/angebot/123</link>
<description>Gepflegt</description></item>
<item><title>Haus 190.000 Euro</title>
<link>https://www.sparkassen-immobilien.de/angebot/456</link>
<description>Zu teuer</description></item>
<item><title>Fremdseite 90.000 Euro</title>
<link>https://evil.example/haus</link><description>Test</description></item>
</channel></rss>"""

def test_preis():
    assert preis_aus_text("119.000 Euro") == 119000
    assert preis_aus_text("Preis auf Anfrage") is None

def test_filter():
    treffer = parse_rss(RSS, "Sparkasse", "sparkassen-immobilien.de", 130000)
    assert len(treffer) == 1
    assert treffer[0]["preis"] == 119000

def test_abruf():
    treffer, status = suche(quellen={"Sparkasse": "sparkassen-immobilien.de"}, abruf=lambda _: RSS)
    assert len(treffer) == 1
    assert len(status) == 1
