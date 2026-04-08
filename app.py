import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="KI Pro-Scanner", page_icon="🎱", layout="centered")
st.title("🎱 KI Pro-Scanner (Ultimate)")

# --- GEDÄCHTNIS ---
if 'api_used' not in st.session_state: st.session_state.api_used = "?"
if 'api_remaining' not in st.session_state: st.session_state.api_remaining = "?"

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

# --- ENGINE ---
def hole_daten(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            st.session_state.api_used = res.headers.get('x-requests-used', st.session_state.api_used)
            st.session_state.api_remaining = res.headers.get('x-requests-remaining', st.session_state.api_remaining)
            return res.json()
    except: pass
    return []

# --- MAIN ---
if st.button("🚀 DEEP SCAN STARTEN"):
    if not api_key: st.error("Key fehlt!")
    else:
        jetzt = datetime.now(timezone.utc)
        limit_zeit = jetzt + timedelta(hours=zeitfenster_stunden)
        
        # 1. Sportarten holen
        sport_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}"
        alle_sportarten = hole_daten(sport_url)
        
        target_list = [s['key'] for s in alle_sportarten if s.get('active')]
        if scan_modus == "vip":
            target_list = [s for s in target_list if s in VIP_SPORTS]
        
        if not target_list: st.warning("Keine Sportarten gefunden.")
        else:
            status = st.empty()
            bar = st.progress(0)
            gefundene = []
            
            # Diagnose-Variablen
            stats = {"zu_spät": 0, "falsche_quote": 0, "kein_markt": 0}

            for i, s_key in enumerate(target_list):
                status.text(f"Scanne {s_key}... ({i+1}/{len(target_list)})")
                bar.progress((i+1)/len(target_list))
                
                # Wir scannen jetzt JEDE Sportart einzeln
                q_url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={api_key}&regions=eu,uk&markets=h2h,totals&bookmakers={'' if buchmacher=='alle' else buchmacher}"
                events = hole_daten(q_url)
                
                for ev in events:
                    # Zeit-Check
                    t_str = ev.get('commence_time')
                    t_obj = datetime.fromisoformat(t_str.replace('Z', '+00:00'))
                    if t_obj > limit_zeit:
                        stats["zu_spät"] += 1
                        continue
                    
                    if not ev.get('bookmakers'): 
                        stats["kein_markt"] += 1
                        continue
                        
                    for bm in ev['bookmakers']:
                        for m in bm.get('markets', []):
                            for o in m.get('outcomes', []):
                                price = o.get('price')
                                if min_quote <= price <= max_quote:
                                    gefundene.append({
                                        "name": f"{ev['home_team']} vs {ev['away_team']}",
                                        "tipp": o['name'],
                                        "quote": price,
                                        "zeit": t_obj.strftime("%H:%M"),
                                        "liga": s_key.upper()
                                    })
                                else:
                                    stats["falsche_quote"] += 1

            status.empty()
            bar.empty()

            if gefundene:
                gefundene = sorted(gefundene, key=lambda x: x['quote'])
                st.success(f"{len(gefundene)} Wetten gefunden!")
                for w in gefundene[:ticket_groesse]:
                    st.info(f"**{w['liga']}** | {w['zeit']} Uhr\n\n{w['name']}\n\n👉 {w['tipp']} | **{w['quote']}**")
            else:
                st.error("Nichts gefunden.")
                st.write(f"Diagnose: {stats['zu_spät']} Spiele zu weit in der Zukunft, {stats['falsche_quote']} hatten nicht deine Quote.")
