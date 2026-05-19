
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(
    page_title="London Runner — 신호등 없는 루트",
    page_icon="🏃",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0a0a14; color: #e0e0e0; }
    h1, h2, h3 { color: #00FF88; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

st.title("🏃 London Runner")
st.markdown("##### 신호등 없이 달리는 최적 런던 루트")

with st.sidebar:
    st.header("⚙️ 내 러닝 설정")
    pace = st.slider("현재 페이스 (분/km)", 4.0, 12.0, 6.33, 0.1)
    start_lat = st.number_input("출발 위도", value=51.5074, format="%.4f")
    start_lon = st.number_input("출발 경도", value=-0.1278, format="%.4f")
    end_lat   = st.number_input("도착 위도", value=51.5155, format="%.4f")
    end_lon   = st.number_input("도착 경도", value=-0.0922, format="%.4f")

@st.cache_data(ttl=600)
def get_weather():
    try:
        api_key = st.secrets.get("WEATHER_API_KEY","")
        if not api_key:
            raise ValueError("no key")
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q":"London,UK","appid":api_key,"units":"metric"},
            timeout=5
        )
        if r.status_code == 200:
            d = r.json()
            temp  = d["main"]["temp"]
            wind  = d["wind"]["speed"]
            hum   = d["main"]["humidity"]
            feels = d["main"]["feels_like"]
            icons = {"Clear":"☀️","Clouds":"☁️","Rain":"🌧️","Drizzle":"🌦️","Snow":"❄️"}
            icon  = icons.get(d["weather"][0]["main"],"🌤️")
            score = 100
            if temp<2 or temp>28: score -= 25
            if wind>12: score -= 20
            if hum>85:  score -= 10
            if "Rain" in d["weather"][0]["main"]: score -= 25
            advice = ("✅ 최적!" if score>=80 else "🟡 가능" if score>=60
                      else "🟠 주의" if score>=40 else "🔴 비권장")
            return {"temp":temp,"feels":feels,"humidity":hum,
                    "wind":wind,"icon":icon,"score":max(0,score),"advice":advice}
    except:
        pass
    return {"temp":14,"feels":12,"humidity":70,"wind":4,
            "icon":"🌤️","score":75,"advice":"🟡 가능 (샘플)"}

weather = get_weather()

col1,col2,col3,col4 = st.columns(4)
with col1: st.metric("🌡️ 런던 날씨", f"{weather['temp']}°C", f"체감 {weather['feels']}°C")
with col2: st.metric("💨 바람", f"{weather['wind']}m/s", f"습도 {weather['humidity']}%")
with col3: st.metric("🏃 달리기 적합도", f"{weather['score']}/100", weather['advice'])
with col4:
    cal = round(pace * 12, 1)
    st.metric("🔥 칼로리/km", f"{cal}kcal", f"페이스 {pace}분/km")

st.divider()

ROUTES = [
    {"name":"옵션1 — 신호 최소 ⭐⭐⭐","color":"#00FF88","stops":4,
     "points":[(51.5074,-0.1278),(51.5065,-0.1229),(51.5055,-0.1090),(51.5033,-0.0980),(51.5155,-0.0922)]},
    {"name":"옵션2 — 중간 루트 ⭐⭐","color":"#FFD700","stops":8,
     "points":[(51.5074,-0.1278),(51.5100,-0.1150),(51.5120,-0.1050),(51.5140,-0.0980),(51.5155,-0.0922)]},
    {"name":"옵션3 — 일반 루트 ⭐","color":"#FF6B6B","stops":14,
     "points":[(51.5074,-0.1278),(51.5040,-0.1200),(51.5060,-0.1100),(51.5100,-0.0980),(51.5155,-0.0922)]},
]

map_col, info_col = st.columns([2,1])

with map_col:
    m = folium.Map(location=[51.5100,-0.1100], zoom_start=13, tiles="CartoDB dark_matter")
    for r in ROUTES:
        folium.PolyLine(r["points"],color=r["color"],weight=4,opacity=0.85,tooltip=r["name"]).add_to(m)
    folium.Marker((start_lat,start_lon),
        icon=folium.Icon(color="green",icon="play",prefix="fa"),popup="🏃 출발").add_to(m)
    folium.Marker((end_lat,end_lon),
        icon=folium.Icon(color="red",icon="flag",prefix="fa"),popup="🏁 도착").add_to(m)
    for pos in [(51.5062,-0.1200),(51.5055,-0.1140),(51.5048,-0.1020),(51.5038,-0.0995)]:
        folium.CircleMarker(pos,radius=5,color="#FF4444",fill=True,
            fill_color="#FF4444",fill_opacity=0.7,tooltip="🚦 신호").add_to(m)
    st_folium(m, width=700, height=500)

with info_col:
    st.markdown("### 📋 루트 비교")
    for r in ROUTES:
        dist  = round(60 / pace, 2)
        c_no  = round(dist * pace * 12, 0)
        c_yes = round(c_no * (1 - r["stops"] * 0.012), 0)
        gain  = int(c_no - c_yes)
        st.markdown(f"""
        <div style="border-left:4px solid {r['color']};
                    background:rgba(255,255,255,0.04);
                    border-radius:6px;padding:10px;margin:8px 0;">
          <b style="color:{r['color']}">{r['name']}</b><br>
          🚦 신호: <b>{r['stops']}회</b><br>
          🔥 신호없을때: <b>{int(c_no)}kcal</b><br>
          🔻 신호있을때: <b>{int(c_yes)}kcal</b><br>
          ✅ 이득: <b style="color:#00FF88">+{gain}kcal</b>
        </div>
        """, unsafe_allow_html=True)

st.caption("London Runner v1.0 | TfL API + OpenWeather")
