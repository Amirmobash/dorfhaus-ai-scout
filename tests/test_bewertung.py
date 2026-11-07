from dorfhaus.bewertung import kaufnebenkosten, monatsrate, risiko, pruefe_url

def test_kaufnebenkosten():
    assert kaufnebenkosten(120000, 3.57)["Gesamt"] == 134484

def test_monatsrate():
    assert monatsrate(100000, 3.5, 2) == 458.33

def test_risiko():
    assert risiko("Schimmel und Feuchtigkeit")["punkte"] < risiko("Gepflegt")["punkte"]

def test_url():
    assert pruefe_url("https://example.com/haus")
    assert not pruefe_url("javascript:alert(1)")
