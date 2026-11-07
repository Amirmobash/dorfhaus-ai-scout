"""Lokales Dashboard für Immobilienangebote."""
import pandas as pd
import streamlit as st
from dorfhaus.bewertung import kaufnebenkosten, monatsrate, risiko, pruefe_url
from dorfhaus.speicher import speichern
from dorfhaus.suche import suche

st.set_page_config(page_title="DorfHaus AI Scout", page_icon="🏡", layout="wide")
st.title("🏡 DorfHaus AI Scout")
st.caption("Immobilienbewertung in der Region zwischen Köln und Düsseldorf · Amirmobash")
st.info("MVP: CSV-Import und Modellbewertung. Keine Live-Abfrage von Immobilienportalen.")
budget = st.sidebar.number_input("Maximaler Kaufpreis (€)", min_value=10000, value=130000, step=5000)
flaeche = st.sidebar.number_input("Mindestwohnfläche (m²)", min_value=0, value=70)
makler = st.sidebar.number_input("Maklerprovision (%)", min_value=0.0, value=3.57, step=0.1)
zins = st.sidebar.number_input("Sollzins (%)", min_value=0.0, value=3.5, step=0.25)
tilgung = st.sidebar.number_input("Anfängliche Tilgung (%)", min_value=0.0, value=2.0, step=0.25)
eigenkapital = st.sidebar.number_input("Eigenkapital (€)", min_value=0, value=0, step=5000)
st.subheader("Öffentliche Immobilien-Suchergebnisse")
st.caption("Kostenlose, begrenzte RSS-Indexsuche; keine Direktabfrage von Immobilienportalen. Treffer können fehlen oder veraltet sein. Preise und Wohnzustand müssen auf der Originalseite geprüft werden.")
if st.button("🔎 Immobilien jetzt suchen", type="primary"):
    with st.spinner("Öffentliche Suchergebnisse werden abgefragt ..."):
        treffer, meldungen = suche(budget=budget)
    for meldung in meldungen:
        st.write(meldung)
    if treffer:
        st.success(f"{len(treffer)} mögliche Treffer – keine bestätigten Angebote")
        for haus in sorted(treffer, key=lambda x: (x["quelle"] != "Sparkassen-Immobilien", x["preis"] is None, x["preis"] or 0)):
            with st.container(border=True):
                st.markdown(f"**{haus['titel']}**")
                st.write(f"{haus['quelle']} · {haus['status']}")
                st.write(f"Preis laut Suchindex: {haus['preis']:,} €" if haus["preis"] is not None else "Preis unbekannt – manuell prüfen")
                st.write(haus["beschreibung"][:500])
                st.link_button("Originalanzeige prüfen", haus["url"])
    else:
        st.warning("Keine Treffer aus dem öffentlichen Suchindex. Das bedeutet nicht, dass keine passenden Immobilien existieren.")
st.divider()
st.subheader("Eigene Anzeigen importieren")
datei = st.file_uploader("Immobilienangebote als CSV importieren", type=["csv"])
if datei is None:
    st.warning("Bitte CSV-Datei hochladen. Unter beispiele/angebote.csv liegt eine fiktive Testdatei.")
else:
    try:
        daten = pd.read_csv(datei, dtype={"url": str}).fillna("")
        benoetigt = {"titel", "preis", "wohnflaeche", "ort", "url", "beschreibung", "quelle"}
        if not benoetigt.issubset(daten.columns):
            st.error("Fehlende CSV-Spalten: " + ", ".join(sorted(benoetigt - set(daten.columns))))
            st.stop()
        for feld in ("preis", "wohnflaeche"):
            daten[feld] = pd.to_numeric(daten[feld], errors="coerce")
        daten = daten.dropna(subset=["preis", "wohnflaeche"])
        daten = daten[(daten.preis >= 0) & (daten.wohnflaeche >= 0)]
        daten = daten[daten.url.map(pruefe_url)].drop_duplicates("url")
        daten = daten[(daten.preis <= budget) & (daten.wohnflaeche >= flaeche)].copy()
        daten["Risikopunkte"] = daten.beschreibung.map(lambda x: risiko(str(x))["punkte"])
        daten["Gesamtkosten (€)"] = daten.preis.map(lambda x: kaufnebenkosten(x, makler)["Gesamt"])
        daten["Monatsrate (€)"] = daten["Gesamtkosten (€)"].map(lambda x: monatsrate(max(0, x - eigenkapital), zins, tilgung))
        daten = daten.sort_values(["Risikopunkte", "preis"], ascending=[False, True])
        st.metric("Passende Angebote", len(daten))
        st.dataframe(daten[["titel", "preis", "wohnflaeche", "ort", "quelle", "Risikopunkte", "Gesamtkosten (€)", "Monatsrate (€)", "url"]], hide_index=True, use_container_width=True,
                     column_config={"url": st.column_config.LinkColumn("Originalanzeige")})
        if st.button("Ergebnisse lokal speichern"):
            speichern(daten.to_dict("records"))
            st.success("Angebote lokal gespeichert.")
        st.download_button("Ergebnis als CSV herunterladen", daten.to_csv(index=False).encode("utf-8-sig"), "immobilienbewertung.csv", "text/csv")
        st.caption("Risikopunkte sind Textheuristiken, keine Bausubstanzprüfung. Beispielanzeigen sind fiktiv.")
    except Exception as fehler:
        st.error(f"CSV konnte nicht verarbeitet werden: {fehler}")
