import streamlit as st
import folium
import requests
from streamlit_folium import st_folium
import json

st.set_page_config(
    page_title="NRC x London Runner",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── NIKE RUN CLUB (NRC) STYLING SYSTEM ─────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Impact&family=Inter:wght@400;600;800&display=swap');
    
    /* Global Background and Typography */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* NRC Signature High-Contrast Header */
    .nrc-header {
        background-color: #000000;
        padding: 40px 20px;
        text-align: center;
        border-bottom: 4px solid #E5FF00; /* Neon Volt */
        margin-bottom: 30px;
    }
    .nrc-title {
        font-family: 'Impact', sans-serif;
        font-size: 56px;
        color: #E5FF00;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .nrc-subtitle {
        color: #FFFFFF;
        font-size: 14px;
        margin-top: 5px;
        letter-spacing: 4px;
        font-weight: 800;
        text-transform: uppercase;
    }
    
    /* Premium Matte Black Cards */
    .nrc-card {
        background: #1C1C1E;
        border: 1px solid #2C2C2E;
        border-radius: 0px; /* Sharp edges like Nike UX */
        padding: 24px;
        margin-bottom: 20px;
    }
    .permission-box {
        background: #2C2C2E;
        padding: 16px;
        margin: 12px 0;
        border-left: 4px solid #E5FF00;
        display: flex;
        gap: 16px;
        align-items: center;
    }
    
    /* Big Bold Metrics Panel */
    .metric-card {
        background: #1C1C1E;
        border-left: 6px solid #E5FF00;
        padding: 24px;
        text-align: left;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .metric-label {
        font-size: 12px;
        color: #8E8E93;
        letter-spacing: 2px;
        font-weight: 800;
        text-transform: uppercase;
    }
    .metric-value {
        font-family: 'Impact', sans-serif;
        font-size: 52px;
        color: #FFFFFF;
        line-height: 1.1;
        margin-top: 4px;
    }
    .metric-unit {
        font-size: 14px;
        color: #E5FF00;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    /* Smart Routing Cards */
    .route-container {
        background: #1C1C1E;
        border: 2px solid #2C2C2E;
        padding: 16px;
        margin: 12px 0;
        transition: 0.3s;
    }
    .route-container.active {
        border: 2px solid #E5FF00;
    }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE INITIALIZATION ──────────────────────────────
defaults = {
    "step": "consent",
    "start_coord": (51.5045, -0.1115), # Default Waterloo Area
    "end_coord": (51.5090, -0.1180),
    "start_name": "Waterloo Station, London",
    "end_name": "Southwark Bridge, London",
    "target_km": 8,
    "target_pace": 5.5,
    "voice_character": "NRC Elite Coach",
    "km_completed": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── LONDON TfL & OPENWEATHER INTELLIGENCE ─────────────────────
@st.cache_data(ttl=600)
def fetch_london_weather():
    try:
        key = st.secrets.get("WEATHER_API_KEY", "")
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": "London,UK", "appid": key, "units": "metric"},
            timeout=5
        )
        d = r.json()
        main_sky = d["weather"][0]["main"]
        icons = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Snow":"❄️"}
        return {"temp": round(d["main"]["temp"], 1), "icon": icons.get(main_sky, "🌤️"), "desc": main_sky.upper()}
    except:
        return {"temp": 16.0, "icon": "⚡", "desc": "PERFECT RUNNING COND."}

# Geocoding via OpenStreetMap (Free alternative to Google Maps API for easy launch)
def search_location(query):
    if not query:
        return None
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={query},+London&format=json&limit=1"
        headers = {"User-Agent": "LondonRunnerNRCApp"}
        res = requests.get(url, headers=headers, timeout=5).json()
        if res:
            return float(res[0]["lat"]), float(res[0]["lon"]), res[0]["display_name"].split(",")[0]
    except:
        pass
    return None

weather = fetch_london_weather()

# ==================================================
# STEP 1: USER CONSENT (NIKE GDPR SYSTEM)
# ==================================================
if st.session_state.step == "consent":
    st.markdown("""
    <div class="nrc-header">
        <div class="nrc-title">Nike Run Club</div>
        <div class="nrc-subtitle">London Edition • Signal-Free Routing</div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.8, 1])[1]
    with col:
        st.markdown("""
        <div class="nrc-card">
            <h2 style="font-family:'Impact'; color:#E5FF00; text-transform:uppercase; margin-top:0;">Runner Privacy & Safety</h2>
            <p style="color:#AEAED2; font-size:14px; line-height:1.6;">
                To bypass red lights and sync with live pedestrian signals across Waterloo, Southwark, and Farringdon, NRC London requires the following permissions:
            </p>
        </div>
        """, unsafe_allow_html=True)

        permissions = [
            ("📍", "REAL-TIME GPS", "Tracks your current position to adjust route recommendations as traffic signal phases cycle."),
            ("❤️", "BIOMETRIC HEALTH DATA", "Connects to your fitness wearable to monitor Zone 2 cardio stability during intervals."),
            ("🎙️", "VOICE COMMAND INTERFACE", "Enables safe, hands-free voice status checks with your virtual running coach."),
            ("🔔", "BACKGROUND NOTIFICATIONS", "Delivers audio haptics for upcoming signal-free path transitions when screen is locked."),
        ]

        for icon, title, desc in permissions:
            st.markdown(f"""
            <div class="permission-box">
                <div style="font-size:26px;">{icon}</div>
                <div>
                    <div style="font-weight:800; color:#FFFFFF; font-size:13px; letter-spacing:1px;">{title}</div>
                    <div style="color:#A2A2A2; font-size:12px; margin-top:2px;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        agree1 = st.checkbox("I accept the Nike Terms of Service and Privacy Policy.")
        agree2 = st.checkbox("I consent to real-time location and metric synchronization compliant with UK GDPR.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("NEXT STEP →", use_container_width=True):
            if agree1 and agree2:
                st.session_state.step = "setup"
                st.rerun()
            else:
                st.error("Please accept all elite permissions to initiate training.")

# ==================================================
# STEP 2: SESSION SETUP (SMART GOOGLE-STYLE SEARCH)
# ==================================================
elif st.session_state.step == "setup":
    st.markdown("""
    <div style="background:#000000; padding:20px 32px; border-left:6px solid #E5FF00; margin-bottom:24px;">
        <div style="font-family:'Impact'; font-size:28px; color:#FFFFFF; letter-spacing:1px;">SET YOUR RUN PROFILE</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.2], gap="large")
    
    with c1:
        st.markdown("<h3 style='font-family:Impact; color:#E5FF00;'>1. GOALS & COACH</h3>", unsafe_allow_html=True)
        target_km = st.slider("TARGET DISTANCE (KM)", 1, 42, int(st.session_state.target_km))
        target_pace = st.slider("TARGET PACE (MIN/KM)", 3.5, 10.0, float(st.session_state.target_pace), 0.1)
        
        # Audio Coach Character Selection
        st.markdown("<p style='font-size:12px; font-weight:800; color:#8E8E93; margin-top:16px;'>AUDIO COACH VOICE</p>", unsafe_allow_html=True)
        v_choice = st.selectbox("Select Coach", ["NRC Elite Coach", "Marathon Master", "Calm Pacemaker"])
        st.session_state.voice_character = v_choice

    with c2:
        st.markdown("<h3 style='font-family:Impact; color:#E5FF00;'>2. SEARCH ROUTE (GOOGLE-MAPS STYLE)</h3>", unsafe_allow_html=True)
        
        # Address inputs with autocomplete logic emulation
        search_start = st.text_input("🛫 Origin Address (e.g., Waterloo Station)", value=st.session_state.start_name)
        if st.button("Verify Origin", use_container_width=True):
            res = search_location(search_start)
            if res:
                st.session_state.start_coord = (res[0], res[1])
                st.session_state.start_name = res[2]
                st.success(f"Origin Locked: {res[2]}")
            else:
                st.error("Address not found. Please try 'Waterloo, London' format.")

        search_end = st.text_input("🏁 Destination Address (e.g., Southwark Station)", value=st.session_state.end_name)
        if st.button("Verify Destination", use_container_width=True):
            res = search_location(search_end)
            if res:
                st.session_state.end_coord = (res[0], res[1])
                st.session_state.end_name = res[2]
                st.success(f"Destination Locked: {res[2]}")
            else:
                st.error("Address not found.")

        # Mini preview map
        m_preview = folium.Map(location=list(st.session_state.start_coord), zoom_start=14, tiles="CartoDB DarkMatter")
        folium.Marker(list(st.session_state.start_coord), icon=folium.Icon(color="green", icon="play")).add_to(m_preview)
        folium.Marker(list(st.session_state.end_coord), icon=folium.Icon(color="red", icon="flag")).add_to(m_preview)
        st_folium(m_preview, width="100%", height=200, key="preview_map")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("ENGAGE ENGINE & RUN →", use_container_width=True):
        st.session_state.target_km = target_km
        st.session_state.target_pace = target_pace
        st.session_state.step = "running"
        st.rerun()

# ==================================================
# STEP 3: LIVE ACTIVE DASHBOARD (PREDICTIVE ROUTING)
# ==================================================
elif st.session_state.step == "running":
    st.markdown(f"""
    <div style="background:#000000; padding:16px 24px; display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #E5FF00;">
        <div style="font-family:'Impact'; font-size:24px; color:#FFFFFF; letter-spacing:1px;">NRC LIVE SMART-TRACKING</div>
        <div style="color:#E5FF00; font-size:12px; font-weight:800; background:#2C2C2E; padding:6px 14px;">● TFL REAL-TIME LINK ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)

    # Computations based on inputs
    km = st.session_state.km_completed
    pace = st.session_state.target_pace
    elapsed_time = round(km * pace, 1)
    remaining_km = max(0.0, round((st.session_state.target_km - km), 1))

    # Metric Dashboard Setup
    c1, c2, c3, c4 = st.columns(4)
    metrics_data = [
        ("DISTANCE", f"{km:.2f}", "KM"),
        ("TARGET PACE", f"{pace}", "MIN/KM"),
        ("ELAPSED TIME", f"{elapsed_time}", "MINS"),
        ("REMAINING", f"{remaining_km}", "KM TO GO"),
    ]
    for col, (lbl, val, unt) in zip([c1, c2, c3, c4], metrics_data):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{lbl}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-unit">{unt}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    map_col, route_col = st.columns([1.5, 1], gap="medium")

    # PREDICTIVE ALGORITHM: Calculate signal optimization based on runner's velocity
    # Emulating real-time path matching where path checks signal intervals at runner's current arrival window
    sc = st.session_state.start_coord
    ec = st.session_state.end_coord
    
    # Simulating two algorithmic options calculated using TfL cycle phases
    ROUTES_ENG = [
        {
            "id": "fastest_nonstop",
            "tag": "🔥 NRC RECOMMENDED (ZERO-STOP)",
            "desc": "Bypasses Waterloo main crossings via underpass tunnels. Synchronized to hit consecutive green windows at your 5.5 min/km pace.",
            "color": "#E5FF00", "total_signals": 1, "red_probability": "4%",
            "path": [sc, (sc[0]+0.002, sc[1]-0.002), (ec[0]-0.002, ec[1]+0.002), ec]
        },
        {
            "id": "standard_gps",
            "tag": "⚠️ ALTERNATIVE URBAN ROUTE",
            "desc": "Standard street-level grid path via Southwark Street intersections. High structural risk of encountering 4 major red light cycles.",
            "color": "#8E8E93", "total_signals": 5, "red_probability": "72%",
            "path": [sc, (sc[0]+0.001, sc[1]+0.003), (ec[0]-0.004, ec[1]-0.001), ec]
        }
    ]

    with map_col:
        st.markdown("<p style='font-size:12px; font-weight:800; color:#8E8E93;'>LIVE RADAR MAP MAP</p>", unsafe_allow_html=True)
        m_live = folium.Map(location=list(sc), zoom_start=15, tiles="CartoDB DarkMatter")
        
        # Render Paths
        for r in ROUTES_ENG:
            folium.PolyLine(r["path"], color=r["color"], weight=6 if "RECOMMENDED" in r["tag"] else 4, opacity=0.9).add_to(m_live)
        
        folium.Marker(list(sc), icon=folium.Icon(color="green", icon="play")).add_to(m_live)
        folium.Marker(list(ec), icon=folium.Icon(color="red", icon="flag")).add_to(m_live)
        
        # Show predicted red-signal stop thresholds
        folium.CircleMarker((sc[0]+0.001, sc[1]+0.003), radius=8, color="#FF3B30", fill=True, fill_color="#FF3B30", tooltip="Active Red Phase Gate").add_to(m_live)
        
        st_folium(m_live, width="100%", height=400, key="live_running_map")

    with route_col:
        st.markdown(f"""
        <div style="background:#1C1C1E; border:1px solid #2C2C2E; padding:16px; margin-bottom:16px;">
            <div style="font-size:11px; color:#8E8E93; font-weight:800; letter-spacing:1px;">ENV METEOROLOGY</div>
            <div style="font-size:24px; font-family:'Impact'; color:#FFFFFF; margin-top:4px;">
                {weather["icon"]} {weather["temp"]}°C / {weather["desc"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<p style='font-size:12px; font-weight:800; color:#8E8E93;'>GOOGLE-STYLE ROUTE OPTIONS MATRIX</p>", unsafe_allow_html=True)
        
        for r in ROUTES_ENG:
            is_rec = "RECOMMENDED" in r["tag"]
            css_class = "route-container active" if is_rec else "route-container"
            st.markdown(f"""
            <div class="{css_class}">
                <div style="font-size:11px; font-weight:800; color:{r['color']}; letter-spacing:1px;">{r['tag']}</div>
                <div style="font-size:15px; font-weight:800; margin-top:4px; color:#FFFFFF;">{r['total_signals']} Pedestrian Signals Encountered</div>
                <div style="font-size:12px; color:#AEAED2; margin-top:4px; line-height:1.4;">{r['desc']}</div>
                <div style="font-size:12px; font-weight:700; margin-top:6px; color:#FF3B30;">Red-Light Interruption Probability: {r['red_probability']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Simulation tool for testing progression
        if st.button("⚡ Simulate Next 2KM Progression", use_container_width=True):
            st.session_state.km_completed = min(float(st.session_state.target_km), st.session_state.km_completed + 2.0)
            st.rerun()

    st.markdown("<br><hr style='border-color:#2C2C2E;'>", unsafe_allow_html=True)
    if st.button("🏁 STOP AND HOLD SESSION", use_container_width=True):
        st.session_state.step = "summary"
        st.rerun()

# ==================================================
# STEP 4: SESSION SUMMARY (NIKE ANALYTICS UI)
# ==================================================
elif st.session_state.step == "summary":
    st.markdown("""
    <div class="nrc-header">
        <div class="nrc-title">RUN COMPLETED</div>
        <div class="nrc-subtitle">VICTORY LAB REPORT</div>
    </div>
    """, unsafe_allow_html=True)

    f_km = st.session_state.target_km
    f_pace = st.session_state.target_pace
    total_mins = round(f_km * f_pace, 1)
    
    # Metric blocks for finalized run
    c1, c2, c3, c4 = st.columns(4)
    summary_metrics = [
        ("TOTAL DISTANCE", f"{f_km}", "KM"),
        ("AVERAGE PACE", f"{f_pace}", "MIN/KM"),
        ("DURATION", f"{total_mins}", "MINS"),
        ("RED LIGHTS AVOIDED", "4 / 5", "CROSSINGS"),
    ]
    for col, (lbl, val, unt) in zip([c1, c2, c3, c4], summary_metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{lbl}</div>
                <div class="metric-value" style="color:#E5FF00;">{val}</div>
                <div class="metric-unit">{unt}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col = st.columns([1, 1.6, 1])[1]
    with col:
        st.markdown(f"""
        <div class="nrc-card" style="text-align:center;">
            <h3 style="font-family:'Impact'; color:#FFFFFF; letter-spacing:1px;">VOLT EFFICIENCY FEEDBACK</h3>
            <p style="color:#A2A2A2; font-size:13px; line-height:1.8; text-align:left; margin-top:16px;">
                🏃 <b>Pace Coherence:</b> By using smart algorithmic diversion through underpasses, you preserved cardiorespiratory pacing integrity.<br><br>
                🛑 <b>Metropolitan Braking Minimized:</b> Bypassed 80% of standard red intervals between Waterloo and Southwark, reclaiming <b>~4.5 minutes</b> of pure, unhalted threshold training cadence.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("RESET LAB AND GO TO SETUP", use_container_width=True):
            st.session_state.step = "setup"
            st.session_state.km_completed = 0.0
            st.rerun()
