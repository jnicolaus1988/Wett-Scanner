import streamlit as st
import requests

st.set_page_config(page_title="KI Pro-Scanner", page_icon="🎱", layout="centered")
st.title("🎱 KI Pro-Scanner (Top Bookies)")
st.markdown("Dein vollautomatisches System für Kombiwetten. Regionen: EU & UK.")

# --- DAS GEDÄCHTNIS ---
if 'api_used' not in st.session_state:
    st.session_state.api_used = "?"
if 'api_remaining' not in st.session_state:
    st.session_state.api_remaining = "?"

VIP_SPORTS = [
    "soccer_uefa_champs_league", "soccer_epl", "soccer_germany_bundesliga", 
    "soccer_italy_serie_a", "soccer_spain_la_liga",
    "tennis_atp", "tennis_wta",
    "basketball_nba", "basketball_euroleague",
    "americanfootball_nfl", "icehockey_nhl"
]

# --- EINSTELLUNGEN ---
st.sidebar.header("⚙️ Ticket-Parameter")
api_key = st.sidebar.text_input("🔑 API Key", type="password")

st.sidebar.markdown("---")
# NEU: "Alle" hinzugefügt für den Transparenz-Test
buchmacher = st.sidebar.radio(
    "🏦 Ziel-Buchmacher:",
    ("bet365", "bwin", "unibet", "alle"),
    format_func=lambda x: {"bet365": "1. Bet365 (Primär)", "bwin": "2. Bwin (Backup)", "unibet": "3. Unibet (Spezialist)", "alle": "🌍 Globaler Mix (Alle ansehen)"}[x]
)

st.sidebar.markdown("---")
max_quote = st.sidebar.slider("Maximale Quote", 1.15, 1.50, 1.35, 0.01)
min_quote = st.sidebar.slider("Minimale Quote", 1.01, 1.25, 1.15, 0.01)
ticket_groesse = st.sidebar.slider("🎟️ Wunsch-Kombi-Größe", 2, 10, 5, 1)

# --- CREDIT COUNTER ---
st.sidebar.markdown("---")
st.sidebar.subheader("API Guthaben (Letzter Stand)")
col1, col2 = st.sidebar.columns(2)
col1.metric("Verbraucht", f"{st.session_state.api_used} / 500")
col2.metric("Übrig", st.session_state.api_remaining)

# --- ENGINE ---
def hole_aktive_vip_sports(key):
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            st.session_state.api_used = response.headers.get('x-requests-used', st.session_state.api_used)
            st.session_state.api_remaining = response.headers.get('x-requests-remaining', st.session_state.api_remaining)
            alle_aktiven = [sport['key'] for sport in response.json() if sport['active']]
            return [s for s in VIP_SPORTS if s in alle_aktiven]
        return []
    except:
        return []

def scan_sportart(sport, key, bookie):
    # FIX: Regionen auf eu UND uk gesetzt!
    if bookie == "alle":
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={key}&regions=eu,uk&markets=h2h,spreads,totals"
    else:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={key}&regions=eu,uk&bookmakers={bookie}&markets=h2h,spreads,totals"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            st.session_state.api_used = response.headers.get('x-requests-used', st.session_state.api_used)
            st.session_state.api_remaining = response.headers.get('x-requests-remaining', st.session_state.api_remaining)
            return response.json()
        return []
    except:
        return []

# --- DER MAGISCHE KNOPF ---
st.markdown("---")
if st.button(f"🚀 SCAN STARTEN", use_container_width=True):
    if not api_key:
        st.error("⚠️ Bitte API-Key links im Menü eintragen!")
    else:
        with st.spinner("Prüfe aktive Märkte..."):
            aktive_vips = hole_aktive_vip_sports(api_key)
            
        if not aktive_vips:
            st.warning("Aktuell läuft keiner der globalen Top-Märkte. Versuche es später wieder.")
        else:
            with st.spinner(f"Analysiere Quoten für {len(aktive_vips)} Sportarten..."):
                gefundene_wetten = []
                gesehene_wetten_id = set()
                
                for sport in aktive_vips:
                    daten = scan_sportart(sport, api_key, buchmacher)
                    
                    for spiel in daten:
                        if 'bookmakers' not in spiel: continue
                        team_a = spiel.get('home_team', 'Unbekannt')
                        team_b = spiel.get('away_team', 'Unbekannt')
                        spiel_name = f"{team_a} vs {team_b}"
                        
                        for bm in spiel['bookmakers']:
                            # Überspringen, wenn wir einen bestimmten Bookie wollen, aber das der falsche ist
                            if buchmacher != "alle" and bm.get('key') != buchmacher:
                                continue
                                
                            buchmacher_name = bm.get('title', 'Unbekannt')
                            
                            for markt in bm.get('markets', []):
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
                                                "quote": quote['price'],
                                                "bookie_name": buchmacher_name
                                            })
                                            gesehene_wetten_id.add(einzigartige_id)

                st.success("✅ Analyse abgeschlossen!")
                
                # --- DAS TICKET (NEUE LOGIK) ---
                if len(gefundene_wetten) > 0:
                    gefundene_wetten = sorted(gefundene_wetten, key=lambda x: x['quote'])
                    top_x = gefundene_wetten[:ticket_groesse]
                    gesamtquote = 1.0
                    
                    st.markdown(f"### 🎫 Dein Ticket ({len(top_x)} Bausteine)")
                    
                    # FIX: Wenn weniger gefunden wurden, als gewünscht
                    if len(gefundene_wetten) < ticket_groesse:
                        st.warning(f"Achtung: Du wolltest {ticket_groesse} Spiele, aber der Markt gibt bei deinen strengen Vorgaben gerade nur {len(gefundene_wetten)} her. Hier ist das Maximum, das wir herausholen konnten:")
                    
                    for i, wette in enumerate(top_x):
                        bookie_info = f" *(Quelle: {wette['bookie_name']})*" if buchmacher == "alle" else ""
                        st.info(f"**Baustein {i+1} ({wette['sport']}) | {wette['markt']}**\n\n**{wette['spiel']}**\n\n👉 **Tipp:** {wette['tipp']} | **Quote: {wette['quote']}**{bookie_info}")
                        gesamtquote *= wette['quote']
                        
                    st.success(f"🔥 **GESAMTQUOTE (KOMBI): {gesamtquote:.2f}**")
                else:
                    st.error("Absolut keine Spiele in diesem Quotenbereich gefunden. Der Markt (oder dieser Buchmacher) ist für heute komplett leergefegt.")
