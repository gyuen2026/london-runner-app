import streamlit as st
import folium
import requests
from streamlit_folium import st_folium
import math
import time

st.set_page_config(
    page_title='NRC x London Runner Pro',
    page_icon='🏃',
    layout='wide',
    initial_sidebar_state='collapsed'
)

# ── NIKE RUN CLUB (NRC) PREMIUM DARK STYLING ─────────────────────
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
        padding: 25px 20px;
        text-align: center;
        border-bottom: 4px solid #E5FF00;
        margin-bottom: 20px;
    }
    .nrc-title {
        font-family: 'Impact', sans-serif;
        font-size: 42px;
        color: #E5FF00;
        letter-spacing: 2px;
    }

    .nrc-card {
        background: #1C1C1E;
        border: 1px solid #2C2C2E;
        padding: 24px;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    .metric-card {
        background: #1C1C1E;
        border-top: 4px solid #E5FF00;
        padding: 20px;
        text-align: center;
        border-radius: 4px;
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
    .metric-unit {
        font-size: 12px;
        color: #8E8E93;
    }

    /* Countdown UX Overlay */
    .countdown-box {
        text-align: center;
        background: #000000;
        padding: 50px;
        border: 3px solid #E5FF00;
        border-radius: 12px;
        margin: 40px auto;
        max-width: 500px;
    }
    .countdown-num {
        font-family: 'Impact', sans-serif;
        font-size: 100px;
        color: #E5FF00;
        animation: pulse 1s infinite;
    }

    .nav-instruction {
        background: #000000;
        border-left: 6px solid #007AFF;
        padding: 15px;
        font-size: 16px;
        font-weight: 700;
        color: #E5FF00;
        margin-top: 10px;
        border-radius: 4px;
    }

    /* Analytics Comparison Cards */
    .vs-box {
        background: #2C2C2E;
        border-radius: 6px;
        padding: 15px;
        margin-top: 10px;
    }
</style>
''', unsafe_allow_html=True)

# ── SESSION STATE INITIALIZATION ──────────────────────────────
defaults = {
    'step': 'location_consent',
    'start_coord': (51.5045, -0.1115), 
    'end_coord': (51.5090, -0.1180),
    'start_name': 'Waterloo Station',
    'end_name': "Gail's Bakery Southwark",
    'target_pace': 6.0,
    'selected_route_id': None,
    'selected_route_name': "",
    'selected_route_signals': 0,
    'km_completed': 0.0,
    'current_coord': (51.5045, -0.1115),
    'search_results_start': [],
    'search_results_end': [],
    'countdown_val': 3
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── REAL LOCATION GEOCODING ENGINE ─────────────────────
def get_location_suggestions(query):
    if not query: return []
    try:
        url = f'https://nominatim.openstreetmap.org/search?q={query},+London&format=json&limit=5'
        headers = {'User-Agent': 'NRC_London_Runner_Application_v6'}
        res = requests.get(url, headers=headers, timeout=5).json()

        suggestions = []
        for item in res:
            raw_name = item.get("display_name", "")
            parts = raw_name.split(",")
            short_name = f"{parts[0].strip()} ({parts[1].strip() if len(parts)>1 else ''})"
            suggestions.append({
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "name": short_name
            })
        return suggestions
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
# 1. 위치 정보 수집 동의 화면
# ==================================================
if st.session_state.step == 'location_consent':
    st.markdown('<div class="nrc-header"><div class="nrc-title">NIKE RUN CLUB</div></div>', unsafe_allow_html=True)
    col = st.columns([1, 1.8, 1])[1]
    with col:
        st.markdown('''
        <div class="nrc-card">
            <h2 style='font-family:Impact; color:#E5FF00;'>📍 STEP 1: LOCATION PERMISSION</h2>
            <p style="color:#FFFFFF; font-size:14px; margin-top:10px;">
                NRC 사용자의 실시간 이동 경로 확인 및 정밀한 러닝 트래킹 가이드를 위해 <b>GPS 위치 정보 수집</b> 동의가 필요합니다.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("AGREE & CONTINUE →", use_container_width=True):
            st.session_state.step = 'health_consent'
            st.rerun()

# ==================================================
# 2. 건강 정보 수집 동의 화면
# ==================================================
elif st.session_state.step == 'health_consent':
    st.markdown('<div class="nrc-header"><div class="nrc-title">NIKE RUN CLUB</div></div>', unsafe_allow_html=True)
    col = st.columns([1, 1.8, 1])[1]
    with col:
        st.markdown('''
        <div class="nrc-card">
            <h2 style='font-family:Impact; color:#E5FF00;'>❤️ STEP 2: HEALTH & BIOMETRIC DATA</h2>
            <p style="color:#FFFFFF; font-size:14px; margin-top:10px;">
                사용자의 페이스 조절 및 안전 관리를 위해 <b>실시간 심장 박동 수(Heart Rate) 및 생체 칼로리 소모 데이터</b>를 연동합니다.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("ACCEPT ALL & OPEN MAP →", use_container_width=True):
            st.session_state.step = 'setup'
            st.rerun()

# ==================================================
# 3. 도착지, 출발지 설정 화면 (구글맵 UI)
# ==================================================
elif st.session_state.step == 'setup':
    st.markdown('<div class="nrc-header"><div class="nrc-title">ROUTE CONFIGURATION</div></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2], gap='large')

    with c1:
        st.markdown("<h3 style='font-family:Impact; color:#E5FF00;'>📍 GOOGLE MAP UX SEARCH</h3>", unsafe_allow_html=True)

        # 출발지
        col_s1, col_b1 = st.columns([5, 1])
        with col_s1:
            start_q = st.text_input('출발지 입력', value=st.session_state.start_name)
        with col_b1:
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button('🔍', key='search_start_btn'):
                st.session_state.search_results_start = get_location_suggestions(start_q)
        if st.session_state.search_results_start:
            for idx, res in enumerate(st.session_state.search_results_start):
                if st.button(f"🏢 {res['name']}", key=f"src_{idx}", use_container_width=True):
                    st.session_state.start_coord = (res['lat'], res['lon'])
                    st.session_state.start_name = res['name']
                    st.session_state.search_results_start = []
                    st.rerun()

        # 도착지
        col_s2, col_b2 = st.columns([5, 1])
        with col_s2:
            end_q = st.text_input('도착지 입력', value=st.session_state.end_name)
        with col_b2:
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button('🔍', key='search_end_btn'):
                st.session_state.search_results_end = get_location_suggestions(end_q)
        if st.session_state.search_results_end:
            for idx, res in enumerate(st.session_state.search_results_end):
                if st.button(f"🏁 {res['name']}", key=f"dst_{idx}", use_container_width=True):
                    st.session_state.end_coord = (res['lat'], res['lon'])
                    st.session_state.end_name = res['name']
                    st.session_state.search_results_end = []
                    st.rerun()

        st.markdown("<hr style='border-color:#2C2C2E;'>", unsafe_allow_html=True)
        st.session_state.target_pace = st.slider('SET RUNNING PACE (MIN/KM)', 4.0, 9.0, float(st.session_state.target_pace), 0.1)

    with c2:
        st.markdown("<h3 style='font-family:Impact; color:#E5FF00;'>🗺️ MAP LOOKUP</h3>", unsafe_allow_html=True)
        st.info(f"출발: {st.session_state.start_name} ➡️ 도착: {st.session_state.end_name}")
        m_preview = folium.Map(location=list(st.session_state.start_coord), zoom_start=14, tiles='CartoDB DarkMatter')
        folium.Marker(list(st.session_state.start_coord), icon=folium.Icon(color='green', icon='play')).add_to(m_preview)
        folium.Marker(list(st.session_state.end_coord), icon=folium.Icon(color='red', icon='flag')).add_to(m_preview)
        st_folium(m_preview, width='100%', height=290, key='setup_preview_map')

    if st.button('GENERATE INTELLIGENT ROUTES →', use_container_width=True):
        st.session_state.step = 'route_selection'
        st.rerun()

# ==================================================
# 4. 추천 경로 리스트 화면 (5개 라열)
# ==================================================
elif st.session_state.step == 'route_selection':
    st.markdown('<div class="nrc-header"><div class="nrc-title">SELECT OPTIMAL SPRINT LINE</div></div>', unsafe_allow_html=True)
    sc, ec = st.session_state.start_coord, st.session_state.end_coord

    ROUTES_5 = [
        {"id": "R1", "name": "⚡ 추천 1: 런던 리버사이드 언더패스 프리패스 라인", "signals": 0, "type": "최적 최저정체", "color": "#E5FF00", "desc": "TfL 연동 신호 제로 구간. 페이스 연속 유지 확률 99%"},
        {"id": "R2", "name": "🌱 추천 2: 워털루 그린 파크 웨이 코스", "signals": 1, "type": "쾌적 우회", "color": "#34C759", "desc": "보행자 도심 숲 공원 내부 트랙 우회. 산소 농도 높음."},
        {"id": "R3", "name": "🏙️ 추천 3: 서더크 하이스트리트 리니어 그리드", "signals": 3, "type": "최단 거리 직선", "color": "#007AFF", "desc": "물리적 거리는 가장 짧으나 교차로 신호등 대기 리스크 존재."},
        {"id": "R4", "name": "🌉 추천 4: 블랙프라이어스 고도 브릿지 로드", "signals": 4, "type": "경사 업힐 고도", "color": "#FF9500", "desc": "다리 진입 업힐 바이브 구간 포함. 고강도 피트니스 훈련 특화."},
        {"id": "R5", "name": "⚠️ 추천 5: 시내 중심가 메인 스탠다드 로드", "signals": 6, "type": "신호등 최다 정체", "color": "#FF3B30", "desc": "도심 공사 구역 연동. 빈번한 신호 멈춤으로 페이스 다운 위험."}
    ]

    col_m, col_l = st.columns([1.3, 1], gap='medium')
    with col_l:
        st.markdown("<p style='font-size:12px; font-weight:800; color:#8E8E93;'>COMPUTED SMART 5-ROUTE MATRIX</p>", unsafe_allow_html=True)
        for r in ROUTES_5:
            with st.container():
                st.markdown(f'''
                <div style="padding:14px; border-left:5px solid {r["color"]}; background:#1C1C1E; margin-bottom:8px; border-radius:4px;">
                    <span style="font-size:10px; font-weight:900; background:#2C2C2E; padding:3px 7px; color:{r["color"]}; border-radius:3px;">{r["type"]}</span>
                    <div style="font-size:16px; font-weight:700; margin-top:6px;">{r["name"]}</div>
                    <div style="font-size:12px; color:#AEAED2; margin-top:2px;">신호등 {r["signals"]}개 돌파 예정</div>
                </div>
                ''', unsafe_allow_html=True)
                if st.button(f"{r['id']} 라인으로 훈련 시작", key=f"sel_{r['id']}", use_container_width=True):
                    st.session_state.selected_route_id = r["id"]
                    st.session_state.selected_route_name = r["name"]
                    st.session_state.selected_route_signals = r["signals"]
                    st.session_state.step = 'countdown'
                    st.session_state.countdown_val = 3
                    st.rerun()

    with col_m:
        m_routes = folium.Map(location=list(sc), zoom_start=14, tiles='CartoDB DarkMatter')
        # 더미 패스 렌더링
        folium.PolyLine([sc, (sc[0]+0.001, sc[1]-0.002), ec], color="#E5FF00", weight=5).add_to(m_routes)
        folium.Marker(list(sc), icon=folium.Icon(color='green')).add_to(m_routes)
        folium.Marker(list(ec), icon=folium.Icon(color='red')).add_to(m_routes)
        st_folium(m_routes, width='100%', height=450, key='matrix_map')

# ==================================================
# 5. NIKE RUN 고유 카운트다운 화면 (3, 2, 1)
# ==================================================
elif st.session_state.step == 'countdown':
    st.markdown('<div class="nrc-header"><div class="nrc-title">NIKE RUN CLUB</div></div>', unsafe_allow_html=True)

    # Streamlit 자동 상태 전이를 이용한 정적 타임 딜레이 시뮬레이션 카운트다운
    val = st.session_state.countdown_val

    st.markdown(f'''
    <div class="countdown-box">
        <p style="color:#8E8E93; font-weight:800; letter-spacing:2px; font-size:14px;">READY TO RUN</p>
        <div class="countdown-num">{val if val > 0 else "START!"}</div>
        <p style="color:#FFFFFF; font-size:13px; margin-top:10px;">스마트 페이스 트래킹 시스템 가동 중...</p>
    </div>
    ''', unsafe_allow_html=True)

    time.sleep(1.0)
    if st.session_state.countdown_val > 1:
        st.session_state.countdown_val -= 1
        st.rerun()
    else:
        st.session_state.step = 'running'
        st.session_state.km_completed = 0.0
        st.rerun()

# ==================================================
# 6. 실시간 자동 위치 & 페이스 트래킹 (러너 자동 무브먼트)
# ==================================================
elif st.session_state.step == 'running':
    st.markdown('<div class="nrc-header"><div class="nrc-title">ACTIVE TRACKING</div></div>', unsafe_allow_html=True)

    sc, ec = st.session_state.start_coord, st.session_state.end_coord
    total_distance = haversine_distance(sc, ec)

    # 버튼을 안 눌러도 페이지 새로고침 시 자동으로 0.35km씩 러너 이동 연출
    if st.session_state.km_completed < total_distance:
        st.session_state.km_completed = min(total_distance, st.session_state.km_completed + 0.35)

    progress_ratio = st.session_state.km_completed / max(0.01, total_distance)

    # 현재 실시간 노드 변위 연산
    lat_step = sc[0] + (ec[0] - sc[0]) * progress_ratio
    lon_step = sc[1] + (ec[1] - sc[1]) * progress_ratio
    st.session_state.current_coord = (lat_step, lon_step)

    if progress_ratio < 0.4:
        nav_msg = "➡️ [구간 안내] 교차 정체 구역 우회 성공. 한강 변 하부 언더패스 진입 중."
    elif progress_ratio < 0.8:
        nav_msg = "🏃 [페이스 안내] 타겟 스피드 리얼타임 동기화 매칭률 98%. 매우 안정적인 흐름입니다."
    else:
        nav_msg = "🎉 [도착 임박] 목표 지점이 가시거리에 잡혔습니다. 마지막 쿨다운 페이스를 준비하세요."

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">총 달린 거리</div><div class="metric-value">{st.session_state.km_completed:.2f}</div><div class="metric-unit">KM / {total_distance:.2f} KM</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">현재 스피드</div><div class="metric-value">{st.session_state.target_pace:.1f}</div><div class="metric-unit">MIN / KM</div></div>', unsafe_allow_html=True)
    with c3:
        # 실시간 가변 칼로리 수집 매핑 계산식
        calories = int(st.session_state.km_completed * 65)
        st.markdown(f'<div class="metric-card"><div class="metric-label">소모 칼로리 (실시간)</div><div class="metric-value">{calories}</div><div class="metric-unit">KCAL</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="nav-instruction">🧭 Real-Time Guide: {nav_msg}</div>', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    m_live = folium.Map(location=list(st.session_state.current_coord), zoom_start=16, tiles='CartoDB DarkMatter')
    folium.PolyLine([sc, ec], color='#E5FF00', weight=6).add_to(m_live)
    folium.Marker(list(st.session_state.current_coord), icon=folium.Icon(color='blue', icon='user', prefix='fa')).add_to(m_live)
    folium.Marker(list(ec), icon=folium.Icon(color='red')).add_to(m_live)
    st_folium(m_live, width='100%', height=340, key='live_nav_map')

    st.markdown('<br>', unsafe_allow_html=True)
    # 러너가 수동 조작하지 않아도 트래킹이 계속 진행되거나 즉시 종료 보고서로 넘어갈 수 있도록 흐름 유도
    if st.session_state.km_completed >= total_distance:
        if st.button('🏁 훈련 완료 - 분석 리포트 확인하기', use_container_width=True):
            st.session_state.step = 'summary'
            st.rerun()
    else:
        if st.button('👟 위치 GPS 동기화 갱신하기 (다음 지점 무브)', use_container_width=True):
            st.rerun()

# ==================================================
# 7. 완주 후 결과 분석 리포트 (최악의 경로 대비 매트릭스 피드백)
# ==================================================
elif st.session_state.step == 'summary':
    st.markdown('<div class="nrc-header"><div class="nrc-title">WORKOUT ANALYTICS SUMMARY</div></div>', unsafe_allow_html=True)
    st.balloons()

    sc, ec = st.session_state.start_coord, st.session_state.end_coord
    final_dist = haversine_distance(sc, ec)
    final_calories = int(final_dist * 67)
    avg_speed = round(60 / st.session_state.target_pace, 1) # 시속계산

    # 최악의 경로(신호등 6개 정체 코스) 대비 인텔리전트 추천 경로의 세이브 가치 환산
    saved_minutes = int(st.session_state.selected_route_signals * 1.5 + 2)
    bpm_stabilization = "142 BPM (안정)" if st.session_state.selected_route_signals <= 1 else "168 BPM (신호대기 급상승 부하)"

    col_main = st.columns([1, 2, 1])[1]
    with col_main:
        st.markdown(f'''
        <div class="nrc-card">
            <h2 style="font-family:'Impact'; color:#E5FF00; text-align:center; margin-bottom:15px;">🎉 RUN COMPLETE! 🎉</h2>
            <p style="text-align:center; color:#8E8E93; font-size:13px;">오늘도 완주해냈습니다. 러너님의 데이터 분석 결과입니다.</p>
            <hr style="border-color:#2C2C2E;">

            <table style="width:100%; color:#FFF; font-size:15px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #2C2C2E;"><td style="padding:10px 0; color:#8E8E93;">총 달린 거리</td><td style="text-align:right; font-weight:700; color:#E5FF00;">{final_dist:.2f} KM</td></tr>
                <tr style="border-bottom: 1px solid #2C2C2E;"><td style="padding:10px 0; color:#8E8E93;">평균 스피드</td><td style="text-align:right; font-weight:700;">시속 {avg_speed} km/h</td></tr>
                <tr style="border-bottom: 1px solid #2C2C2E;"><td style="padding:10px 0; color:#8E8E93;">소모 에너지</td><td style="text-align:right; font-weight:700; color:#FF9500;">{final_calories} KCAL</td></tr>
                <tr style="border-bottom: 1px solid #2C2C2E;"><td style="padding:10px 0; color:#8E8E93;">설정 목표 페이스</td><td style="text-align:right; font-weight:700;">{st.session_state.target_pace} MIN/KM</td></tr>
            </table>

            <div class="vs-box">
                <h4 style="color:#FF3B30; font-family:'Inter'; font-weight:800; margin-bottom:5px;">⚠️ 최악의 우회 경로(Standard Line) 대비 가치 분석</h4>
                <p style="font-size:13px; color:#AEAED2; line-height:1.5;">
                    일반 도심 경로를 선택했을 경우 총 6회의 신호등 급정거 마찰이 야기되었으나, 오늘 선택하신 <b>[{st.session_state.selected_route_name}]</b> 코스를 통해 다음 성과를 달성했습니다.
                </p>
                <ul style="font-size:13px; color:#FFFFFF; padding-left:20px; margin-top:8px;">
                    <li>🕒 <b>시간 단축 효과:</b> 일반 경로 대비 약 <b style="color:#E5FF00;">{saved_minutes}분 빠른</b> 골인 성공</li>
                    <li>❤️ <b>심장 박동수 유지:</b> 가속/감속 스트레스 차단으로 평균 심박수 <b style="color:#34C759;">{bpm_stabilization}</b> 제어 완료</li>
                </ul>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        if st.button('새로운 러닝 라인 세팅하기 🔄', use_container_width=True):
            st.session_state.step = 'setup'
            st.session_state.km_completed = 0.0
            st.rerun()
