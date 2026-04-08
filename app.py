import streamlit as st
import requests

st.set_page_config(page_title="Tipico One-Click Scanner", page_icon="🎱", layout="centered")
st.title("🎱 Tipico One-Click Scanner")
st.markdown("Ein Knopfdruck. Die KI scannt automatisch die Top-Märkte – **exklusiv für Tipico**.")

# --- DIE VIP-LISTE ---
VIP_SPORTS = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_germany_bundesliga", 
    "soccer_italy_serie_a", "soccer_spain_la_liga",
    "tennis_atp", "tennis_wta",
    "basketball_nba", "basketball_euroleague",
    "americanfootball_nfl", "icehockey_nhl"
]

# --- EINSTELLUNGEN ---
st.sidebar.header("⚙️ Parameter")
api_key = st.sidebar.text_input("🔑 API Key", type="password")

st.sidebar.markdown("---")
max_quote = st.sidebar.slider("Maximale Quote", 1.15, 1.50, 1.35, 0.01)
min_quote = st.sidebar.slider("Minimale Quote", 1.01, 1.25, 1.15, 0.01)

st.sidebar.markdown("---")
ticket_groesse = st.sidebar.slider("🎟️ Kombi-Größe", 2, 10, 5, 1)

# --- ENGINE ---
def hole_aktive_vip_sports(key):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            used = response.headers.get('x-requests-used', 'Unbekannt')
            remaining = response.headers.get('x-requests-remaining', 'Unbekannt')
            alle_aktiven = [sport['key'] for sport in response.json() if sport['active']]
            return [s for s in VIP_SPORTS if s in alle_aktiven], used, remaining
        return [], 0, 0
    except:
        return [], 0, 0

def scan_sportart(sport, key):
    # API-UPDATE: Wir fordern jetzt explizit nur die Daten von Tipico an (&bookmakers=tipico)
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={key}&regions=eu&bookmakers=tipico&markets=h2h,spreads,totals"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            used = response.headers.get('x-requests-used', 'Unbekannt')
            remaining = response.headers.get('x-requests-remaining', 'Unbekannt')
            return response.json(), used, remaining
        return [], 0, 0
    except:
        return [], 0, 0

# --- DER MAGISCHE KNOPF ---
st.markdown("---")
if st.button("🚀 TIPICO MAGIC SCAN STARTEN", use_container_width=True):
    if not api_key:
        st.error("⚠️ Bitte API-Key links im Menü eintragen!")
    else:
        with st.spinner("Prüfe aktive Märkte und API-Limit..."):
            aktive_vips, letzer_verbrauch, letztes_limit = hole_aktive_vip_sports(api_key)
            
        if not aktive_vips:
            st.warning("Aktuell läuft keiner der globalen Top-Märkte. Versuche es später wieder.")
        else:
            with st.spinner(f"Analysiere Tipico-Quoten für {len(aktive_vips)} Sportarten..."):
                gefundene_wetten = []
                gesehene_wetten_id = set()
                
                for sport in aktive_vips:
                    daten, used, remaining = scan_sportart(sport, api_key)
                    letzer_verbrauch = used 
                    letztes_limit = remaining
                    
                    for spiel in daten:
                        if 'bookmakers' not in spiel: continue
                        team_a = spiel.get('home_team', 'Unbekannt')
                        team_b = spiel.get('away_team', 'Unbekannt')
                        spiel_name = f"{team_a} vs {team_b}"
                        
                        for buchmacher in spiel['bookmakers']:
                            # SICHERHEITSFILTER: Wir lassen im Code wirklich nur Tipico durch
                            if buchmacher.get('key') != 'tipico' and buchmacher.get('title') != 'Tipico':
                                continue
                            
                            for markt in buchmacher.get('markets', []):
                                markt_name = markt['key'].upper() 
                                
                                for quote in markt.get('outcomes', []):
                                    if min_quote <= quote['price'] <= max_quote:
                                        
                                        tipp_text = f"{quote.get('name', '')} {quote.get('point', '')}".strip()
                                        einzigartige_id = f"{spiel_name}_{markt_name}_{tipp_text}"
                                        
                                        if einzigartige_id not in gesehene_wetten_id:
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

                st.success("✅ Exklusive Tipico-Analyse abgeschlossen!")
                
                # --- DAS TICKET ---
                st.markdown(f"### 🎫 Dein Tipico {ticket_groesse}er-Kombi-Ticket")
                if len(gefundene_wetten) >= ticket_groesse:
                    gefundene_wetten = sorted(gefundene_wetten, key=lambda x: x['quote'])
                    top_x = gefundene_wetten[:ticket_groesse]
                    gesamtquote = 1.0
                    
                    for i, wette in enumerate(top_x):
                        st.info(f"**Baustein {i+1} ({wette['sport']}) | {wette['markt']}**\n\n**{wette['spiel']}**\n\n👉 **Tipp:** {wette['tipp']} | **Quote: {wette['quote']}**")
                        gesamtquote *= wette['quote']
                        
                    st.success(f"🔥 **GESAMTQUOTE (KOMBI): {gesamtquote:.2f}**")
                else:
                    st.warning(f"Nicht genügend Spiele gefunden. Bei Tipico gibt es gerade nur {len(gefundene_wetten)} Wetten in deinem eingestellten Quoten-Bereich.")

                # --- DER API-COUNTER ---
                st.markdown("---")
                col1, col2 = st.columns(2)
                col1.metric("Verbrauchte API-Credits", f"{letzer_verbrauch} / 500")
                col2.metric("Verbleibende Credits", letztes_limit)
                st.caption("Dein Guthaben setzt sich am 1. jedes Monats automatisch wieder auf 500 zurück.")
