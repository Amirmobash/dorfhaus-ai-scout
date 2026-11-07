"""Lokales Dashboard für Häuser und Eigentumswohnungen."""
import pandas as pd
import streamlit as st

from dorfhaus.bewertung import kaufnebenkosten, monatsrate, risiko, pruefe_url
from dorfhaus.speicher import speichern
from dorfhaus.suche import (DORF_REGIONEN, QUELLEN, ausschlussgruende,
                             erkenne_art, ort_passt, suche)

st.set_page_config(page_title="DorfHaus & Wohnungs-Scout", page_icon="🏡", layout="wide")
st.title("🏡 DorfHaus & Wohnungs-Scout")
st.caption("Häuser und Eigentumswohnungen zwischen Köln und Düsseldorf · Amirmobash")
st.info("Kostenlose Indexsuche – keine vollständige Live-Suche in Immobilienportalen. Preis, Ort, Zustand und tatsächliche Fahrzeit immer selbst verifizieren.")

st.sidebar.header("Suchprofil")
immobilienart = st.sidebar.radio("Immobilienart", ("Beides", "Haus", "Wohnung"), horizontal=True)
budget = st.sidebar.number_input("Maximaler Kaufpreis (€)", min_value=10000, value=120000, step=5000)
flaeche = st.sidebar.number_input("Mindestwohnfläche für CSV (m²)", min_value=0, value=0)
regionen = st.sidebar.multiselect(
    "Dörfer / Ortsteile im Suchkorridor", DORF_REGIONEN,
    default=list(DORF_REGIONEN[:8]),
    help="Eine Ortsnennung im Suchtext bestätigt nicht die tatsächliche Lage. Fahrzeiten bis 40 Minuten werden nicht automatisch geprüft.",
)
nur_doerfer = st.sidebar.checkbox("Nur Treffer mit Ortsnennung", value=True,
                                    help="Strenger Textfilter; kann passende Anzeigen ohne konkrete Ortsnennung ausblenden.")
ohne_fachwerk = st.sidebar.checkbox("Fachwerk-Hinweise ausschließen", value=True)
ohne_sanierung = st.sidebar.checkbox("Deutliche Sanierungshinweise ausschließen", value=True)
st.sidebar.caption("Auch ohne Warnwörter kann eine Immobilie sanierungsbedürftig sein. Für Wohnungen Hausgeld, Rücklagen, Teilungserklärung und Sonderumlagen prüfen.")

st.sidebar.header("Kostenmodell (NRW)")
makler = st.sidebar.number_input("Maklerprovision (%)", min_value=0.0, value=3.57, step=0.1)
zins = st.sidebar.number_input("Sollzins (%)", min_value=0.0, value=3.5, step=0.25)
tilgung = st.sidebar.number_input("Anfängliche Tilgung (%)", min_value=0.0, value=2.0, step=0.25)
eigenkapital = st.sidebar.number_input("Eigenkapital (€)", min_value=0, value=0, step=5000)

st.subheader("Öffentliche Suchindex-Treffer")
st.caption("Öffentliche Bing-RSS-Ergebnisse mit Links zu Immobilienportalen, kein Scraping der Portale. Unvollständig und möglicherweise veraltet. Eine Überschrift ist kein Nachweis für Kaufpreis, Bausubstanz oder Verfügbarkeit.")
st.write("Quellen: " + ", ".join(QUELLEN.keys()))
parameter = (immobilienart, int(budget), tuple(regionen), nur_doerfer, ohne_fachwerk, ohne_sanierung)
if st.button("🔎 Immobilien jetzt suchen", type="primary"):
    with st.spinner("Öffentliche Suchindex-Treffer werden abgerufen ..."):
        st.session_state["suchergebnis"] = suche(
            budget=budget, immobilienart=immobilienart, regionen=regionen,
            nur_regionen=nur_doerfer, ohne_fachwerk=ohne_fachwerk,
            ohne_sanierung=ohne_sanierung,
        )
        st.session_state["suchparameter"] = parameter

if "suchergebnis" in st.session_state:
    if st.session_state.get("suchparameter") != parameter:
        st.info("Suchprofil wurde geändert. Bitte die Suche erneut starten.")
    else:
        treffer, meldungen = st.session_state["suchergebnis"]
        with st.expander("Abfrageprotokoll", expanded=not bool(treffer)):
            for meldung in meldungen:
                st.write(meldung)
        if treffer:
            bekannte = sum(a["preis"] is not None for a in treffer)
            st.write(f"{bekannte} potenzielle Treffer mit Preisangabe im Suchindex; "
                     f"{len(treffer) - bekannte} mit unbekanntem Preis. Nichts davon ist bestätigt.")
            for angebot in sorted(treffer, key=lambda a: (
                    a["quelle"] != "Sparkassen-Immobilien",
                    a["preis"] is None, a["preis"] or 0)):
                with st.container(border=True):
                    st.write(angebot["titel"])
                    st.caption(f"{angebot['quelle']} · {angebot['immobilienart']} · "
                               f"Ortsnennung: {angebot['ortshinweise'] or 'nicht bestätigt'}")
                    st.write(angebot["status"])
                    if angebot["preis"] is not None:
                        st.write(f"Preis laut Suchindex: {angebot['preis']:,.0f} €")
                    if angebot["beschreibung"]:
                        st.write(angebot["beschreibung"][:500])
                    if angebot["hinweise"]:
                        st.warning("Zusätzlich prüfen: " + ", ".join(angebot["hinweise"]))
                    st.link_button("Originalanzeige prüfen", angebot["url"])
            st.download_button("Suchergebnis als CSV speichern",
                               pd.DataFrame(treffer).to_csv(index=False).encode("utf-8-sig"),
                               "suchindex-treffer.csv", "text/csv")
            if st.button("Suchindex-Treffer lokal merken"):
                speichern(treffer)
                st.success("Treffer in der lokalen Datenbank gespeichert.")
        else:
            st.warning("Keine passenden Index-Treffer. Das beweist nicht, dass keine passenden Immobilien angeboten werden.")

st.divider()
st.subheader("Eigene Angebote als CSV prüfen")
st.caption("Pflichtfelder: titel, preis, wohnflaeche, ort, url, beschreibung, quelle. Optional: immobilienart (Haus/Wohnung), hausgeld (€/Monat).")
datei = st.file_uploader("Angebote importieren", type=["csv"])
if datei is None:
    st.caption("Eine vollständig fiktive Testdatei liegt unter beispiele/angebote.csv.")
else:
    try:
        daten = pd.read_csv(datei, dtype={"url": str}).fillna("")
        benoetigt = {"titel", "preis", "wohnflaeche", "ort", "url", "beschreibung", "quelle"}
        if not benoetigt.issubset(daten.columns):
            st.error("Fehlende CSV-Spalten: " + ", ".join(sorted(benoetigt - set(daten.columns))))
            st.stop()
        if "immobilienart" not in daten.columns:
            daten["immobilienart"] = ""
        if "hausgeld" not in daten.columns:
            daten["hausgeld"] = ""
        for feld in ("preis", "wohnflaeche", "hausgeld"):
            daten[feld] = pd.to_numeric(daten[feld], errors="coerce")
        daten = daten.dropna(subset=["preis", "wohnflaeche"])
        daten = daten[(daten.preis >= 0) & (daten.wohnflaeche >= 0)]
        daten = daten[daten.url.map(pruefe_url)].drop_duplicates("url").copy()
        daten["immobilienart"] = daten.apply(
            lambda z: z["immobilienart"] if z["immobilienart"] in ("Haus", "Wohnung")
            else erkenne_art(str(z["titel"]), str(z["beschreibung"])), axis=1)
        if immobilienart != "Beides":
            daten = daten[daten["immobilienart"] == immobilienart]
        if nur_doerfer:
            daten = daten[daten.ort.map(lambda s: ort_passt(str(s), regionen))]
        daten = daten[(daten.preis <= budget) & (daten.wohnflaeche >= flaeche)].copy()
        daten = daten[~daten.apply(lambda z: bool(ausschlussgruende(
            str(z["titel"]) + " " + str(z["beschreibung"]),
            ohne_fachwerk, ohne_sanierung)), axis=1)].copy()
        daten["Bewertungspunkte"] = daten.beschreibung.map(lambda x: risiko(str(x))["punkte"])
        daten["Gesamtkosten (€)"] = daten.preis.map(lambda x: kaufnebenkosten(x, makler)["Gesamt"])
        daten["Monatsrate (€)"] = daten["Gesamtkosten (€)"].map(
            lambda x: monatsrate(max(0, x - eigenkapital), zins, tilgung))
        daten = daten.sort_values(["Bewertungspunkte", "preis"], ascending=[False, True])
        st.metric("CSV-Treffer nach Textfiltern", len(daten))
        st.dataframe(daten[["titel", "immobilienart", "preis", "wohnflaeche", "hausgeld", "ort",
                            "quelle", "Bewertungspunkte", "Gesamtkosten (€)", "Monatsrate (€)", "url"]],
                     hide_index=True, use_container_width=True,
                     column_config={"url": st.column_config.LinkColumn("Originalanzeige")})
        if st.button("CSV-Treffer lokal speichern"):
            speichern(daten.to_dict("records"))
            st.success("Angebote lokal gespeichert.")
        st.download_button("CSV-Auswertung herunterladen", daten.to_csv(index=False).encode("utf-8-sig"),
                           "immobilienbewertung.csv", "text/csv")
        st.caption("Bewertungspunkte sind reine Textheuristiken, keine Bauprüfung. Finanzierungsmodell ohne laufendes Hausgeld.")
    except Exception as fehler:
        st.error(f"CSV konnte nicht verarbeitet werden: {fehler}")
