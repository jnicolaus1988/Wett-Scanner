import streamlit as st
import requests

st.set_page_config(page_title="Global Market Scanner", page_icon="🌍", layout="wide")
st.title("🌍 Global Omnisport Scanner")
st.markdown("Scannt dynamisch alle aktuell verfügbaren Sportarten und Hauptmärkte.")

# --- DATEN-FUNKTIONEN ---
@st.cache_data(ttl=3600) # Speichert die Sportarten für 1 Stunde, um API-Anfragen zu sparen
def lade_aktive_sportarten(key):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return [sport['key'] for sport in response.json() if sport['active']]
        return []
    except:
        return []

def hole_live_quoten(sport, maerkte, key):
    maerkte_str = ",".join(maerkte)
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={key}&regions=eu&markets={maerkte_str}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- EINSTELLUNGEN (SIDEBAR) ---
st.sidebar.header("⚙️ System-Konfiguration")
api_key = st.sidebar.text_input("🔑 API Key", type="password")

st.sidebar.markdown("---")
max_quote = st.sidebar.slider("Maximale Quote", 1.15, 1.60, 1.35, 0.01)
min_quote = st.sidebar.slider("Minimale Quote", 1.01, 1.25, 1.15, 0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("Märkte (Je mehr, desto teurer für die API!)")
market_h2h = st.sidebar.checkbox("🏆 Sieger (H2H)", value=True)
market_spread = st.sidebar.checkbox("⚖️ Handicap (Spreads)", value=False)
market_total = st.sidebar.checkbox("⚽ Über/Unter (Totals)", value=False)

aktive_maerkte = []
if market_h2h: aktive_maerkte.append("h2h")
if market_spread: aktive_maerkte.append("spreads")
if market_total: aktive_maerkte.append("totals")

# --- SPORTARTEN AUSWAHL ---
st.sidebar.markdown("---")
st.sidebar.subheader("Aktive Sportarten weltweit")
if api_key:
    alle_sportarten = lade_aktive_sportarten(api_key)
    if alle_sportarten:
        ausgewaehlte_sportarten = st.sidebar.multiselect(
            "Wähle deine Ziel-Märkte für diesen Scan:", 
            alle_sportarten, 
            default=alle_sportarten[:3] # Wählt standardmäßig die ersten 3, um dich zu schützen
        )
    else:
        st.sidebar.error("Konnte Sportarten nicht laden. API-Key prüfen!")
        ausgewaehlte_sportarten = []
else:
    st.sidebar.warning("Trage den API-Key ein, um die Sportarten zu laden.")
    ausgewaehlte_sportarten = []


# --- HAUPT-SCANNER ---
if st.button("🚀 Globalen Cross-Market Scan starten", use_container_width=True):
    if not api_key:
        st.error("Kein API-Key hinterlegt.")
    elif not ausgewaehlte_sportarten:
        st.warning("Bitte wähle mindestens eine Sportart aus dem Menü.")
    elif not aktive_maerkte:
        st.warning("Bitte wähle mindestens einen Wettmarkt aus (z.B. Sieger).")
    else:
        with st.spinner(f"Scanne {len(ausgewaehlte_sportarten)} Sportarten quer durch alle gewählten Märkte..."):
            gefundene_wetten = []
            gesehene_wetten_id = set() 
            
            for sport in ausgewaehlte_sportarten:
                daten = hole_live_quoten(sport, aktive_maerkte, api_key)
                
                for spiel in daten:
                    if 'bookmakers' not in spiel: continue
                    team_a = spiel.get('home_team', 'Unbekannt')
                    team_b = spiel.get('away_team', 'Unbekannt')
                    spiel_name = f"{team_a} vs {team_b}"
                    
                    for buchmacher in spiel['bookmakers']:
                        for markt in buchmacher.get('markets', []):
                            markt_name = markt['key']
                            
                            for quote in markt.get('outcomes', []):
                                if min_quote <= quote['price'] <= max_quote:
                                    
                                    # Erzeuge eine einzigartige ID für diesen genauen Tipp, um Duplikate zu filtern
                                    tipp_beschreibung = f"{quote.get('name', '')} {quote.get('point', '')}".strip()
                                    einzigartige_id = f"{spiel_name}_{markt_name}_{tipp_beschreibung}"
                                    
                                    if einzigartige_id not in gesehene_wetten_id:
                                        gefundene_wetten.append({
                                            "sport": sport,
                                            "spiel": spiel_name,
                                            "markt": markt_name.upper(),
                                            "tipp": tipp_beschreibung,
                                            "quote": quote['price']
                                        })
                                        gesehene_wetten_id.add(einzigartige_id)

            st.success("Omnisport-Scan abgeschlossen!")
            
            # --- ERGEBNIS-TICKET ---
            st.markdown("### 🎫 Dein KI-Cross-Sport-Ticket")
            if len(gefundene_wetten) >= 3:
                # Nach Quote sortieren (sicherste zuerst)
                gefundene_wetten = sorted(gefundene_wetten, key=lambda x: x['quote'])
                top_3 = gefundene_wetten[:3] 
                gesamtquote = 1.0
                
                for i, wette in enumerate(top_3):
                    st.info(f"**Baustein {i+1} ({wette['sport']}) - Markt: {wette['markt']}**\n\n{wette['spiel']}\n\n👉 **Tipp:** {wette['tipp']} | **Quote: {wette['quote']}**")
                    gesamtquote *= wette['quote']
                    
                st.success(f"🔥 **GESAMTQUOTE (KOMBI): {gesamtquote:.2f}**")
            else:
                st.warning("Die Filter waren zu streng. Nicht genügend einmalige Wetten über alle Sportarten gefunden.")
