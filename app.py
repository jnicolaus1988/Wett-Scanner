import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="KI Pro-Scanner", page_icon="🎱", layout="centered")
st.title("🎱 KI Pro-Scanner (Ultimate Edition)")

# --- GEDÄCHTNIS ---
if 'api_used' not in st.session_state: st.session_state.api_used = "0"
if 'api_remaining' not in st.session_state: st.session_state.api_remaining = "500"

VIP_SPORTS = ["soccer_uefa_champs_league", "soccer_epl", "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_spain_la_liga", "tennis_atp", "tennis_wta", "basketball_nba", "basketball_euroleague"]

# --- SIDEBAR ---
st.sidebar.header("⚙️ Parameter")
api_key = st.sidebar.text_input("🔑 API Key", type="password")
buchmacher = st.sidebar.radio("🏦 Buchmacher:", ("bet365", "bwin", "unibet", "alle"))
max_quote = st.sidebar.slider("Maximale Quote", 1.10, 2.00, 1.40, 0.01)
min_quote = st.sidebar.slider("Minimale Quote", 1.01, 1.20, 1.10, 0.01)
ticket_groesse = st.sidebar.slider("🎟️ Kombi-Größe", 2, 10, 5, 1)
zeitfenster_stunden = st.sidebar.slider("⏳ Max. Stunden bis Start", 6, 72, 24, 6)
scan_modus = st.sidebar.radio("🌍 Scan-Tiefe", ("vip", "alles"))

st.sidebar.markdown("---")
st.sidebar.subheader("📊 API Guthaben")
st.sidebar.write(f"Verbraucht: **{st.session_state.api_used}**")
st.sidebar.write(f"Verbleibend: **{st.session_state.api_remaining}**")

# --- ENGINE ---
def hole_daten(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            st.session_state.api_used = res.headers.get('x-requests-used', st.session_state.api_used)
            st.session_state.api_remaining = res.headers.get('x-requests-remaining', st.session_state.api_remaining)
            return res.json()
    except: pass
    return []

# --- MAIN ---
if st.button("🚀 JETZT GLOBAL SCANNEN"):
    if not api_key: st.error("Bitte API Key eingeben!")
    else:
        jetzt = datetime.now(timezone.utc)
        limit_zeit = jetzt + timedelta(hours=zeitfenster_stunden)
        
        with st.spinner("Hole Sportarten..."):
            s_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}"
            alle_sportarten = hole_daten(s_url)
        
        target_list = [s['key'] for s in alle_sportarten if s.get('active')]
        if scan_modus == "vip":
            target_list = [s for s in target_list if s in VIP_SPORTS]
        
        if not target_list:
            st.warning("Keine aktiven Sportarten gefunden.")
        else:
            bar = st.progress(0)
            status = st.empty()
            gefundene = []
            
            for i, s_key in enumerate(target_list):
                status.text(f"Scanne {s_key}... ({i+1}/{len(target_list)})")
                bar.progress((i+1)/len(target_list))
                
                # Wir fragen jetzt die Märkte dynamischer ab
                q_url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_key}&regions=eu,uk&bookmakers={'' if buchmacher=='alle' else buchmacher}"
                events = hole_daten(q_url)
                
                if isinstance(events, list):
                    for ev in events:
                        t_str = ev.get('commence_time')
                        t_obj = datetime.fromisoformat(t_str.replace('Z', '+00:00'))
                        
                        if t_obj <= limit_zeit:
                            for bm in ev.get('bookmakers', []):
                                for m in bm.get('markets', []):
                                    for o in m.get('outcomes', []):
                                        price = o.get('price')
                                        if min_quote <= price <= max_quote:
                                            gefundene.append({
                                                "liga": s_key.upper(),
                                                "zeit": t_obj.strftime("%d.%m. %H:%M"),
                                                "match": f"{ev['home_team']} vs {ev['away_team']}",
                                                "tipp": o['name'],
                                                "quote": price
                                            })
            
            status.empty()
            bar.empty()
            
            if gefundene:
                # Duplikate entfernen (gleiches Match, gleicher Tipp)
                unique_tickets = {f"{w['match']}_{w['tipp']}": w for w in gefundene}.values()
                sorted
