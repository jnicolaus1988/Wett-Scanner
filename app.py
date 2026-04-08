import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

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
buchmacher = st.sidebar.radio(
    "🏦 Ziel-Buchmacher:",
    ("bet365", "bwin", "unibet", "alle"),
    format_func=lambda x: {"bet365": "1. Bet365 (Primär)", "bwin": "2. Bwin (Backup)", "unibet": "3. Unibet (Spezialist)", "alle": "🌍 Globaler Mix (Alle ansehen)"}[x]
)

st.sidebar.markdown("---")
max_quote = st.sidebar.slider("Maximale Quote", 1.15, 1.50, 1.35, 0.01)
min_quote = st.sidebar.slider("Minimale Quote", 1.01, 1.25, 1.15, 0.01)
ticket_groesse = st.sidebar.slider("🎟️ Wunsch-Kombi-Größe", 2, 10, 5, 1)

# --- DER ZEIT-FILTER ---
st.sidebar.markdown("---")
st.sidebar.subheader("⏳ Zeit-Filter")
zeitfenster_stunden = st.sidebar.slider("Max. Zeit bis Anpfiff (Stunden)", 12, 72, 24, 12, help="Filtert Spiele heraus, die zu weit in der Zukunft liegen.")

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
        jetzt = datetime.now(timezone.utc)
        max_zeit = jetzt + timedelta(hours=zeitfenster_stunden)
        
        with st.spinner("Prüfe aktive Märkte..."):
            aktive_vips = hole_aktive_vip_sports(api_key)
            
        if not aktive_vips:
            st.warning("Aktuell läuft keiner der globalen Top-Märkte. Versuche es später wieder.")
        else:
            with st.spinner(f"Analysiere Quoten für die nächsten {zeitfenster_stunden} Stunden..."):
                gefundene_wetten = []
                gesehene_wetten_id = set()
                
                for sport in aktive_vips:
                    daten = scan_sportart(sport, api_key, buchmacher)
                    
                    for spiel in daten:
                        startzeit_str = spiel.get('commence_time')
                        if startzeit_str:
                            try:
                                startzeit = datetime.fromisoformat(startzeit_str.replace('Z', '+00:00'))
                                if startzeit > max_zeit:
                                    continue
                            except:
                                pass 
                        
                        if 'bookmakers' not in spiel: continue
                        team_a = spiel.get
