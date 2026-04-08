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
            daten = response.json()
            # Sicherheits-Check: Ist das Ergebnis wirklich eine Liste?
            if isinstance(daten, list):
                alle_aktiven = [sport['key'] for sport in daten if sport.get('active')]
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
            daten = response.json()
            if isinstance(daten, list):
                return daten
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
        
        with st.spinner("🛰️ Verbinde mit Servern und prüfe aktive Märkte..."):
            aktive_vips = hole_aktive_vip_sports(api_key)
            
        if not aktive_vips:
            st.warning("Aktuell läuft keiner der globalen Top-Märkte. Versuche es später wieder.")
        else:
            st.info(f"📡 {len(aktive_vips)} globale Ligen online. Starte Deep-Scan...")
            
            # --- NEU: LIVE-DASHBOARD (LADEBALKEN) ---
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            gefundene_wetten = []
            gesehene_wetten_id = set()
            
            for index, sport in enumerate(aktive_vips):
                # Update der Live-Anzeige
                status_text.text(f"🔍 Analysiere: {sport.upper()} ... ({index + 1}/{len(aktive_vips)})")
                progress_bar.progress((index + 1) / len(aktive_vips))
                
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
                    team_a = spiel.get('home_team', 'Unbekannt')
                    team_b = spiel.get('away_team', 'Unbekannt')
                    spiel_name = f"{team_a} vs {team_b}"
                    
                    for bm in spiel['bookmakers']:
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
                                        
                                        anzeige_datum = "Unbekannt"
                                        if startzeit_str:
                                            try:
                                                # Zeit auf unsere Zeitzone (+2h) angleichen (simpel)
                                                anzeige_datum = startzeit.strftime("%d.%m. %H:%M")
                                            except: pass
                                        
                                        gefundene_wetten.append({
                                            "sport": sport.replace('soccer_', '').replace('tennis_', '').replace('basketball_', '').upper(),
                                            "spiel": spiel_name,
                                            "zeit": anzeige_datum,
                                            "markt": anzeige_markt,
                                            "tipp": tipp_text,
                                            "quote": quote['price'],
                                            "bookie_name": buchmacher_name
                                        })
                                        gesehene_wetten_id.add(einzigartige_id)

            # Lade-Animationen am Ende entfernen
            status_text.empty()
            progress_bar.empty()
            
            st.success("✅ Analyse erfolgreich abgeschlossen!")
            
            # --- DAS TICKET ---
            if len(gefundene_wetten) > 0:
                gefundene_wetten = sorted(gefundene_wetten, key=lambda x: x['quote'])
                top_x = gefundene_wetten[:ticket_groesse]
                gesamtquote = 1.0
                
                st.markdown(f"### 🎫 Dein Ticket ({len(top_x)} Bausteine)")
                
                if len(gefundene_wetten) < ticket_groesse:
                    st.warning(f"Achtung: Du wolltest {ticket_groesse} Spiele, aber für die nächsten {zeitfenster_stunden} Stunden gibt der Markt nur {len(gefundene_wetten)} her.")
                
                for i, wette in enumerate(top_x):
                    bookie_info = f" *(Quelle: {wette['bookie_name']})*" if buchmacher == "alle" else ""
                    st.info(f"**Baustein {i+1} ({wette['sport']}) | 🕒 {wette['zeit']} UTC | {wette['markt']}**\n\n**{wette['spiel']}**\n\n
