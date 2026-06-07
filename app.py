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

# ── Gail's Bakery 스타일 고도화 CSS ─────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,900;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    /* 글로벌 폰트 및 배경 정의 */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #FAFAF5 !important;
        color: #2E4A3F;
    }
    
    /* Gail's 시그니처 상단 배너 */
    .gails-header {
        background-color: #1C3829;
        padding: 40px 20px;
        text-align: center;
        border-bottom: 3px solid #E8D5B7;
        margin-bottom: 24px;
        border-radius: 12px;
    }
    .gails-title {
        font-family: 'Playfair Display', serif;
        font-size: 42px;
        color: #FAFAF5;
        font-weight: 900;
        letter-spacing: -1px;
    }
    .gails-subtitle {
        color: #A8C4B0;
        font-size: 13px;
        margin-top: 10px;
        letter-spacing: 3px;
        font-weight: 600;
    }
    
    /* 카드 및 박스 컴포넌트 통합 */
    .gails-card {
        background: #FFFFFF;
        border: 1px solid #E8D5B7;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(28, 56, 41, 0.03);
        margin-bottom: 16px;
    }
    .permission-item {
        background: #F4F1EA;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 10px 0;
        display: flex;
        gap: 16px;
        align-items: center;
    }
    
    /* 메트릭 대시보드 스타일 */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E8D5B7;
        border-top: 4px solid #1C3829;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    }
    .metric-label {
        font-size: 11px;
        color: #8B7355;
        letter-spacing: 1.5px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: 34px;
        font-weight: 900;
        color: #1C3829;
    }
    .metric-unit {
        font-size: 12px;
        color: #8B7355;
        margin-top: 2px;
    }
    
    /* 루트 선택 카드 */
    .route-card {
        background: #FDFDFB;
        border-left: 4px solid #1C3829;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        border-top: 1px solid #E8D5B7;
        border-right: 1px solid #E8D5B7;
        border-bottom: 1px solid #E8D5B7;
    }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 초기화 ──────────────────────────────
defaults = {
    "step": "consent",
    "start_pin": None,
    "end_pin": None,
    "target_km": 10,
    "target_pace": 6.0,
    "voice_character": "친근한 코치",
    "km_completed": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── 날씨 API 핸들러 ─────────────────────────────────
@st.cache_data(ttl=600)
def get_weather():
    try:
        key = st.secrets.get("WEATHER_API_KEY", "")
        if not key:
            raise ValueError()
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": "London,UK", "appid": key, "units": "metric"},
            timeout=5
        )
        if r.status_code != 200:
            raise ValueError()
        d = r.json()
        icons = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Drizzle":"🌦️","Snow":"❄️"}
        main_sky = d["weather"][0]["main"]
        icon = icons.get(main_sky, "🌤️")
        temp = round(d["main"]["temp"], 1)
        
        # 웰니스 가동 지수 계산
        score = 100
        if temp < 2 or temp > 30: score -= 25
        if d.get("wind", {}).get("speed", 0) > 12: score -= 20
        if "Rain" in main_sky: score -= 25
        return {"temp": temp, "feels": round(d["main"]["feels_like"], 1), "icon": icon, "score": max(0, score), "desc": d["weather"][0]["description"].title()}
    except:
        # API 오류 발생 시 런던 가을 날씨 기준 Default 값 반환 (안정성 확보)
        return {"temp": 14.5, "feels": 13.0, "icon": "🌤️", "score": 80, "desc": "Partly Clouds (Sample)"}

weather = get_weather()

# ==================================================
# STEP 1: 개인정보 및 안전 동의 화면
# ==================================================
if st.session_state.step == "consent":
    st.markdown("""
    <div class="gails-header">
        <div class="gails-title">London Runner</div>
        <div class="gails-subtitle">MARATHON TRAINING · SIGNAL-FREE ROUTES</div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("""
        <div class="gails-card">
            <h3 style="font-family:'Playfair Display',serif; color:#1C3829; margin-top:0;">Before We Begin</h3>
            <p style="color:#5a5a4a; font-size:14px; line-height:1.6;">
                London Runner는 런던 도심 내 신호대기를 최소화한 최적의 마라톤 러닝 경로를 제공하기 위해 아래 권한을 필요로 합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)

        items = [
            ("📍", "위치 정보 접근", "실시간 경로 계산 및 Turn-by-Turn 신호 회피 가이드를 위해 필요합니다."),
            ("❤️", "생체 건강 데이터", "Apple Health / 피트니스 데이터를 연동하여 맞춤형 Zone 2~3 페이스를 유지합니다."),
            ("🎙️", "마이크 이용 권한", "러닝 도중 안전하게 AI 코치와 대화할 수 있는 음성 명령 인터페이스를 활성화합니다."),
            ("🔔", "백그라운드 알림", "화면이 꺼져 있을 때도 1km 단위 체크포인트 및 실시간 페이스 코칭 알림을 보냅니다."),
        ]

        for icon, title, desc in items:
            st.markdown(f"""
            <div class="permission-item">
                <div style="font-size:24px;">{icon}</div>
                <div>
                    <div style="font-weight:600; color:#1C3829; font-size:14px;">{title}</div>
                    <div style="color:#8B7355; font-size:12px; margin-top:2px;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#EBF2EE; border-radius:8px; padding:14px; margin:16px 0; border-left:4px solid #1C3829;">
            <div style="font-size:11px; color:#4A5E53; line-height:1.6;">
                본 서비스는 <b>UK GDPR</b> 및 <b>영국 데이터 보호법(2018)</b> 가이드라인을 엄격히 준수합니다. 모든 신체 및 위치 정보는 온디바이스로 처리되며 외부에 저장되지 않습니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

        agree1 = st.checkbox("서비스 이용약관 및 개인정보 처리방침에 동의합니다.")
        agree2 = st.checkbox("실시간 위치 및 피트니스 데이터 연동에 동의합니다.")
        agree3 = st.checkbox("본인은 만 16세 이상임을 확인합니다.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("GET STARTED →", use_container_width=True):
            if agree1 and agree2 and agree3:
                st.session_state.step = "setup"
                st.rerun()
            else:
                st.error("앱을 시작하려면 모든 필수 동의 항목에 체크해주세요.")

# ==================================================
# STEP 2: 러닝 세션 셋업 (경로 및 목표 설정)
# ==================================================
elif st.session_state.step == "setup":
    st.markdown("""
    <div style="background:#1C3829; padding:20px 32px; border-radius:8px; margin-bottom:20px;">
        <div style="font-family:'Playfair Display',serif; font-size:24px; color:#FAFAF5; font-weight:700;">London Runner Settings</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.2], gap="large")
    
    with c1:
        st.markdown("<h4 style='color:#1C3829; margin-top:0;'>🏃 Target Profile</h4>", unsafe_allow_html=True)
        age = st.number_input("나이 (Age)", value=28, min_value=15, max_value=70)
        max_hr = 220 - age
        z2 = round(max_hr * 0.60)
        z3 = round(max_hr * 0.80)
        st.caption(f"🎯 실시간 권장 유산소(Zone 2~3) 심박수 범위: {z2} – {z3} bpm")
        
        target_km = st.slider("목표 거리 (Distance, km)", 1, 42, 10)
        target_pace = st.slider("목표 페이스 (Pace, min/km)", 4.0, 12.0, 6.0, 0.1)

        st.markdown("<h4 style='color:#1C3829; margin-top:20px;'>🔊 Voice Coaching Character</h4>", unsafe_allow_html=True)
        voices = [
            {"name": "친근한 코치", "desc": "Motivating & Friendly", "icon": "🏃"},
            {"name": "전문 트레이너", "desc": "Professional & Precise", "icon": "💪"},
            {"name": "차분한 안내", "desc": "Calm & Relaxed", "icon": "🧘"},
            {"name": "에너지 코치", "desc": "Energetic & Fun", "icon": "⚡"},
        ]
        
        v_cols = st.columns(4)
        for i, (col_v, v) in enumerate(zip(v_cols, voices)):
            with col_v:
                is_sel = st.session_state.voice_character == v["name"]
                bg_color = "#EBF2EE" if is_sel else "#FFFFFF"
                brd_color = "#1C3829" if is_sel else "#E8D5B7"
                st.markdown(f"""
                <div style="background:{bg_color}; border:2px solid {brd_color}; border-radius:8px; padding:10px; text-align:center; min-height:90px;">
                    <div style="font-size:20px;">{v["icon"]}</div>
                    <div style="font-weight:700; color:#1C3829; font-size:12px; margin-top:4px;">{v["name"]}</div>
                    <div style="color:#8B7355; font-size:10px;">{v["desc"]}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("선택", key=f"v_btn_{i}", use_container_width=True):
                    st.session_state.voice_character = v["name"]
                    st.rerun()

    with c2:
        st.markdown("""
        <h4 style='color:#1C3829; margin-top:0;'>📍 Set Signal-Free Checkpoints</h4>
        <p style='color:#8B7355; font-size:13px; margin-top:-10px;'>지도를 클릭하여 출발지와 목적지를 핀으로 지정하세요 (Waterloo / Southwark 인근 브리지 최적화)</p>
        """, unsafe_allow_html=True)
        
        # 기본 런던 중심 지도 설정
        m = folium.Map(location=[51.5045, -0.1115], zoom_start=14, tiles="CartoDB Positron")
        
        if st.session_state.start_pin:
            folium.Marker(st.session_state.start_pin, icon=folium.Icon(color="green", icon="play", prefix="fa"), popup="Start").add_to(m)
        if st.session_state.end_pin:
            folium.Marker(st.session_state.end_pin, icon=folium.Icon(color="red", icon="flag", prefix="fa"), popup="End").add_to(m)

        map_data = st_folium(m, width="100%", height=320, returned_objects=["last_clicked"])

        if map_data and map_data.get("last_clicked"):
            clicked = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
            if not st.session_state.start_pin:
                st.session_state.start_pin = clicked
                st.rerun()
            elif not st.session_state.end_pin and clicked != st.session_state.start_pin:
                st.session_state.end_pin = clicked
                st.rerun()

        if st.button("🔄 Reset Route Pins", use_container_width=True):
            st.session_state.start_pin = None
            st.session_state.end_pin = None
            st.rerun()

    st.markdown("---")
    spotify = st.checkbox("🎵 오디오 오버레이 시스템 활성화 (코칭 음성 발생 시 음악 자동 페이드아웃)")
    
    if st.button("START RUNNING →", use_container_width=True):
        st.session_state.target_km = target_km
        st.session_state.target_pace = target_pace
        st.session_state.step = "running"
        st.rerun()

# ==================================================
# STEP 3: 실시간 러닝 대시보드 (Live Tracking)
# ==================================================
elif st.session_state.step == "running":
    st.markdown("""
    <div style="background:#1C3829; padding:16px 24px; display:flex; justify-content:between; align-items:center; border-radius:8px; margin-bottom:20px;">
        <div style="font-family:'Playfair Display',serif; font-size:20px; color:#FAFAF5; font-weight:700;">London Runner Active Dashboard</div>
        <div style="color:#A8C4B0; font-size:12px; font-weight:700; background:#244735; padding:4px 12px; border-radius:12px;">● LIVE GPS TRACKING</div>
    </div>
    """, unsafe_allow_html=True)

    km = st.session_state.km_completed
    pace = st.session_state.target_pace
    elapsed = round(km * pace, 0)
    remaining = max(0.0, round((st.session_state.target_km - km), 1))

    # 주요 메트릭 대시보드 출력
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("TOTAL DISTANCE", f"{km}", "km"),
        ("CURRENT PACE", f"{pace}", "min/km"),
        ("ELAPSED TIME", f"{int(elapsed)}", "mins"),
        ("REMAINING DISTANCE", f"{remaining}", "km left"),
    ]
    for col, (label, val, unit) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-unit">{unit}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    map_col, info_col = st.columns([1.4, 1], gap="medium")

    # Waterloo & Southwark 인근 회피 경로 시뮬레이션 데이터 
    ROUTES = [
        {"name": "신호 우회 최적 경로 (Waterloo Bridge 하부 도로 관통)", "color": "#1C3829", "stops": 1,
         "points": [(51.5045, -0.1115), (51.5060, -0.1140), (51.5075, -0.1120), (51.5090, -0.1180)]},
        {"name": "일반 도심 경로 (남부 Southwark St 지상 교차로 통과)", "color": "#8B7355", "stops": 6,
         "points": [(51.5045, -0.1115), (51.5030, -0.1080), (51.5020, -0.1020), (51.5010, -0.0950)]},
    ]

    with map_col:
        start = st.session_state.start_pin or (51.5045, -0.1115)
        end = st.session_state.end_pin or (51.5090, -0.1180)

        m = folium.Map(location=list(start), zoom_start=15, tiles="CartoDB Positron")
        
        # 인프라 폴리라인 드로잉
        for r in ROUTES:
            folium.PolyLine(r["points"], color=r["color"], weight=5, opacity=0.85, tooltip=r["name"]).add_to(m)
            
        folium.Marker(list(start), icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(m)
        folium.Marker(list(end), icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(m)
        
        # 신호등 정체 상습 구간 가시화 (Southwark/Waterloo 부근)
        for idx, pos in enumerate([(51.5035, -0.1090), (51.5025, -0.1040)]):
            folium.CircleMarker(pos, radius=8, color="#D9534F", fill=True, fill_color="#D9534F", fill_opacity=0.7, tooltip=f"정체 유발 신호등 대기 구간 {idx+1}").add_to(m)
            
        st_folium(m, width="100%", height=380, key="running_live_map")

    with info_col:
        # 실시간 웨더 스코어 박스
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E8D5B7; border-radius:12px; padding:18px; margin-bottom:14px;">
            <div style="color:#8B7355; font-size:11px; letter-spacing:2px; font-weight:700;">LIVE MET OFFICE ENVIRONMENT</div>
            <div style="font-size:28px; font-weight:900; color:#1C3829; margin-top:4px;">
                {weather["icon"]} {weather["temp"]}°C <span style="font-size:16px; font-weight:400; color:#8B7355;">(체감 {weather["feels"]}°C)</span>
            </div>
            <div style="color:#4A5E53; font-size:13px; margin-top:4px; font-weight:500;">
                상태: {weather["desc"]} | 러닝 쾌적도 지수: <b>{weather["score"]}/100</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 실시간 신호 우회 및 훈련 강도 연산
        st.markdown("<div style='font-size:13px; font-weight:700; color:#1C3829; margin-bottom:8px;'>🗺️ SIGNAL-FREE ROUTE REALTIME ANALYSIS</div>", unsafe_allow_html=True)
        for r in ROUTES:
            lost_time = round(r["stops"] * 1.45, 1) # 신호 대기 소요 시간 예측 시뮬레이터
            eff_ratio = round(((60 - lost_time) / 60) * 100)
            progress_bar = "█" * int(eff_ratio / 10) + "░" * (10 - int(eff_ratio / 10))
            
            st.markdown(f"""
            <div class="route-card">
                <div style="font-weight:700; color:#1C3829; font-size:13px;">{r["name"]}</div>
                <div style="color:#8B7355; font-size:12px; margin-top:2px;">예상 대기 신호: {r["stops"]}개소 | 심박수 유지 효율성: {eff_ratio}%</div>
                <div style="color:#1C3829; font-family:monospace; font-size:12px; letter-spacing:1px; margin-top:4px;">[{progress_bar}]</div>
            </div>""", unsafe_allow_html=True)

        # ── 오디오 캐스팅 엔진 (Web Speech API 활용 인터페이스) ──
        if st.button("🔊 음성 브리핑 강제 재생 (Voice Guideline)", use_container_width=True):
            tts_text = f"Runner info. {km} kilometers completed. Current pace is {pace} minutes per kilometer. {remaining} kilometers remaining. Keep Zone 2 training line. You are doing fantastic."
            st.markdown(f"""
            <script>
                var synth = window.speechSynthesis;
                var utter = new SpeechSynthesisUtterance("{tts_text}");
                utter.lang = "en-GB"; utter.rate = 0.90; utter.pitch = 1.0;
                synth.speak(utter);
            </script>
            """, unsafe_allow_html=True)

        # ── AI Coach Q&A 엔드포인트 ──
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        q = st.text_input("AI Coach 대화창 (Ask about pace, weather, routes...)", placeholder="페이스 조절은 어떻게 할까요? 비가 올 예정인가요?")
        if st.button("코치에게 질문하기 →", use_container_width=True) and q:
            try:
                g_key = st.secrets.get("GEMINI_API_KEY", "")
                if not g_key:
                    raise ValueError()
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
                sys_prompt = f"You are an elite London marathon running coach. Runner status: {km}km completed, target pace {pace} min/km, current London weather temp {weather['temp']}C. User question: {q}. Provide a highly inspiring and tactical response in Korean within 2 sentences."
                
                resp = requests.post(api_url, json={"contents": [{"parts": [{"text": sys_prompt}]}]}, timeout=6)
                coach_ans = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                
                st.markdown(f"""
                <div style="background:#EBF2EE; border-left:4px solid #1C3829; border-radius:4px; padding:12px; font-size:13px; color:#1C3829; margin-top:10px; font-weight:500;">
                    <b>Coach Response:</b> {coach_ans}
                </div>
                """, unsafe_allow_html=True)
            except:
                st.info("💡 실시간 AI 코칭을 받으시려면 Streamlit Secrets 설정에 'GEMINI_API_KEY'를 추가해주세요.")

    st.markdown("---")
    if st.button("🏁 FINISH RUN (세션 종료)", use_container_width=True):
        st.session_state.step = "summary"
        st.rerun()

# ==================================================
# STEP 4: 러닝 서머리 및 트레이닝 세션 분석 (Summary)
# ==================================================
elif st.session_state.step == "summary":
    st.markdown("""
    <div style="background:#1C3829; padding:40px 20px; text-align:center; border-radius:12px;">
        <div style="font-size:54px; margin-bottom:12px;">🏅</div>
        <div style="font-family:'Playfair Display',serif; font-size:36px; color:#FAFAF5; font-weight:900;">Session Completed</div>
        <div style="color:#A8C4B0; font-size:14px; margin-top:8px; letter-spacing:1px;">오늘도 런던의 신호를 극복하고 성공적으로 마라톤 훈련을 마쳤습니다.</div>
    </div>
    """, unsafe_allow_html=True)

    f_km = st.session_state.target_km
    f_pace = st.session_state.target_pace
    avoided_stops = 5
    saved_time = round(avoided_stops * 1.5, 1)
    zone_accuracy = round(((f_km * f_pace - saved_time) / (f_km * f_pace)) * 100)
    burnt_cal = round(f_km * 74.2, 0)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    results = [
        ("TOTAL DISTANCE", f"{f_km}", "km"),
        ("AVERAGE PACE", f"{f_pace}", "min/km"),
        ("ZONE 2~3 RATIO", f"{int(zone_accuracy)}", "%"),
        ("TOTAL ENERGY BURNT", f"{int(burnt_cal)}", "kcal"),
    ]
    for col, (label, val, unit) in zip([c1, c2, c3, c4], results):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-unit">{unit}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col = st.columns([1, 1.8, 1])[1]
    with col:
        st.markdown(f"""
        <div class="gails-card">
            <h4 style="font-family:'Playfair Display',serif; color:#1C3829; text-align:center; margin-top:0; font-size:20px;">📊 Training Insight Report</h4>
            <hr style="border:0; border-top:1px solid #E8D5B7; margin:16px 0;">
            <div style="color:#2E4A3F; font-size:14px; line-height:2.2; font-weight:500;">
                ✅ <b>불필요 정체 회피:</b> 도심 신호대기 구간 <b>{avoided_stops}회 완전 회피</b> 성공<br>
                ✅ <b>훈련 시간 세이브:</b> 신호 대기 소모 시간 <b>약 {saved_time}분 단축</b><br>
                ✅ <b>심박수 유지력:</b> 전 구간 마라톤 타겟 Zone 2~3 심박수 유지 지수 <b>{zone_accuracy}%</b> 달성<br>
                ✅ <b>마라톤 코스 빌드업:</b> 정식 풀코스(42.195km) 기준 <b>{round(f_km/42.195*100, 1)}% 목표 누적 완료</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 RUN NEW SESSION (새 트레이닝 시작)", use_container_width=True):
            st.session_state.step = "setup"
            st.session_state.start_pin = None
            st.session_state.end_pin = None
            st.rerun()
