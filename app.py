import streamlit as st
import requests

st.set_page_config(page_title="Magic One-Click Scanner", page_icon="🎱", layout="centered")
st.title("🎱 Magic One-Click Scanner")
st.markdown("Ein Knopfdruck. Die KI scannt automatisch die größten globalen Sportmärkte nach deinen Vorgaben.")

# --- DIE VIP-LISTE (Schützt dein API-Limit und garantiert hohe Datenqualität) ---
VIP_SPORTS = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_germany_bundesliga", 
    "soccer_italy_serie_a", "soccer_spain_la_liga",
    "tennis_atp", "tennis_wta",
    "basketball_nba", "basketball_euroleague",
    "americanfootball_nfl", "icehockey_nhl"
]

# --- EINSTELLUNGEN ---
st.sidebar.header("⚙️ Risiko-Parameter")
api_key = st.sidebar.text_input("🔑 API Key", type="password")
st.sidebar.markdown("---")
st.sidebar.markdown("**Dein Sweetspot:**")
max_quote = st.sidebar.slider("Maximale Quote (Risiko-Decke)", 1.15, 1.50, 1.35, 0.01)
min_quote = st.sidebar.slider("Minimale Quote (Mindest-Ertrag)", 1.01, 1.25, 1.15, 0.01)

# --- ENGINE ---
def hole_aktive_vip_sports(key):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            alle_aktiven = [sport['key'] for sport in response.json() if sport['active']]
            # Schnittmenge aus VIP-Liste und aktuell laufenden Sportarten
            return [s for s in VIP_SPORTS if s in alle_aktiven]
        return []
    except:
        return []

def scan_sportart(sport, key):
    # Wir fragen direkt alle drei großen Märkte auf einmal ab!
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={key}&regions=eu&markets=h2h,spreads,totals"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- DER MAGISCHE KNOPF ---
st.markdown("---")
if st.button("🚀 MAGIC SCAN STARTEN", use_container_width=True):
    if not api_key:
        st.error("⚠️ Bitte API-Key links im Menü eintragen!")
    else:
        with st.spinner("Initialisiere globale Satelliten... Suche nach aktiven Top-Märkten..."):
            aktive_vips = hole_aktive_vip_sports(api_key)
            
        if not aktive_vips:
            st.warning("Aktuell läuft keiner der globalen Top-Märkte. Versuche es später wieder.")
        else:
            with st.spinner(f"Analysiere {len(aktive_vips)} aktive Sportarten auf Sieger, Handicaps und Punkte..."):
                gefundene_wetten = []
                gesehene_wetten_id = set()
                
                for sport in aktive_vips:
                    daten = scan_sportart(sport, api_key)
                    
                    for spiel in daten:
                        if 'bookmakers' not in spiel: continue
                        team_a = spiel.get('home_team', 'Unbekannt')
                        team_b = spiel.get('away_team', 'Unbekannt')
                        spiel_name = f"{team_a} vs {team_b}"
                        
                        for buchmacher in spiel['bookmakers']:
                            for markt in buchmacher.get('markets', []):
                                markt_name = markt['key'].upper() # H2H, SPREADS oder TOTALS
                                
                                for quote in markt.get('outcomes', []):
                                    if min_quote <= quote['price'] <= max_quote:
                                        
                                        tipp_text = f"{quote.get('name', '')} {quote.get('point', '')}".strip()
                                        einzigartige_id = f"{spiel_name}_{markt_name}_{tipp_text}"
                                        
                                        if einzigartige_id not in gesehene_wetten_id:
                                            # Übersetze die Märkte für die Anzeige
                                            if markt_name == "H2H": anzeige_markt = "🏆 Sieger"
                                            elif markt_name == "SPREADS": anzeige_markt = "⚖️ Handicap"
                                            elif markt_name == "TOTALS": anzeige_markt = "🎯 Über/Unter"
                                            else: anzeige_markt = markt_name
                                            
                                            gefundene_wetten.append({
                                                "sport": sport.replace('soccer_', '').replace('tennis_', '').replace('basketball_', '').upper(),
                                                "spiel": spiel_name,
                                                "markt": anzeige_markt,
                                                "tipp": tipp_text,
                                                "quote": quote['price']
                                            })
                                            gesehene_wetten_id.add(einzigartige_id)

                st.success("✅ Globale Analyse abgeschlossen!")
                
                # --- DAS TICKET ---
                st.markdown("### 🎫 Dein vollautomatisches Ticket")
                if len(gefundene_wetten) >= 3:
                    # Sortieren nach Quote (niedrigste/sicherste zuerst)
                    gefundene_wetten = sorted(gefundene_wetten, key=lambda x: x['quote'])
                    top_3 = gefundene_wetten[:3]
                    gesamtquote = 1.0
                    
                    for i, wette in enumerate(top_3):
                        st.info(f"**Baustein {i+1} ({wette['sport']}) | {wette['markt']}**\n\n**{wette['spiel']}**\n\n👉 **Tipp:** {wette['tipp']} | **Quote: {wette['quote']}**")
                        gesamtquote *= wette['quote']
                        
                    st.success(f"🔥 **GESAMTQUOTE (KOMBI): {gesamtquote:.2f}**")
                    st.markdown("*Baue diese 3 Bausteine jetzt in deiner Wett-App nach.*")
                else:
                    st.warning("Die Filter waren zu streng. Die Buchmacher geben aktuell keine 3 Spiele in diesem Quoten-Bereich her. Versuche es in ein paar Stunden wieder oder erhöhe die 'Maximale Quote'.")
