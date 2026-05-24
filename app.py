
import streamlit as st
import folium
import requests
from streamlit_folium import st_folium
import json

st.set_page_config(
    page_title="London Runner",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Gail's Bakery 스타일 CSS ─────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap');

* { font-family: 'Inter', sans-serif; }
.stApp { background-color: #FAFAF5; color: #2C2C2C; }
.main .block-container { padding: 0; max-width: 100%; }

h1, h2, h3 {
    font-family: 'Playfair Display', serif;
    color: #1C3829;
    font-weight: 900;
}

.stButton>button {
    background: #1C3829;
    color: #FAFAF5;
    border: none;
    border-radius: 4px;
    padding: 14px 32px;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    width: 100%;
}
.stButton>button:hover { background: #2d5a3f; }

.stTextInput>div>div>input {
    background: #FAFAF5;
    border: 1px solid #D4C4A8;
    border-radius: 4px;
    color: #2C2C2C;
    padding: 12px 16px;
}

div[data-testid="stSidebar"] { background: #1C3829; }

.metric-card {
    background: white;
    border: 1px solid #E8D5B7;
    border-radius: 8px;
    padding: 24px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(28,56,41,0.08);
}
.metric-label {
    color: #8B7355;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.metric-value {
    color: #1C3829;
    font-size: 36px;
    font-weight: 900;
    font-family: 'Playfair Display', serif;
    line-height: 1;
}
.metric-unit {
    color: #8B7355;
    font-size: 13px;
    margin-top: 4px;
}

.route-card {
    background: white;
    border: 1px solid #E8D5B7;
    border-radius: 8px;
    padding: 20px;
    margin: 8px 0;
    cursor: pointer;
    transition: all 0.2s;
}
.route-card:hover { border-color: #1C3829; box-shadow: 0 4px 16px rgba(28,56,41,0.12); }
.route-card.best { border-left: 4px solid #1C3829; }

.section-title {
    font-family: 'Playfair Display', serif;
    color: #1C3829;
    font-size: 22px;
    font-weight: 700;
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #E8D5B7;
}

.consent-box {
    background: white;
    border: 1px solid #E8D5B7;
    border-radius: 8px;
    padding: 32px;
    max-width: 600px;
    margin: 0 auto;
}

.voice-card {
    background: white;
    border: 2px solid #E8D5B7;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    cursor: pointer;
}
.voice-card.selected { border-color: #1C3829; background: #f0f7f3; }

div[data-testid="stSelectbox"] > div { border-color: #D4C4A8; }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 초기화 ──────────────────────────────
defaults = {
    "step": "consent",
    "consent_done": False,
    "start_pin": None,
    "end_pin": None,
    "target_km": 10,
    "target_pace": 6.0,
    "voice_character": "친근한 코치",
    "running": False,
    "km_completed": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── 날씨 ─────────────────────────────────────────
@st.cache_data(ttl=600)
def get_weather():
    try:
        key = st.secrets.get("WEATHER_API_KEY", "")
        if not key: raise ValueError()
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": "London,UK", "appid": key, "units": "metric"},
            timeout=5
        )
        d = r.json()
        icons = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Drizzle":"🌦️","Snow":"❄️"}
        icon = icons.get(d["weather"][0]["main"], "🌤️")
        temp = round(d["main"]["temp"], 1)
        score = 100
        if temp < 2 or temp > 30: score -= 25
        if d["wind"]["speed"] > 12: score -= 20
        if "Rain" in d["weather"][0]["main"]: score -= 25
        return {"temp": temp, "feels": round(d["main"]["feels_like"],1),
                "icon": icon, "score": max(0,score),
                "desc": d["weather"][0]["description"]}
    except:
        return {"temp": 14, "feels": 12, "icon": "🌤️", "score": 75, "desc": "샘플"}

weather = get_weather()

# ══════════════════════════════════════════════════
# STEP 1: 개인정보 동의 화면
# ══════════════════════════════════════════════════
if st.session_state.step == "consent":

    st.markdown("""
    <div style="background:#1C3829;padding:32px;text-align:center;margin-bottom:0;">
        <div style="font-family:'Playfair Display',serif;font-size:36px;
                    color:#FAFAF5;font-weight:900;letter-spacing:-1px;">
            London Runner
        </div>
        <div style="color:#A8C4B0;font-size:14px;margin-top:8px;letter-spacing:2px;">
            MARATHON TRAINING · SIGNAL-FREE ROUTES
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col = st.columns([1,2,1])[1]
    with col:
        st.markdown("""
        <div class="consent-box">
            <div style="font-family:'Playfair Display',serif;font-size:22px;
                        color:#1C3829;font-weight:700;margin-bottom:16px;">
                Before We Begin
            </div>
            <div style="color:#5a5a4a;font-size:14px;line-height:1.8;margin-bottom:24px;">
                London Runner needs access to the following to provide
                you with the best training experience:
            </div>
        </div>
        """, unsafe_allow_html=True)

        items = [
            ("📍", "Location Access", "To track your real-time position and calculate route progress. Required for turn-by-turn navigation."),
            ("❤️", "Health Data", "To read heart rate and workout history from Apple Health for personalized training zones."),
            ("🎙️", "Microphone", "To enable voice commands so you can ask your AI coach questions while running."),
            ("🔔", "Notifications", "For km milestone alerts and pace coaching even when your screen is off."),
        ]

        for icon, title, desc in items:
            st.markdown(f"""
            <div style="background:#f8f6f0;border-radius:8px;padding:16px;
                        margin:8px 0;display:flex;gap:16px;align-items:flex-start;">
                <div style="font-size:24px;">{icon}</div>
                <div>
                    <div style="font-weight:600;color:#1C3829;margin-bottom:4px;">{title}</div>
                    <div style="color:#8B7355;font-size:13px;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#f0f7f3;border-radius:8px;padding:16px;margin:16px 0;
                    border-left:4px solid #1C3829;">
            <div style="font-size:12px;color:#5a5a4a;line-height:1.7;">
                Your data is processed locally and never sold to third parties.
                In compliance with <b>UK GDPR</b> and <b>Data Protection Act 2018</b>.
                You can withdraw consent at any time in Settings.
            </div>
        </div>
        """, unsafe_allow_html=True)

        agree1 = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        agree2 = st.checkbox("I consent to location and health data processing")
        agree3 = st.checkbox("I confirm I am 16 years or older")

        if st.button("GET STARTED →"):
            if agree1 and agree2 and agree3:
                st.session_state.step = "setup"
                st.rerun()
            else:
                st.error("Please accept all required permissions to continue.")

# ══════════════════════════════════════════════════
# STEP 2: 러닝 설정
# ══════════════════════════════════════════════════
elif st.session_state.step == "setup":

    st.markdown("""
    <div style="background:#1C3829;padding:20px 32px;">
        <div style="font-family:'Playfair Display',serif;font-size:24px;
                    color:#FAFAF5;font-weight:700;">London Runner</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Set Your Run</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        age = st.number_input("Age", value=28, min_value=15, max_value=70)
        max_hr = 220 - age
        z2 = round(max_hr * 0.60)
        z3 = round(max_hr * 0.80)
        st.caption(f"Target Heart Rate Zone 2~3: {z2}–{z3} bpm")
        target_km = st.slider("Target Distance (km)", 1, 42, 10)
        target_pace = st.slider("Target Pace (min/km)", 4.0, 12.0, 6.0, 0.1)

    with c2:
        st.markdown("""
        <div style="color:#1C3829;font-weight:600;font-size:14px;
                    letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">
            📍 Set Start & End Point
        </div>
        <div style="color:#8B7355;font-size:13px;margin-bottom:12px;">
            Click on the map to place your start pin, then end pin
        </div>
        """, unsafe_allow_html=True)

        # 지도 클릭으로 핀 설정
        m = folium.Map(location=[51.5074, -0.1278], zoom_start=13,
                      tiles="CartoDB Positron")

        if st.session_state.start_pin:
            folium.Marker(st.session_state.start_pin,
                icon=folium.Icon(color="green", icon="play", prefix="fa"),
                popup="Start").add_to(m)

        if st.session_state.end_pin:
            folium.Marker(st.session_state.end_pin,
                icon=folium.Icon(color="red", icon="flag", prefix="fa"),
                popup="End").add_to(m)

        map_data = st_folium(m, width=None, height=300,
                             returned_objects=["last_clicked"])

        if map_data and map_data.get("last_clicked"):
            clicked = (map_data["last_clicked"]["lat"],
                      map_data["last_clicked"]["lng"])
            if not st.session_state.start_pin:
                st.session_state.start_pin = clicked
                st.success(f"✅ Start set: {clicked[0]:.4f}, {clicked[1]:.4f}")
            elif not st.session_state.end_pin:
                st.session_state.end_pin = clicked
                st.success(f"✅ End set: {clicked[0]:.4f}, {clicked[1]:.4f}")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Reset Pins"):
                st.session_state.start_pin = None
                st.session_state.end_pin = None
                st.rerun()

    st.markdown('<div class="section-title">Voice & Audio</div>', unsafe_allow_html=True)

    voices = [
        {"name": "친근한 코치", "age": "30대", "desc": "Motivating & Friendly", "icon": "🏃"},
        {"name": "전문 트레이너", "age": "40대", "desc": "Professional & Precise", "icon": "💪"},
        {"name": "차분한 안내", "age": "30대", "desc": "Calm & Relaxed", "icon": "🧘"},
        {"name": "에너지 코치", "age": "20대", "desc": "Energetic & Fun", "icon": "⚡"},
    ]

    v_cols = st.columns(4)
    for i, (col, v) in enumerate(zip(v_cols, voices)):
        with col:
            selected = st.session_state.voice_character == v["name"]
            bg = "#f0f7f3" if selected else "white"
            border = "#1C3829" if selected else "#E8D5B7"
            st.markdown(f"""
            <div style="background:{bg};border:2px solid {border};border-radius:8px;
                        padding:16px;text-align:center;">
                <div style="font-size:28px;">{v["icon"]}</div>
                <div style="font-weight:600;color:#1C3829;font-size:13px;">{v["name"]}</div>
                <div style="color:#8B7355;font-size:11px;">{v["desc"]}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(v["name"], key=f"voice_{i}"):
                st.session_state.voice_character = v["name"]
                st.rerun()

    spotify = st.checkbox("🎵 Enable Spotify integration (voice pauses for coaching)")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("START RUNNING →"):
        st.session_state.target_km = target_km
        st.session_state.target_pace = target_pace
        st.session_state.step = "running"
        st.rerun()

# ══════════════════════════════════════════════════
# STEP 3: 러닝 화면
# ══════════════════════════════════════════════════
elif st.session_state.step == "running":

    st.markdown("""
    <div style="background:#1C3829;padding:16px 24px;
                display:flex;justify-content:space-between;align-items:center;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;color:#FAFAF5;">
            London Runner
        </div>
        <div style="color:#A8C4B0;font-size:13px;">● LIVE</div>
    </div>
    """, unsafe_allow_html=True)

    # 주요 지표
    km = st.session_state.km_completed
    pace = st.session_state.target_pace
    elapsed = round(km * pace, 0)
    remaining = round((st.session_state.target_km - km), 1)

    c1,c2,c3,c4 = st.columns(4)
    metrics = [
        ("DISTANCE", f"{km}", "km"),
        ("PACE", f"{pace}", "min/km"),
        ("TIME", f"{int(elapsed)}", "min"),
        ("REMAINING", f"{remaining}", "km left"),
    ]
    for col, (label, val, unit) in zip([c1,c2,c3,c4], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-unit">{unit}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    map_col, info_col = st.columns([3,2])

    ROUTES = [
        {"name":"Best Route","color":"#1C3829","stops":4,
         "points":[(51.5074,-0.1278),(51.5065,-0.1229),
                   (51.5055,-0.1090),(51.5033,-0.0980),(51.5155,-0.0922)]},
        {"name":"Mid Route","color":"#8B7355","stops":8,
         "points":[(51.5074,-0.1278),(51.5100,-0.1150),
                   (51.5120,-0.1050),(51.5140,-0.0980),(51.5155,-0.0922)]},
    ]

    with map_col:
        start = st.session_state.start_pin or (51.5074,-0.1278)
        end   = st.session_state.end_pin   or (51.5155,-0.0922)

        m = folium.Map(location=list(start), zoom_start=14,
                      tiles="CartoDB Positron")
        for r in ROUTES:
            folium.PolyLine(r["points"], color=r["color"],
                           weight=5, opacity=0.9,
                           tooltip=r["name"]).add_to(m)
        folium.Marker(list(start),
            icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(m)
        folium.Marker(list(end),
            icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(m)
        for pos in [(51.5062,-0.1200),(51.5048,-0.1020)]:
            folium.CircleMarker(pos, radius=7,
                color="#E8C9A0", fill=True,
                fill_color="#E8C9A0", fill_opacity=0.9,
                tooltip="🚦 Signal").add_to(m)
        st_folium(m, width=None, height=400)

    with info_col:
        # 날씨
        st.markdown(f"""
        <div style="background:white;border:1px solid #E8D5B7;border-radius:8px;
                    padding:16px;margin-bottom:12px;">
            <div style="color:#8B7355;font-size:11px;letter-spacing:2px;margin-bottom:8px;">
                LONDON WEATHER
            </div>
            <div style="font-size:32px;font-weight:900;color:#1C3829;">
                {weather["icon"]} {weather["temp"]}°C
            </div>
            <div style="color:#8B7355;font-size:13px;">
                Feels {weather["feels"]}°C · {weather["desc"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 루트 비교
        st.markdown('<div style="color:#1C3829;font-weight:600;font-size:13px;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">Route Comparison</div>', unsafe_allow_html=True)
        for r in ROUTES:
            lost = round(r["stops"] * 2.25, 1)
            zone_t = round(60 - lost, 1)
            zone_r = round((zone_t / 60) * 100, 0)
            bar = "█" * int(zone_r/10) + "░" * (10 - int(zone_r/10))
            st.markdown(f"""
            <div class="route-card">
                <div style="font-weight:600;color:#1C3829;">{r["name"]}</div>
                <div style="color:#8B7355;font-size:12px;">{r["stops"]} signals · Zone {int(zone_r)}%</div>
                <div style="color:#1C3829;font-family:monospace;font-size:13px;">[{bar}]</div>
            </div>""", unsafe_allow_html=True)

        # 음성 안내
        st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
        if st.button("🔊 Voice Coaching"):
            msg = f"{km} kilometres completed. Current pace {pace} minutes per kilometre. {remaining} kilometres remaining. Heart rate Zone 2 to 3. Keep going, you're doing great."
            st.markdown(f"""
            <script>
            var u = new SpeechSynthesisUtterance("{msg}");
            u.lang = "en-GB"; u.rate = 0.85; u.pitch = 1.0;
            window.speechSynthesis.speak(u);
            </script>
            """, unsafe_allow_html=True)

        # AI Q&A
        q = st.text_input("Ask your coach...",
            placeholder="How's my pace? Will it rain?")
        if st.button("Ask →") and q:
            try:
                key = st.secrets.get("GEMINI_API_KEY", "")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}"
                prompt = f"You are a London marathon running coach. Runner status: {km}km done, pace {pace}min/km, weather {weather['temp']}°C. Question: {q}. Answer in 2 sentences max."
                r = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}]}, timeout=8)
                ans = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                st.markdown(f"""
                <div style="background:#f0f7f3;border-left:3px solid #1C3829;
                            border-radius:4px;padding:12px;font-size:13px;">{ans}</div>
                """, unsafe_allow_html=True)
                st.markdown(f"""<script>
                var u = new SpeechSynthesisUtterance(`{ans}`);
                u.lang="en-GB"; window.speechSynthesis.speak(u);
                </script>""", unsafe_allow_html=True)
            except:
                st.info("Add GEMINI_API_KEY to Streamlit Secrets")

    if st.button("🏁 FINISH RUN"):
        st.session_state.step = "summary"
        st.rerun()

# ══════════════════════════════════════════════════
# STEP 4: 러닝 요약
# ══════════════════════════════════════════════════
elif st.session_state.step == "summary":

    st.markdown("""
    <div style="background:#1C3829;padding:48px 32px;text-align:center;">
        <div style="font-size:48px;margin-bottom:8px;">🏅</div>
        <div style="font-family:'Playfair Display',serif;font-size:32px;
                    color:#FAFAF5;font-weight:900;">Run Complete</div>
        <div style="color:#A8C4B0;font-size:14px;margin-top:8px;">
            Great work today, Runner.
        </div>
    </div>
    """, unsafe_allow_html=True)

    km = st.session_state.target_km
    pace = st.session_state.target_pace
    stops = 4
    lost_min = round(stops * 2.25, 1)
    zone_pct = round(((km*pace - lost_min)/(km*pace))*100, 0)
    cal = round(km * 72.9, 0)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    results = [
        ("DISTANCE", f"{km}", "km"),
        ("AVG PACE", f"{pace}", "min/km"),
        ("ZONE TIME", f"{int(zone_pct)}", "%"),
        ("CALORIES", f"{int(cal)}", "kcal"),
    ]
    for col, (label, val, unit) in zip([c1,c2,c3,c4], results):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-unit">{unit}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col = st.columns([1,2,1])[1]
    with col:
        st.markdown(f"""
        <div style="background:white;border:1px solid #E8D5B7;border-radius:8px;padding:32px;">
            <div style="font-family:'Playfair Display',serif;font-size:18px;
                        color:#1C3829;font-weight:700;margin-bottom:16px;">
                Training Impact
            </div>
            <div style="color:#5a5a4a;font-size:14px;line-height:2;">
                ✅ Signal-free route: <b>{stops} stops avoided</b><br>
                ✅ Zone 2~3 maintained: <b>{int(zone_pct)}% of run</b><br>
                ✅ Effective training: <b>{round(km*pace - lost_min, 0)} minutes</b><br>
                ✅ Marathon progress: <b>+{round(km/42.195*100, 1)}% of full distance</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("NEW RUN →"):
            st.session_state.step = "setup"
            st.session_state.start_pin = None
            st.session_state.end_pin = None
            st.rerun()

st.markdown("""
<div style="text-align:center;padding:24px;color:#8B7355;font-size:11px;
            letter-spacing:2px;border-top:1px solid #E8D5B7;margin-top:32px;">
    LONDON RUNNER · MARATHON TRAINING · SIGNAL-FREE ROUTES
</div>
""", unsafe_allow_html=True)
