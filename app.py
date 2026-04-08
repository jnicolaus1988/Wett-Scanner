import streamlit as st
import requests

# 1. DESIGN DER APP
st.set_page_config(page_title="KI Kombi-Scanner", page_icon="🎯", layout="centered")
st.title("🎯 KI Low-Risk Scanner")
st.markdown("Zieht Live-Quoten über die API und filtert nach Hochwahrscheinlichkeits-Spielen.")

# 2. SEITENLEISTE (EINSTELLUNGEN)
st.sidebar.header("⚙️ Deine Einstellungen")
api_key = st.sidebar.text_input("🔑 Dein The-Odds-API Key", type="password", help="Hol dir den Key auf the-odds-api.com")
st.sidebar.markdown("---")
max_quote = st.sidebar.slider("Maximale Quote", 1.15, 1.50, 1.35, 0.01)
min_quote = st.sidebar.slider("Minimale Quote", 1.05, 1.25, 1.15, 0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("Welche Sportarten scannen?")
check_soccer = st.sidebar.checkbox("⚽ Fußball (Champions League)", value=True)
check_tennis = st.sidebar.checkbox("🎾 Tennis (ATP)", value=True)
check_basketball = st.sidebar.checkbox("🏀 Basketball (NBA)", value=True)

# 3. DIE DATEN-ENGINE
def hole_live_quoten(sport, key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={key}&regions=eu&markets=h2h"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# 4. DER HAUPT-BUTTON
if st.button("🚀 Globalen Markt scannen", use_container_width=True):
    if not api_key:
        st.warning("⚠️ Bitte trage zuerst links (oder im Menü) deinen API-Key ein!")
    else:
        sportarten = []
        if check_soccer: sportarten.append("soccer_uefa_champs_league")
        if check_tennis: sportarten.append("tennis_atp")
        if check_basketball: sportarten.append("basketball_nba")

        if not sportarten:
            st.warning("Bitte wähle mindestens eine Sportart aus.")
        else:
            with st.spinner("Zapfe Buchmacher-Server an..."):
                gefundene_wetten = []
                for sport in sportarten:
                    daten = hole_live_quoten(sport, api_key)
                    for spiel in daten:
                        if 'home_team' not in spiel or 'bookmakers' not in spiel: continue
                        team_a = spiel['home_team']
                        team_b = spiel['away_team']
                        
                        for buchmacher in spiel['bookmakers']:
                            if not buchmacher['markets']: continue
                            quoten = buchmacher['markets'][0]['outcomes']
                            for quote in quoten:
                                if min_quote <= quote['price'] <= max_quote:
                                    gefundene_wetten.append({
                                        "sport": sport.split('_')[0].capitalize(),
                                        "spiel": f"{team_a} vs {team_b}",
                                        "tipp": quote['name'],
                                        "quote": quote['price']
                                    })
                                    break 

                st.success("Scan abgeschlossen!")
                
                # 5. TICKET AUSGEBEN
                st.markdown("### 🎫 Dein KI-Ticket für heute")
                if len(gefundene_wetten) >= 3:
                    # Wir sortieren die Wetten nach Sicherheit (niedrigste Quote zuerst)
                    gefundene_wetten = sorted(gefundene_wetten, key=lambda x: x['quote'])
                    top_3 = gefundene_wetten[:3] 
                    gesamtquote = 1.0
                    
                    for i, wette in enumerate(top_3):
                        st.info(f"**Baustein {i+1} ({wette['sport']})**\n\n{wette['spiel']}\n\n👉 **Tipp:** {wette['tipp']} | **Quote: {wette['quote']}**")
                        gesamtquote *= wette['quote']
                        
                    st.success(f"🔥 **GESAMTQUOTE (KOMBI): {gesamtquote:.2f}**")
                    st.markdown("*Tippe diese 3 Spiele jetzt in deiner Tipico-App nach.*")
                else:
                    st.warning("Nicht genügend Spiele gefunden. Die Buchmacher haben aktuell keine passenden Spiele. Versuche es in ein paar Stunden wieder!")
