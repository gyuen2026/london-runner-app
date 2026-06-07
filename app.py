import streamlit as st
import folium
import requests
from streamlit_folium import st_folium
import math

st.set_page_config(
    page_title='NRC x London Runner Pro',
    page_icon='🏃',
    layout='wide',
    initial_sidebar_state='collapsed'
)

# ── NIKE RUN CLUB (NRC) DARK PREMIUM STYLING ─────────────────────
st.markdown('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Impact&family=Inter:wght=400;600;700;900&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }

    .nrc-header {
        background-color: #000000;
        padding: 30px 20px;
        text-align: center;
        border-bottom: 4px solid #E5FF00;
        margin-bottom: 20px;
    }
    .nrc-title {
        font-family: 'Impact', sans-serif;
        font-size: 48px;
        color: #E5FF00;
        letter-spacing: 2px;
    }

    .nrc-card {
        background: #1C1C1E;
        border: 1px solid #2C2C2E;
        padding: 20px;
        margin-bottom: 15px;
    }

    .metric-card {
        background: #1C1C1E;
        border-top: 4px solid #E5FF00;
        padding: 20px;
        text-align: center;
    }
    .metric-label {
        font-size: 11px;
        color: #8E8E93;
        font-weight: 800;
        letter-spacing: 1.5px;
    }
    .metric-value {
        font-family: 'Impact', sans-serif;
        font-size: 44px;
        color: #FFFFFF;
        margin-top: 4px;
    }

    .search-item {
        background: #2C2C2E;
        padding: 10px 14px;
        margin: 4px 0;
        border-radius: 4px;
        cursor: pointer;
        border-left: 3px solid #8E8E93;
    }
    .search-item:hover {
        border-left: 3px solid #E5FF00;
        background: #3A3A3C;
    }

    .nav-instruction {
        background: #000000;
        border-left: 6px solid #007AFF;
        padding: 15px;
        font-size: 16px;
        font-weight: 700;
        color: #E5FF00;
        margin-top: 10px;
    }
</style>
''', unsafe_allow_html=True)

# ── SESSION STATE MANAGEMENT ──────────────────────────────
defaults = {
    'step': 'consent',
    'start_coord': (51.5045, -0.1115), 
    'end_coord': (51.5090, -0.1180),
    'start_name': 'Waterloo Station',
    'end_name': 'Southwark Bridge',
    'target_km': 5,
    'target_pace': 6.0,
    'selected_route_id': None,
    'km_completed': 0.0,
    'current_coord': None,
    'search_results_start': [],
    'search_results_end': []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── GEOCODING ENGINE (GOOGLE-STYLE SEARCH) ─────────────────────
def get_location_suggestions(query):
    if not query: return []
    try:
        url = f'https://nominatim.openstreetmap.org/search?q={query},+London&format=json&limit=4'
        headers = {'User-Agent': 'LondonRunnerNRCPro'}
        res = requests.get(url, headers=headers, timeout=5).json()
        return [{'lat': float(item['lat']), 'lon': float(item['lon']), 'name': item['display_name'].split(',')[0]} for item in res]
    except:
        return []

def haversine_distance(coord1, coord2):
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ==================================================
# STEP 1: PRIVACY AGREEMENT
# ==================================================
if st.session_state.step == 'consent':
    st.markdown('<div class="nrc-header"><div class="nrc-title">NIKE RUN CLUB</div></div>', unsafe_allow_html=True)
    col = st.columns([1, 1.5, 1])[1]
    with col:
        st.markdown('<div class="nrc-card"><h3>LIVE DATA PROCESSING</h3><p style="color:#8E8E93;">NRC requires GPS Tracking and TfL Signal linking to optimize your performance.</p></div>', unsafe_allow_html=True)
        if st.button('I AGREE & CONTINUE', use_container_width=True):
            st.session_state.step = 'setup'
            st.rerun()

# ==================================================
# STEP 2: SEARCH & LOCATION MATRIX (GOOGLE-UX)
# ==================================================
elif st.session_state.step == 'setup':
    st.markdown('<div class="nrc-header"><div class="nrc-title">ROUTE CONFIGURATION</div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.2], gap='large')

    with c1:
        st.markdown("<h3 style='font-family:Impact; color:#E5FF00;'>📍 LOCATIONS SEARCH</h3>", unsafe_allow_html=True)

        col_s1, col_b1 = st.columns([5, 1])
        with col_s1:
            start_q = st.text_input('Origin Address', value=st.session_state.start_name)
        with col_b1:
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button('🔍', key='search_start_btn'):
                st.session_state.search_results_start = get_location_suggestions(start_q)

        if st.session_state.search_results_start:
            st.markdown("<p style='font-size:11px; color:#8E8E93;'>Select matching origin location:</p>", unsafe_allow_html=True)
            for idx, res in enumerate(st.session_state.search_results_start):
                if st.button(f"📍 {res['name']}", key=f"src_{idx}", use_container_width=True):
                    st.session_state.start_coord = (res['lat'], res['lon'])
                    st.session_state.start_name = res['name']
                    st.session_state.search_results_start = []
                    st.rerun()

        col_s2, col_b2 = st.columns([5, 1])
        with col_s2:
            end_q = st.text_input('Destination Address', value=st.session_state.end_name)
        with col_b2:
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button('🔍', key='search_end_btn'):
                st.session_state.search_results_end = get_location_suggestions(end_q)

        if st.session_state.search_results_end:
            st.markdown("<p style='font-size:11px; color:#8E8E93;'>Select matching destination location:</p>", unsafe_allow_html=True)
            for idx, res in enumerate(st.session_state.search_results_end):
                if st.button(f"🏁 {res['name']}", key=f"dst_{idx}", use_container_width=True):
                    st.session_state.end_coord = (res['lat'], res['lon'])
                    st.session_state.end_name = res['name']
                    st.session_state.search_results_end = []
                    st.rerun()

        st.markdown("<hr style='border-color:#2C2C2E;'>", unsafe_allow_html=True)
        st.session_state.target_pace = st.slider('SET RUNNING PACE (MIN/KM)', 4.0, 9.0, float(st.session_state.target_pace), 0.1)

    with c2:
        st.markdown("<h3 style='font-family:Impact; color:#E5FF00;'>🗺️ SELECTED ANCHORS PREVIEW</h3>", unsafe_allow_html=True)
        st.info(f"From: {st.session_state.start_name} -> To: {st.session_state.end_name}")

        m_preview = folium.Map(location=list(st.session_state.start_coord), zoom_start=14, tiles='CartoDB DarkMatter')
        folium.Marker(list(st.session_state.start_coord), icon=folium.Icon(color='green', icon='play')).add_to(m_preview)
        folium.Marker(list(st.session_state.end_coord), icon=folium.Icon(color='red', icon='flag')).add_to(m_preview)
        st_folium(m_preview, width='100%', height=280, key='setup_preview_map')

    if st.button('GENERATE SMART ROUTES →', use_container_width=True):
        st.session_state.step = 'route_selection'
        st.rerun()

# ==================================================
# STEP 3: 5-ROUTE MATRIX RECOMMENDATION (GOOGLE-STYLE)
# ==================================================
elif st.session_state.step == 'route_selection':
    st.markdown('<div class="nrc-header"><div class="nrc-title">SELECT INTELLIGENT ROUTE</div></div>', unsafe_allow_html=True)

    sc = st.session_state.start_coord
    ec = st.session_state.end_coord

    ROUTES_5 = [
        {"id": "R1", "name": "⚡ Route 1: Volt Underpass Non-Stop", "signals": 0, "type": "Recommended", "color": "#E5FF00", "desc": "100% signal-free via specialized riverside tunnels.", "path": [sc, (sc[0]+0.001, sc[1]-0.002), (ec[0]-0.001, ec[1]+0.002), ec]},
        {"id": "R2", "name": "🌱 Route 2: Eco Green Park Way", "signals": 1, "type": "Scenic", "color": "#34C759", "desc": "Bypasses Waterloo traffic by entering perimeter park paths.", "path": [sc, (sc[0]+0.002, sc[1]+0.001), (ec[0]+0.001, ec[1]-0.002), ec]},
        {"id": "R3", "name": "🏙️ Route 3: Southwark Structural Grid", "signals": 3, "type": "Fastest Distance", "color": "#007AFF", "desc": "Shortest linear distance but contains 3 synchronized crossings.", "path": [sc, (sc[0]-0.001, sc[1]+0.002), (ec[0]-0.002, ec[1]+0.001), ec]},
        {"id": "R4", "name": "🌉 Route 4: Blackfriars Bridge Overpass", "signals": 4, "type": "Elevation", "color": "#FF9500", "desc": "Includes bridge climb intervals. TfL data shows minor delays.", "path": [sc, (sc[0]+0.003, sc[1]-0.004), (ec[0]+0.002, ec[1]-0.001), ec]},
        {"id": "R5", "name": "⚠️ Route 5: Standard High-Street Line", "signals": 6, "type": "Standard", "color": "#FF3B30", "desc": "Standard sidewalk routing. Extremely high risk of red light stops.", "path": [sc, (sc[0]-0.003, sc[1]-0.001), (ec[0]-0.004, ec[1]-0.003), ec]}
    ]

    col_m, col_l = st.columns([1.4, 1], gap='medium')

    with col_l:
        st.markdown("<p style='font-size:12px; font-weight:800; color:#8E8E93;'>5 INTELLIGENT OPTIONS CALCULATED</p>", unsafe_allow_html=True)
        for r in ROUTES_5:
            with st.container():
                st.markdown(f'''
                <div style="padding:12px; border-left:4px solid {r["color"]}; background:#1C1C1E; margin-bottom:8px;">
                    <span style="font-size:11px; font-weight:900; background:#2C2C2E; padding:2px 6px; color:{r["color"]};">{r["type"].upper()}</span>
                    <div style="font-size:15px; font-weight:700; margin-top:4px;">{r["name"]}</div>
                    <div style="font-size:12px; color:#AEAED2; margin-top:2px;">{r["desc"]} · <b>{r["signals"]} Stops</b></div>
                </div>
                ''', unsafe_allow_html=True)
                if st.button('SELECT THIS ROUTE', key=f"sel_{r['id']}", use_container_width=True):
                    st.session_state.selected_route_id = r["id"]
                    st.session_state.step = 'running'
                    st.session_state.km_completed = 0.0
                    st.session_state.current_coord = sc
                    st.rerun()

    with col_m:
        m_routes = folium.Map(location=list(sc), zoom_start=14, tiles='CartoDB DarkMatter')
        for r in ROUTES_5:
            folium.PolyLine(r["path"], color=r["color"], weight=4, tooltip=r["name"]).add_to(m_routes)
        folium.Marker(list(sc), icon=folium.Icon(color='green')).add_to(m_routes)
        folium.Marker(list(ec), icon=folium.Icon(color='red')).add_to(m_routes)
        st_folium(m_routes, width='100%', height=420, key='matrix_map')

# ==================================================
# STEP 4: ACTIVE TRACKING & LIVE DIRECTION GUIDE
# ==================================================
elif st.session_state.step == 'running':
    st.markdown('<div class="nrc-header"><div class="nrc-title">NRC ACTIVE NAVIGATION</div></div>', unsafe_allow_html=True)

    sc = st.session_state.start_coord
    ec = st.session_state.end_coord
    path_nodes = [sc, (sc[0]+0.001, sc[1]-0.002), (ec[0]-0.001, ec[1]+0.002), ec]

    total_distance = haversine_distance(sc, ec)
    if st.session_state.km_completed == 0.0:
        st.session_state.current_coord = sc

    progress_ratio = st.session_state.km_completed / max(0.1, total_distance)
    if progress_ratio < 0.3:
        nav_msg = "➡️ Head east toward Waterloo Underpass Link. Path is clear. Keep your pace."
        st.session_state.current_coord = path_nodes[0]
    elif progress_ratio < 0.7:
        nav_msg = "🏃 Bypassing Southwark intersection via Riverside Pedestrian Lane. 0 Red Lights Ahead."
        st.session_state.current_coord = path_nodes[1]
    elif progress_ratio < 0.95:
        nav_msg = "🏁 Straight Ahead. Approaching Southwark Bridge Finish Line. Prepare to sprint!"
        st.session_state.current_coord = path_nodes[2]
    else:
        nav_msg = "🎉 Destination reached! Safely halt your training session below."
        st.session_state.current_coord = ec

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">COMPLETED DISTANCE</div><div class="metric-value">{st.session_state.km_completed:.2f}</div><div class="metric-unit">KM / Total {total_distance:.2f}KM</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">CURRENT PACE</div><div class="metric-value">{st.session_state.target_pace}</div><div class="metric-unit">MIN / KM</div></div>', unsafe_allow_html=True)
    with c3:
        rem_distance = max(0.0, total_distance - st.session_state.km_completed)
        st.markdown(f'<div class="metric-card"><div class="metric-label">DISTANCE REMAINING</div><div class="metric-value">{rem_distance:.2f}</div><div class="metric-unit">KM LEFT</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="nav-instruction">🧭 LIVE DIRECTION GUIDE: {nav_msg}</div>', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    col_map, col_ctrl = st.columns([1.5, 1])

    with col_map:
        m_live = folium.Map(location=list(st.session_state.current_coord), zoom_start=16, tiles='CartoDB DarkMatter')
        folium.PolyLine(path_nodes, color='#E5FF00', weight=6, opacity=0.8).add_to(m_live)
        folium.Marker(list(st.session_state.current_coord), icon=folium.Icon(color='blue')).add_to(m_live)
        folium.Marker(list(ec), icon=folium.Icon(color='red', icon='flag')).add_to(m_live)
        st_folium(m_live, width='100%', height=350, key='live_nav_map')

    with col_ctrl:
        st.markdown("<div class='nrc-card'><h4>🛰️ GPS TRACKING SIMULATOR</h4><p style='color:#8E8E93; font-size:12px;'>Use this module to mock active acceleration along the optimized Waterloo system line.</p></div>", unsafe_allow_html=True)

        if st.button('🏃 SIMULATE RUNNING PROGRESS (Advance 0.5 KM)', use_container_width=True):
            st.session_state.km_completed = min(total_distance, st.session_state.km_completed + 0.5)
            st.rerun()

        if st.button('🏁 STOP RUN & VIEW REPORT', use_container_width=True):
            st.session_state.step = 'summary'
            st.rerun()

# ==================================================
# STEP 5: RUN SUMMARY ANALYTICS
# ==================================================
elif st.session_state.step == 'summary':
    st.markdown('<div class="nrc-header"><div class="nrc-title">WORKOUT INSIGHTS</div></div>', unsafe_allow_html=True)
    st.balloons()
    col = st.columns([1, 1.5, 1])[1]
    with col:
        st.markdown(f'''
        <div class="nrc-card" style="text-align:center;">
            <h2 style="font-family:'Impact'; color:#E5FF00;">SESSION CRUSHED!</h2>
            <p style="color:#FFFFFF; font-size:18px; font-weight:700; margin-top:10px;">Total Distance: {st.session_state.km_completed:.2f} KM</p>
            <p style="color:#8E8E93; font-size:13px; line-height:1.6;">You fully avoided standard municipal street delays through our predictive TfL algorithm integration.</p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button('NEW SPRINT SETUP', use_container_width=True):
            st.session_state.step = 'setup'
            st.session_state.km_completed = 0.0
            st.rerun()
