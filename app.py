
import streamlit as st
import folium
import requests
import json
from streamlit_folium import st_folium

st.set_page_config(
    page_title="London Runner",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Nike Run 스타일 CSS ─────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');

    .stApp { background-color: #0a0a0a; color: #ffffff; font-family: 'Inter', sans-serif; }
    .main .block-container { padding: 1rem 2rem; max-width: 100%; }
    div[data-testid="stSidebar"] { background-color: #111111; }
    h1,h2,h3 { color: #ffffff; font-weight: 900; letter-spacing: -1px; }
    .stButton>button {
        background: #00FF88; color: #000000;
        font-weight: 700; border: none; border-radius: 50px;
        padding: 12px 32px; font-size: 16px; width: 100%;
    }
    .stButton>button:hover { background: #00cc6a; }
    hr { border-color: #222; }
    .stMetric { background: #111; border-radius: 12px; padding: 16px; }
    label { color: #888 !important; font-size: 12px !important; }
    .stSlider>div>div { background: #00FF88; }
</style>
""", unsafe_allow_html=True)

# ── 상태 관리 ─────────────────────────────────────
if "running" not in st.session_state:
    st.session_state.running = False
if "km_completed" not in st.session_state:
    st.session_state.km_completed = 0

# ── 날씨 ──────────────────────────────────────────
@st.cache_data(ttl=600)
def get_weather():
    try:
        key = st.secrets.get("WEATHER_API_KEY", "")
        if not key:
            raise ValueError("no key")
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": "London,UK", "appid": key, "units": "metric"},
            timeout=5
        )
        d = r.json()
        temp = d["main"]["temp"]
        feels = d["main"]["feels_like"]
        wind = d["wind"]["speed"]
        hum = d["main"]["humidity"]
        desc = d["weather"][0]["description"]
        icons = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Drizzle":"🌦️","Snow":"❄️"}
        icon = icons.get(d["weather"][0]["main"], "🌤️")
        score = 100
        if temp < 2 or temp > 28: score -= 25
        if wind > 12: score -= 20
        if hum > 85: score -= 10
        if "rain" in desc.lower(): score -= 25
        return {"temp": round(temp,1), "feels": round(feels,1),
                "wind": wind, "hum": hum, "icon": icon,
                "desc": desc, "score": max(0,score)}
    except:
        return {"temp": 14, "feels": 12, "wind": 4, "hum": 70,
                "icon": "🌤️", "desc": "샘플", "score": 75}

weather = get_weather()

# ── AI 음성 Q&A (Gemini) ──────────────────────────
def ask_gemini(question, context):
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if not key:
            return "Gemini API 키가 없습니다. Streamlit Secrets에 추가해주세요."
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}"
        prompt = f"""
        당신은 런던 마라톤 러닝 코치입니다.
        현재 러너 상태:
        - 현재 페이스: {context["pace"]}분/km
        - 완료 거리: {context["km"]}km
        - 날씨: {context["weather"]}°C {context["weather_desc"]}
        - 심박 Zone: {context["zone"]}
        - 신호등 없는 루트 사용 중: {context["route"]}

        러너 질문: {question}

        30초 이내에 읽을 수 있는 짧고 실용적인 답변을 해주세요.
        한국어로 답변하세요.
        """
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(url, json=body, timeout=10)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"AI 연결 오류: {str(e)}"

# ── 사이드바 설정 ──────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 러닝 설정")
    age = st.number_input("나이", value=28, min_value=15, max_value=70)
    max_hr = 220 - age
    z2_min = round(max_hr * 0.60)
    z3_max = round(max_hr * 0.80)
    st.caption(f"목표 Zone 2~3: {z2_min}~{z3_max} bpm")
    st.divider()
    pace = st.slider("현재 페이스 (분/km)", 4.0, 12.0, 6.33, 0.1)
    st.divider()
    st.markdown("**출발지**")
    s_lat = st.number_input("위도", value=51.5074, format="%.4f")
    s_lon = st.number_input("경도", value=-0.1278, format="%.4f")
    st.markdown("**도착지**")
    e_lat = st.number_input("위도 ", value=51.5155, format="%.4f")
    e_lon = st.number_input("경도 ", value=-0.0922, format="%.4f")

# ── 헤더 ──────────────────────────────────────────
col_title, col_weather = st.columns([3,1])
with col_title:
    st.markdown("# 🏃 LONDON RUNNER")
    st.markdown(f"##### 마라톤 훈련 최적 루트 · Zone {z2_min}~{z3_max} bpm 유지")
with col_weather:
    st.markdown(f"""
    <div style="background:#111;border-radius:12px;padding:16px;text-align:center;margin-top:8px;">
        <div style="font-size:32px;">{weather["icon"]}</div>
        <div style="font-size:28px;font-weight:900;color:#fff;">{weather["temp"]}°C</div>
        <div style="color:#888;font-size:12px;">체감 {weather["feels"]}°C</div>
        <div style="color:#888;font-size:12px;">💨 {weather["wind"]}m/s</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── 주요 지표 카드 (Nike 스타일) ─────────────────
c1,c2,c3,c4 = st.columns(4)
zone_score = round((1 - 4*0.0225)*100)

with c1:
    st.markdown(f"""
    <div style="background:#111;border-radius:16px;padding:20px;text-align:center;">
        <div style="color:#888;font-size:11px;letter-spacing:2px;">PACE</div>
        <div style="font-size:42px;font-weight:900;color:#fff;">{pace}</div>
        <div style="color:#888;font-size:12px;">분/km</div>
    </div>""", unsafe_allow_html=True)

with c2:
    run_score_color = "#00FF88" if zone_score>=80 else "#FFD700" if zone_score>=60 else "#FF6B6B"
    st.markdown(f"""
    <div style="background:#111;border-radius:16px;padding:20px;text-align:center;">
        <div style="color:#888;font-size:11px;letter-spacing:2px;">ZONE 유지율</div>
        <div style="font-size:42px;font-weight:900;color:{run_score_color};">{zone_score}%</div>
        <div style="color:#888;font-size:12px;">훈련 효율</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div style="background:#111;border-radius:16px;padding:20px;text-align:center;">
        <div style="color:#888;font-size:11px;letter-spacing:2px;">목표 심박</div>
        <div style="font-size:42px;font-weight:900;color:#FF6B6B;">{z2_min}~{z3_max}</div>
        <div style="color:#888;font-size:12px;">bpm · Zone 2~3</div>
    </div>""", unsafe_allow_html=True)

with c4:
    w_color = "#00FF88" if weather["score"]>=75 else "#FFD700" if weather["score"]>=50 else "#FF6B6B"
    st.markdown(f"""
    <div style="background:#111;border-radius:16px;padding:20px;text-align:center;">
        <div style="color:#888;font-size:11px;letter-spacing:2px;">달리기 적합도</div>
        <div style="font-size:42px;font-weight:900;color:{w_color};">{weather["score"]}</div>
        <div style="color:#888;font-size:12px;">/100</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── 지도 + 루트 비교 ──────────────────────────────
ROUTES = [
    {"name":"최적 루트","color":"#00FF88","stops":4,
     "points":[(51.5074,-0.1278),(51.5065,-0.1229),(51.5055,-0.1090),(51.5033,-0.0980),(51.5155,-0.0922)]},
    {"name":"중간 루트","color":"#FFD700","stops":8,
     "points":[(51.5074,-0.1278),(51.5100,-0.1150),(51.5120,-0.1050),(51.5140,-0.0980),(51.5155,-0.0922)]},
    {"name":"일반 루트","color":"#FF6B6B","stops":14,
     "points":[(51.5074,-0.1278),(51.5040,-0.1200),(51.5060,-0.1100),(51.5100,-0.0980),(51.5155,-0.0922)]},
]

map_col, info_col = st.columns([3,2])

with map_col:
    m = folium.Map(location=[51.5100,-0.1100], zoom_start=13,
                   tiles="CartoDB dark_matter")
    for r in ROUTES:
        folium.PolyLine(r["points"], color=r["color"],
                        weight=5, opacity=0.9,
                        tooltip=r["name"]).add_to(m)
    folium.Marker((s_lat,s_lon),
        icon=folium.Icon(color="green",icon="play",prefix="fa"),
        popup="🏃 출발").add_to(m)
    folium.Marker((e_lat,e_lon),
        icon=folium.Icon(color="red",icon="flag",prefix="fa"),
        popup="🏁 도착").add_to(m)
    for pos in [(51.5062,-0.1200),(51.5055,-0.1140),
                (51.5048,-0.1020),(51.5038,-0.0995)]:
        folium.CircleMarker(pos, radius=6, color="#FF4444",
            fill=True, fill_color="#FF4444",
            fill_opacity=0.8, tooltip="🚦 신호").add_to(m)
    st_folium(m, width=None, height=450)

with info_col:
    st.markdown("### 루트별 훈련 효과")
    for r in ROUTES:
        lost = round(r["stops"] * 2.25, 1)
        total_min = 60
        zone_t = round(total_min - lost, 1)
        zone_r = round((zone_t / total_min) * 100, 0)
        bar_f = int(zone_r / 10)
        bar = "█" * bar_f + "░" * (10 - bar_f)
        col = r["color"]
        effect = "⭐⭐⭐ 최적" if zone_r>=80 else "⭐⭐ 양호" if zone_r>=60 else "⭐ 비권장"

        st.markdown(f"""
        <div style="background:#111;border-left:4px solid {col};
                    border-radius:8px;padding:16px;margin:8px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:{col};font-weight:700;font-size:16px;">{r["name"]}</span>
                <span style="color:#888;font-size:12px;">신호 {r["stops"]}회</span>
            </div>
            <div style="margin:8px 0;">
                <div style="color:#888;font-size:11px;margin-bottom:4px;">ZONE 유지</div>
                <div style="font-size:24px;font-weight:900;color:#fff;">{int(zone_r)}%</div>
                <div style="color:{col};font-family:monospace;font-size:14px;margin:4px 0;">[{bar}]</div>
                <div style="color:#888;font-size:12px;">{zone_t}분 / {total_min}분 · {effect}</div>
            </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── 음성 안내 섹션 ────────────────────────────────
st.markdown("### 🎙️ 음성 안내 & AI 코치")

v_col, ai_col = st.columns(2)

with v_col:
    st.markdown("**자동 음성 안내**")
    st.markdown("""
    <div style="background:#111;border-radius:12px;padding:16px;">
        <div style="color:#888;font-size:12px;margin-bottom:12px;">안내 시점</div>
        <div style="margin:6px 0;">✅ 매 1km 완료 시</div>
        <div style="margin:6px 0;">✅ 심박 Zone 변화 시</div>
        <div style="margin:6px 0;">✅ 신호 예상 구간 접근 시</div>
        <div style="margin:6px 0;">✅ 날씨 변화 경고</div>
        <div style="margin:6px 0;">✅ 목표 달성 시</div>
    </div>
    """, unsafe_allow_html=True)

    # 음성 테스트 버튼
    if st.button("🔊 음성 안내 테스트"):
        msg = f"현재 페이스 {pace}분 킬로미터. 목표 심박 Zone {z2_min}에서 {z3_max}. 오늘 런던 날씨 {weather['temp']}도. 달리기 적합도 {weather['score']}점. 최적 루트로 출발하세요."
        st.markdown(f"""
        <script>
        var msg = new SpeechSynthesisUtterance("{msg}");
        msg.lang = "ko-KR";
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
        </script>
        """, unsafe_allow_html=True)
        st.success(f"🔊 {msg}")

with ai_col:
    st.markdown("**AI 코치에게 질문하기**")
    question = st.text_input("질문 입력",
        placeholder="예: 오늘 비 오나? 내 페이스 어때? 얼마나 더 가야 해?")

    if st.button("🤖 AI 코치에게 묻기") and question:
        context = {
            "pace": pace,
            "km": st.session_state.km_completed,
            "weather": weather["temp"],
            "weather_desc": weather["desc"],
            "zone": f"Zone 2~3 ({z2_min}~{z3_max} bpm)",
            "route": "최적 루트 (신호 4회)"
        }
        with st.spinner("AI 코치 답변 중..."):
            answer = ask_gemini(question, context)

        st.markdown(f"""
        <div style="background:#111;border-left:4px solid #00FF88;
                    border-radius:8px;padding:16px;margin:8px 0;">
            <div style="color:#00FF88;font-size:12px;margin-bottom:8px;">AI 코치</div>
            <div style="font-size:14px;">{answer}</div>
        </div>""", unsafe_allow_html=True)

        # AI 답변 음성 출력
        st.markdown(f"""
        <script>
        var msg = new SpeechSynthesisUtterance(`{answer}`);
        msg.lang = "ko-KR";
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
        </script>
        """, unsafe_allow_html=True)

st.divider()

# ── GPS 위치 추적 ──────────────────────────────────
st.markdown("### 📍 실시간 위치 추적")
st.markdown("""
<div style="background:#111;border-radius:12px;padding:16px;">
    <div id="gps-status" style="color:#888;">GPS 대기 중...</div>
    <div id="gps-coords" style="font-size:12px;color:#555;margin-top:4px;"></div>
</div>

<script>
if (navigator.geolocation) {
    navigator.geolocation.watchPosition(function(pos) {
        var lat = pos.coords.latitude.toFixed(4);
        var lon = pos.coords.longitude.toFixed(4);
        var acc = pos.coords.accuracy.toFixed(0);
        document.getElementById("gps-status").innerHTML =
            "📍 위치 추적 중 <span style='color:#00FF88'>●</span>";
        document.getElementById("gps-coords").innerHTML =
            "위도: " + lat + " / 경도: " + lon + " / 정확도: " + acc + "m";
    }, function(err) {
        document.getElementById("gps-status").innerHTML =
            "⚠️ GPS 오류: " + err.message;
    }, {enableHighAccuracy: true, maximumAge: 5000});
} else {
    document.getElementById("gps-status").innerHTML = "GPS 미지원 브라우저";
}
</script>
""", unsafe_allow_html=True)

st.caption("London Runner v2.0 · 마라톤 훈련 최적화 · Zone 2~3 심박 유지")
