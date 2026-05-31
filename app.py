# =============================================================================
# LONDON RUNNER × PRET A MANGER  |  app_pret.py
# Nike Run Club–style UI · Traffic Light Route Avoidance · Zone 2~3 Tracking
# Deploy: streamlit run app_pret.py
# =============================================================================
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
from datetime import datetime, timedelta
import math, random

# ── BRAND CONFIG ──────────────────────────────────────────────────────────────
B = {
    "name"       : "Pret Runner",
    "tagline"    : "Fresh Routes. Fresh Coffee.",
    "emoji"      : "🥐",
    "page_title" : "Pret Runner · London",
    "bg"         : "#040202",
    "surface"    : "#100808",
    "surface2"   : "#1A0F0F",
    "border"     : "#2A1515",
    "primary"    : "#CC0000",
    "accent"     : "#F5F0E8",
    "text"       : "#F5F0E8",
    "text_dim"   : "#857060",
    "z2"         : "#3B82F6",
    "z3"         : "#F59E0B",
    "green"      : "#22C55E",
    "reward"     : "Pret Stars",
    "r_icon"     : "⭐",
    "r_rate"     : 5,
    "unlock_at"  : 30,
    "unlock_msg" : "Free hot drink unlocked! Redeem at any Pret.",
    "cta"        : "Grab your post-run Pret",
    "cta_url"    : "https://www.pret.co.uk",
    "powered"    : "Powered by Pret A Manger",
    "brand_tip"  : "Nearest Pret is 3 min away — your order is ready.",
}

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title=B["page_title"], page_icon=B["emoji"],
                   layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
.stApp{{background:{B['bg']};color:{B['text']};font-family:'Inter',sans-serif;}}
.block-container{{padding:0 1rem 6rem 1rem;max-width:480px;margin:0 auto;}}
#MainMenu,footer,header{{visibility:hidden;}}
.stDeployButton{{display:none;}}
::-webkit-scrollbar{{width:4px;}}
::-webkit-scrollbar-thumb{{background:{B['border']};border-radius:2px;}}
.brand-header{{background:linear-gradient(135deg,{B['primary']},{B['surface2']});
  padding:20px 20px 16px;border-radius:0 0 24px 24px;
  margin:-1rem -1rem 1.5rem -1rem;display:flex;align-items:center;gap:12px;}}
.brand-name{{font-size:22px;font-weight:900;color:{B['text']};}}
.brand-tag{{font-size:12px;color:{B['accent']};opacity:.8;margin-top:2px;letter-spacing:.5px;}}
.card{{background:{B['surface']};border:1px solid {B['border']};
  border-radius:16px;padding:18px;margin-bottom:12px;}}
.card-label{{font-size:11px;font-weight:600;letter-spacing:1.5px;
  text-transform:uppercase;color:{B['text_dim']};margin-bottom:6px;}}
.big-num{{font-size:64px;font-weight:900;line-height:1;color:{B['text']};letter-spacing:-2px;}}
.unit-lbl{{font-size:16px;font-weight:400;color:{B['text_dim']};margin-left:4px;}}
.metric-row{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:12px;}}
.m-card{{background:{B['surface']};border:1px solid {B['border']};
  border-radius:12px;padding:14px 10px;text-align:center;}}
.m-val{{font-size:26px;font-weight:800;color:{B['text']};}}
.m-lbl{{font-size:10px;color:{B['text_dim']};margin-top:2px;letter-spacing:.5px;}}
.run-card{{background:{B['surface']};border:1px solid {B['border']};
  border-radius:14px;padding:16px;margin-bottom:10px;
  display:flex;justify-content:space-between;align-items:center;}}
.zone-bar-bg{{background:{B['border']};border-radius:6px;height:10px;overflow:hidden;}}
.zone-bar-fill{{height:10px;border-radius:6px;transition:width .8s ease;}}
.reward-card{{background:linear-gradient(135deg,{B['primary']}22,{B['accent']}08);
  border:1px solid {B['primary']}44;border-radius:16px;
  padding:20px;text-align:center;margin-bottom:12px;}}
.reward-pts{{font-size:48px;font-weight:900;color:{B['primary']};}}
.badge{{display:inline-flex;align-items:center;gap:6px;
  background:{B['primary']}33;border:1px solid {B['primary']}66;
  border-radius:20px;padding:6px 14px;font-size:12px;font-weight:600;color:{B['accent']};margin:4px;}}
.ring-container{{display:flex;justify-content:center;margin:8px 0;}}
.divider{{height:1px;background:{B['border']};margin:16px 0;}}
.stButton>button{{background:{B['primary']};color:{B['text']};border:none;
  border-radius:50px;padding:14px 32px;font-size:16px;font-weight:700;
  width:100%;cursor:pointer;letter-spacing:.5px;}}
.stButton>button:hover{{background:{B['accent']};color:#1A0000;}}
.stTextInput>div>div>input,.stNumberInput>div>div>input{{
  background:{B['surface2']};color:{B['text']};border:1px solid {B['border']};border-radius:10px;}}
</style>""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_state():
    defaults={"page":"home","age":30,"name":"Runner","max_hr":190,
        "runs":[],"total_pts":0,"run_active":False,"run_start":None,
        "start_pin":None,"end_pin":None,"chosen_route":None,"routes":[],
        "current_hr":140,"current_dist":0.0,"current_pace":0.0,"zone_time":0.0,"total_time":0.0}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v

init_state()
ss=st.session_state

# ── API HELPERS ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_weather():
    try:
        key=st.secrets.get("WEATHER_API_KEY","")
        if not key: raise ValueError
        r=requests.get("https://api.openweathermap.org/data/2.5/weather",
            params={"q":"London,UK","appid":key,"units":"metric"},timeout=5)
        d=r.json(); ic=d["weather"][0]["icon"]
        imap={"01":"☀️","02":"⛅","03":"☁️","04":"☁️","09":"🌧️","10":"🌦️","11":"⛈️","13":"❄️","50":"🌫️"}
        return {"temp":round(d["main"]["temp"]),"feels":round(d["main"]["feels_like"]),
                "desc":d["weather"][0]["description"].title(),"icon":imap.get(ic[:2],"🌤️")}
    except:
        return {"temp":14,"feels":12,"desc":"Cloudy","icon":"☁️"}

@st.cache_data(ttl=300)
def get_tfl_routes(flat,flon,tlat,tlon):
    try:
        key=st.secrets.get("TFL_APP_KEY","")
        url=f"https://api.tfl.gov.uk/Journey/JourneyResults/{flat},{flon}/to/{tlat},{tlon}"
        params={"mode":"walking","app_key":key} if key else {"mode":"walking"}
        r=requests.get(url,params=params,timeout=8); data=r.json()
        routes=[]; labels=["Low Traffic Route","Fast Route","Scenic Route"]
        for i,j in enumerate(data.get("journeys",[])[:3]):
            legs=j.get("legs",[]); dur=j.get("duration",30)
            dist=round(sum(l.get("distance",0) for l in legs)/1000,2)
            stops=sum(len(l.get("path",{}).get("stopPoints",[])) for l in legs)
            lights=max(2,stops//3+random.randint(0,3)); eff=max(20,min(100,100-lights*5))
            routes.append({"id":i,"label":labels[i%3],"duration_min":dur,
                          "distance_km":dist if dist>0.1 else 3.2,"lights":lights,"efficiency":eff})
        if routes: return sorted(routes,key=lambda x:x["lights"])
        raise ValueError
    except:
        d=max(0.5,round(((tlat-flat)**2+(tlon-flon)**2)**0.5*111,2))
        return [
            {"id":0,"label":"Low Traffic Route","duration_min":round(d*12),"distance_km":round(d,2),"lights":3,"efficiency":85},
            {"id":1,"label":"Fast Route","duration_min":round(d*10),"distance_km":round(d*1.1,2),"lights":7,"efficiency":65},
            {"id":2,"label":"Scenic Route","duration_min":round(d*14),"distance_km":round(d*1.2,2),"lights":11,"efficiency":45},
        ]

def ask_gemini(prompt):
    try:
        key=st.secrets.get("GEMINI_API_KEY","")
        if not key: raise ValueError
        url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}"
        r=requests.post(url,json={"contents":[{"parts":[{"text":prompt}]}]},timeout=8)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Excellent run! Consistent Zone 2–3 training is the secret to marathon success. You're on track."

def zone_for_hr(hr,mhr):
    p=hr/mhr
    if p<0.60: return 1
    if p<0.70: return 2
    if p<0.80: return 3
    if p<0.90: return 4
    return 5

def eff_color(e):
    if e>=80: return B["green"]
    if e>=60: return B["z3"]
    return "#EF4444"

def svg_ring(pct,color,size=120,label=""):
    r=46; c=2*math.pi*r; dash=c*pct/100
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 120 120">'
            f'<circle cx="60" cy="60" r="{r}" fill="none" stroke="{B["border"]}" stroke-width="10"/>'
            f'<circle cx="60" cy="60" r="{r}" fill="none" stroke="{color}" stroke-width="10" '
            f'stroke-dasharray="{dash:.1f} {c:.1f}" stroke-dashoffset="{c*0.25:.1f}" '
            f'stroke-linecap="round" transform="rotate(-90 60 60)"/>'
            f'<text x="50%" y="46%" dominant-baseline="middle" text-anchor="middle" '
            f'fill="{B["text"]}" font-size="22" font-weight="900" font-family="Inter">{pct:.0f}%</text>'
            f'<text x="50%" y="62%" dominant-baseline="middle" text-anchor="middle" '
            f'fill="{B["text_dim"]}" font-size="10" font-family="Inter">{label}</text></svg>')

# ── NAVIGATION ────────────────────────────────────────────────────────────────
def nav_bar():
    pages=[("🏠","Home","home"),("🗺️","Route","route"),
           ("▶️","Run","running"),("📊","Stats","history"),("👤","Me","profile")]
    cols=st.columns(len(pages))
    for col,(icon,label,pid) in zip(cols,pages):
        with col:
            if st.button(f"{icon}\n{label}",key=f"nav_{pid}",use_container_width=True):
                ss.page=pid; st.rerun()

# ── HOME ──────────────────────────────────────────────────────────────────────
def page_home():
    w=get_weather()
    st.markdown(f"""<div class="brand-header">
      <span style="font-size:34px">{B['emoji']}</span>
      <div><div class="brand-name">{B['name']}</div><div class="brand-tag">{B['tagline']}</div></div>
      <div style="margin-left:auto;text-align:right">
        <div style="font-size:26px;font-weight:800">{w['icon']} {w['temp']}°</div>
        <div style="font-size:11px;color:{B['accent']};opacity:.7">{w['desc']}</div>
      </div></div>""",unsafe_allow_html=True)

    h=datetime.now().hour
    greet="Good morning" if h<12 else "Good afternoon" if h<17 else "Good evening"
    st.markdown(f"<div style='font-size:20px;font-weight:700;margin-bottom:12px'>{greet}, {ss.name} 👋</div>",unsafe_allow_html=True)

    week_runs=[r for r in ss.runs if datetime.fromisoformat(r["date"])>datetime.now()-timedelta(days=7)] if ss.runs else []
    wkm=sum(r["distance_km"] for r in week_runs)
    st.markdown(f"""<div class="metric-row">
      <div class="m-card"><div class="m-val">{len(week_runs)}</div><div class="m-lbl">RUNS/WEEK</div></div>
      <div class="m-card"><div class="m-val">{wkm:.1f}</div><div class="m-lbl">KM/WEEK</div></div>
      <div class="m-card"><div class="m-val" style="color:{B['primary']}">{ss.total_pts}</div>
        <div class="m-lbl">PRET STARS</div></div></div>""",unsafe_allow_html=True)

    if ss.runs:
        last=ss.runs[-1]; eff=last["efficiency"]
        c1,c2=st.columns(2)
        with c1:
            st.markdown(f"""<div class="card"><div class="card-label">Last Run Zone Efficiency</div>
            <div class="ring-container">{svg_ring(eff,eff_color(eff),label="Zone 2~3")}</div>
            <div style="text-align:center;font-size:13px;color:{B['text_dim']}">{last['distance_km']} km · {last['duration_min']} min</div>
            </div>""",unsafe_allow_html=True)
        with c2:
            best=max(r["efficiency"] for r in ss.runs)
            avg=round(sum(r["efficiency"] for r in ss.runs)/len(ss.runs))
            st.markdown(f"""<div class="card"><div class="card-label">Personal Stats</div>
            <div style="margin-top:8px"><div style="font-size:11px;color:{B['text_dim']}">Total runs</div>
              <div style="font-size:26px;font-weight:800">{len(ss.runs)}</div></div>
            <div style="margin-top:8px"><div style="font-size:11px;color:{B['text_dim']}">Best zone eff</div>
              <div style="font-size:26px;font-weight:800;color:{B['primary']}">{best}%</div></div>
            <div style="margin-top:8px"><div style="font-size:11px;color:{B['text_dim']}">Avg zone eff</div>
              <div style="font-size:26px;font-weight:800">{avg}%</div></div></div>""",unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="card" style="text-align:center;padding:32px">
        <div style="font-size:48px;margin-bottom:12px">🏃</div>
        <div style="font-size:18px;font-weight:700">Ready to run London?</div>
        <div style="font-size:14px;color:{B['text_dim']};margin-top:6px">Earn Pret Stars on every Zone km</div>
        </div>""",unsafe_allow_html=True)

    if st.button("▶  Start a Run",use_container_width=True):
        ss.page="route"; st.rerun()

    pts_to=B["unlock_at"]-(ss.total_pts%B["unlock_at"]) if ss.total_pts>0 else B["unlock_at"]
    pct_to=((ss.total_pts%B["unlock_at"])/B["unlock_at"])*100
    st.markdown(f"""<div class="card">
      <div class="card-label">{B['r_icon']} {B['reward']}</div>
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin:8px 0">
        <div style="font-size:32px;font-weight:900;color:{B['primary']}">{ss.total_pts}</div>
        <div style="font-size:12px;color:{B['text_dim']}">{pts_to} stars to free drink</div>
      </div>
      <div class="zone-bar-bg"><div class="zone-bar-fill" style="width:{pct_to:.0f}%;background:{B['primary']}"></div></div>
      <div style="font-size:12px;color:{B['text_dim']};margin-top:8px">{B['r_icon']} {B['unlock_msg']}</div>
    </div>""",unsafe_allow_html=True)

# ── ROUTE ─────────────────────────────────────────────────────────────────────
def page_route():
    st.markdown(f"<div style='font-size:22px;font-weight:800;margin:16px 0 8px'>🗺️ Plan Route</div>",unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:13px;color:{B['text_dim']};margin-bottom:10px'>Tap map → Set Start, then End</div>",unsafe_allow_html=True)

    center=list(ss.start_pin) if ss.start_pin else [51.5074,-0.1278]
    m=folium.Map(location=center,zoom_start=14,tiles="CartoDB.DarkMatter")
    if ss.start_pin: folium.Marker(ss.start_pin,icon=folium.Icon(color="green",icon="play"),popup="Start").add_to(m)
    if ss.end_pin:   folium.Marker(ss.end_pin,icon=folium.Icon(color="red",icon="flag"),popup="End").add_to(m)
    if ss.routes and ss.chosen_route is not None and ss.start_pin and ss.end_pin:
        folium.PolyLine([ss.start_pin,ss.end_pin],color=B["primary"],weight=4,opacity=0.8).add_to(m)

    md=st_folium(m,width=None,height=280,returned_objects=["last_clicked"])
    if md and md.get("last_clicked"):
        pt=(md["last_clicked"]["lat"],md["last_clicked"]["lng"])
        if not ss.start_pin:  ss.start_pin=pt; st.rerun()
        elif not ss.end_pin:  ss.end_pin=pt;   st.rerun()

    c1,c2=st.columns(2)
    with c1: st.markdown(f"<div class='badge'>{'🟢 Start set' if ss.start_pin else '⬜ Tap for start'}</div>",unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='badge'>{'🔴 End set' if ss.end_pin else '⬜ Tap for end'}</div>",unsafe_allow_html=True)
    if st.button("🔄 Reset Pins"):
        ss.start_pin=None; ss.end_pin=None; ss.routes=[]; ss.chosen_route=None; st.rerun()

    if ss.start_pin and ss.end_pin:
        st.markdown("<div class='divider'></div>",unsafe_allow_html=True)
        if not ss.routes or st.button("🔍 Find Best Routes",use_container_width=True):
            with st.spinner("Finding fresh routes..."):
                ss.routes=get_tfl_routes(ss.start_pin[0],ss.start_pin[1],ss.end_pin[0],ss.end_pin[1])
        if ss.routes:
            st.markdown(f"<div style='font-size:16px;font-weight:700;margin:12px 0 8px'>Route Options</div>",unsafe_allow_html=True)
            for i,rt in enumerate(ss.routes):
                ec=eff_color(rt["efficiency"]); sel=ss.chosen_route==i
                bdr=f"border:2px solid {B['primary']};" if sel else ""
                stars="⭐⭐⭐" if rt["efficiency"]>=80 else "⭐⭐" if rt["efficiency"]>=60 else "⭐"
                st.markdown(f"""<div class="card" style="{bdr}">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div><div style="font-size:15px;font-weight:700">{rt['label']}</div>
                      <div style="font-size:13px;color:{B['text_dim']};margin-top:4px">{rt['distance_km']} km · {rt['duration_min']} min</div></div>
                    <div style="text-align:right">
                      <div style="font-size:26px;font-weight:900;color:{ec}">{rt['efficiency']}%</div>
                      <div style="font-size:11px;color:{B['text_dim']}">Zone eff</div></div>
                  </div>
                  <div class="zone-bar-bg" style="margin-top:10px">
                    <div class="zone-bar-fill" style="width:{rt['efficiency']}%;background:{ec}"></div></div>
                  <div style="font-size:12px;color:{B['text_dim']};margin-top:8px">🚦 ~{rt['lights']} lights · {stars} Zone 2~3</div>
                </div>""",unsafe_allow_html=True)
                if st.button(f"{'✓ Selected' if sel else 'Select this route'}",key=f"sr_{i}",use_container_width=True):
                    ss.chosen_route=i; st.rerun()

            if ss.chosen_route is not None:
                rt=ss.routes[ss.chosen_route]
                pts=round(rt["distance_km"]*B["r_rate"]*(rt["efficiency"]/100))
                st.markdown(f"""<div class="reward-card">
                  <div style="font-size:13px;color:{B['text_dim']}">Complete to earn</div>
                  <div class="reward-pts">+{pts} ⭐</div>
                  <div style="font-size:14px;color:{B['text_dim']}">{B['reward']}</div>
                </div>""",unsafe_allow_html=True)
                if st.button("▶  Start Run Now",use_container_width=True):
                    ss.run_active=True; ss.run_start=datetime.now().isoformat()
                    ss.current_dist=0.0; ss.current_pace=0.0; ss.zone_time=0.0; ss.total_time=0.0
                    ss.page="running"; st.rerun()

# ── RUNNING ───────────────────────────────────────────────────────────────────
def page_running():
    if not ss.run_active:
        st.markdown(f"""<div class="card" style="text-align:center;padding:40px">
        <div style="font-size:48px;margin-bottom:12px">🏃</div>
        <div style="font-size:18px;font-weight:700">No active run</div></div>""",unsafe_allow_html=True)
        if st.button("Plan Route",use_container_width=True): ss.page="route"; st.rerun()
        return

    rt=ss.routes[ss.chosen_route] if ss.routes and ss.chosen_route is not None else {}
    tgt_km=rt.get("distance_km",5.0)
    st.markdown(f"<div style='font-size:13px;color:{B['primary']};text-align:center;letter-spacing:2px;margin-bottom:8px'>● LIVE RUN</div>",unsafe_allow_html=True)

    progress=min(100,ss.current_dist/tgt_km*100) if tgt_km>0 else 0
    st.markdown(f"""<div class="card" style="text-align:center;padding:24px">
      <div class="card-label">DISTANCE</div>
      <div class="big-num">{ss.current_dist:.2f}<span class="unit-lbl">km</span></div>
      <div style="font-size:13px;color:{B['text_dim']};margin-top:6px">of {tgt_km} km target</div>
      <div class="zone-bar-bg" style="margin-top:12px">
        <div class="zone-bar-fill" style="width:{progress:.0f}%;background:{B['primary']}"></div></div>
    </div>""",unsafe_allow_html=True)

    zone_pct=(ss.zone_time/max(ss.total_time,1))*100 if ss.total_time>0 else 0
    c1,c2=st.columns(2)
    with c1:
        st.markdown(f"""<div class="card" style="text-align:center">
        <div class="card-label">ZONE 2~3</div>
        <div class="ring-container">{svg_ring(zone_pct,B['z3'] if zone_pct>=60 else B['z2'],label="efficiency")}</div>
        </div>""",unsafe_allow_html=True)
    with c2:
        pace_str=f"{ss.current_pace:.1f}" if ss.current_pace>0 else "--"
        st.markdown(f"""<div class="card">
        <div class="card-label">PACE</div>
        <div style="font-size:36px;font-weight:800">{pace_str}<span style="font-size:13px;color:{B['text_dim']}"> /km</span></div>
        <div class="card-label" style="margin-top:12px">TIME</div>
        <div style="font-size:36px;font-weight:800">{int(ss.total_time)}<span style="font-size:13px;color:{B['text_dim']}"> min</span></div>
        </div>""",unsafe_allow_html=True)

    hr=st.number_input("Current HR (bpm)",50,220,ss.current_hr,key="hr_live")
    zone=zone_for_hr(hr,ss.max_hr)
    zc={1:"#94A3B8",2:B["z2"],3:B["z3"],4:"#F97316",5:"#EF4444"}
    zn={1:"Zone 1 – Easy",2:"Zone 2 – Aerobic ✓",3:"Zone 3 – Tempo ✓",4:"Zone 4 – Hard ↑",5:"Zone 5 – Max ⚠️"}
    st.markdown(f"""<div class="card" style="border-color:{zc[zone]}44">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><div style="font-size:38px;font-weight:900">{hr}<span style="font-size:14px;color:{B['text_dim']}"> bpm</span></div>
          <div style="font-size:14px;font-weight:700;color:{zc[zone]};margin-top:4px">{zn[zone]}</div></div>
        <div style="font-size:11px;color:{B['text_dim']};text-align:right">
          Z2: {ss.max_hr*.6:.0f}–{ss.max_hr*.7:.0f}<br/>Z3: {ss.max_hr*.7:.0f}–{ss.max_hr*.8:.0f}</div>
      </div></div>""",unsafe_allow_html=True)
    ss.current_hr=hr

    gc1,gc2,gc3=st.columns(3)
    with gc1: km_add=st.number_input("+km",0.0,5.0,0.5,0.1,key="add_km")
    with gc2: min_add=st.number_input("+min",0,60,5,1,key="add_min")
    with gc3: in_zone=st.checkbox("In zone?",value=(zone in [2,3]))
    if st.button("📍 Log Checkpoint",use_container_width=True):
        ss.current_dist+=km_add; ss.total_time+=min_add
        if in_zone: ss.zone_time+=min_add
        if km_add>0 and min_add>0: ss.current_pace=round(min_add/km_add,1)
        st.rerun()

    st.markdown("<div class='divider'></div>",unsafe_allow_html=True)
    if st.button("🏁  Finish Run",use_container_width=True):
        eff=round((ss.zone_time/max(ss.total_time,1))*100) if ss.total_time>0 else 0
        lights=rt.get("lights",0); pts=round(ss.current_dist*B["r_rate"]*(eff/100))
        ss.runs.append({"date":datetime.now().isoformat(),"distance_km":round(ss.current_dist,2),
            "duration_min":round(ss.total_time),"avg_hr":ss.current_hr,"zone_time":round(ss.zone_time,1),
            "efficiency":eff,"lights":lights,"route_label":rt.get("label","Custom"),"pts_earned":pts})
        ss.total_pts+=pts; ss.run_active=False; ss.page="summary"; st.rerun()

    if zone not in [2,3] and ss.total_time>0:
        adv="slow down to lower your heart rate" if zone>3 else "increase your pace slightly"
        st.markdown(f"""<script>
        var u=new SpeechSynthesisUtterance("Zone {zone} alert. {adv}.");
        u.lang="en-GB";u.rate=0.9;window.speechSynthesis.speak(u);</script>""",unsafe_allow_html=True)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
def page_summary():
    if not ss.runs:
        st.markdown("<div class='card' style='text-align:center;padding:40px'>No runs recorded yet.</div>",unsafe_allow_html=True)
        return
    last=ss.runs[-1]; eff=last["efficiency"]; ec=eff_color(eff)
    stars="⭐⭐⭐" if eff>=80 else "⭐⭐" if eff>=60 else "⭐"

    st.markdown(f"""<div style="text-align:center;padding:20px 0 12px">
      <div style="font-size:40px;margin-bottom:8px">🎉</div>
      <div style="font-size:26px;font-weight:900">Run Complete!</div>
      <div style="font-size:13px;color:{B['text_dim']};margin-top:4px">
        {datetime.fromisoformat(last['date']).strftime('%d %b %Y · %H:%M')}</div>
    </div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="card" style="text-align:center">
      <div class="card-label">ZONE 2~3 EFFICIENCY</div>
      <div class="ring-container">{svg_ring(eff,ec,size=160,label="Zone 2~3")}</div>
      <div style="font-size:14px;color:{B['text_dim']};margin-top:6px">{stars} Marathon Training Score</div>
    </div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="metric-row">
      <div class="m-card"><div class="m-val">{last['distance_km']}</div><div class="m-lbl">KM</div></div>
      <div class="m-card"><div class="m-val">{last['duration_min']}</div><div class="m-lbl">MIN</div></div>
      <div class="m-card"><div class="m-val">🚦{last['lights']}</div><div class="m-lbl">LIGHTS</div></div>
    </div><div class="metric-row">
      <div class="m-card"><div class="m-val">{last['avg_hr']}</div><div class="m-lbl">AVG HR</div></div>
      <div class="m-card"><div class="m-val">{last['zone_time']}</div><div class="m-lbl">ZONE MIN</div></div>
      <div class="m-card"><div class="m-val" style="color:{B['primary']}">{eff}%</div><div class="m-lbl">EFF</div></div>
    </div>""",unsafe_allow_html=True)

    pts=last["pts_earned"]
    st.markdown(f"""<div class="reward-card">
      <div style="font-size:13px;color:{B['text_dim']}">You earned</div>
      <div class="reward-pts">+{pts} ⭐</div>
      <div style="font-size:14px;color:{B['text_dim']}">{B['reward']} · Total: {ss.total_pts}</div>
    </div>""",unsafe_allow_html=True)

    # Pret-specific: calorie → menu recommendation
    kcal=round(last['distance_km']*65)
    if kcal<200:     menu="Lemon Drizzle Slice + Flat White"
    elif kcal<350:   menu="Chicken Avocado Wrap + Oat Latte"
    elif kcal<500:   menu="Chicken Caesar Baguette + Cappuccino"
    else:            menu="All-Day Brunch Box + Large Latte"

    st.markdown(f"""<div class="card">
      <div class="card-label">{B['r_icon']} POST-RUN PRET PICK</div>
      <div style="font-size:15px;font-weight:700;margin-top:8px">Burned ~{kcal} kcal → {menu}</div>
      <div style="font-size:13px;color:{B['text_dim']};margin-top:4px">{B['brand_tip']}</div>
      <a href="{B['cta_url']}" target="_blank"
         style="display:block;margin-top:10px;color:{B['primary']};font-size:14px;font-weight:700">{B['cta']} →</a>
    </div>""",unsafe_allow_html=True)

    if ss.total_pts>=B["unlock_at"]:
        st.markdown(f"""<div class="card" style="text-align:center;
            background:linear-gradient(135deg,{B['primary']}33,#ffffff08)">
          <div style="font-size:28px">🎁</div>
          <div style="font-size:17px;font-weight:800;margin:8px 0">{B['unlock_msg']}</div>
        </div>""",unsafe_allow_html=True)

    if st.button("🤖 AI Coach Feedback",use_container_width=True):
        with st.spinner("Analysing your run..."):
            fb=ask_gemini(f"London marathon running coach. 3-sentence motivating feedback. "
                         f"Run: {last['distance_km']}km, {last['duration_min']}min, "
                         f"Zone 2-3 eff {eff}%, {last['lights']} traffic lights, avg HR {last['avg_hr']}bpm.")
        st.markdown(f"""<div class="card"><div class="card-label">AI COACH</div>
        <div style="font-size:14px;line-height:1.6;margin-top:8px">{fb}</div></div>""",unsafe_allow_html=True)

    if st.button("🔄 New Run",use_container_width=True):
        ss.page="route"; ss.start_pin=None; ss.end_pin=None; ss.routes=[]; ss.chosen_route=None; st.rerun()

# ── HISTORY ───────────────────────────────────────────────────────────────────
def page_history():
    st.markdown(f"<div style='font-size:22px;font-weight:800;margin:16px 0 12px'>📊 Performance History</div>",unsafe_allow_html=True)
    if not ss.runs:
        st.markdown(f"""<div class="card" style="text-align:center;padding:40px">
        <div style="font-size:48px;margin-bottom:12px">📈</div>
        <div style="font-size:18px;font-weight:700">No runs yet</div>
        </div>""",unsafe_allow_html=True)
        return

    tkm=sum(r["distance_km"] for r in ss.runs)
    ae=round(sum(r["efficiency"] for r in ss.runs)/len(ss.runs))
    be=max(r["efficiency"] for r in ss.runs)
    st.markdown(f"""<div class="metric-row">
      <div class="m-card"><div class="m-val">{tkm:.1f}</div><div class="m-lbl">TOTAL KM</div></div>
      <div class="m-card"><div class="m-val">{ae}%</div><div class="m-lbl">AVG ZONE</div></div>
      <div class="m-card"><div class="m-val" style="color:{B['primary']}">{be}%</div><div class="m-lbl">BEST ZONE</div></div>
    </div>""",unsafe_allow_html=True)

    if len(ss.runs)>=2:
        df=pd.DataFrame([{"Run":f"#{i+1}","Zone Efficiency (%)":r["efficiency"],"Traffic Lights":r["lights"]}
                         for i,r in enumerate(ss.runs)])
        st.markdown(f"<div class='card-label' style='margin:8px 0 4px'>ZONE EFFICIENCY TREND</div>",unsafe_allow_html=True)
        st.line_chart(df.set_index("Run")[["Zone Efficiency (%)"]],color=[B["primary"]])
        st.markdown(f"<div class='card-label' style='margin:8px 0 4px'>TRAFFIC LIGHTS PER RUN</div>",unsafe_allow_html=True)
        st.bar_chart(df.set_index("Run")[["Traffic Lights"]],color=[B["primary"]])

    st.markdown(f"<div style='font-size:16px;font-weight:700;margin:16px 0 8px'>Run Log</div>",unsafe_allow_html=True)
    for r in reversed(ss.runs):
        ec=eff_color(r["efficiency"]); dt=datetime.fromisoformat(r["date"]).strftime("%d %b · %H:%M")
        st.markdown(f"""<div class="run-card">
          <div>
            <div style="font-size:12px;color:{B['text_dim']}">{dt}</div>
            <div style="font-size:28px;font-weight:800">{r['distance_km']} km</div>
            <div style="font-size:12px;color:{B['text_dim']}">{r['duration_min']} min · 🚦{r['lights']} · {r['route_label']}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:22px;font-weight:800;color:{ec}">{r['efficiency']}%</div>
            <div style="font-size:11px;color:{B['text_dim']}">Zone eff</div>
            <div style="font-size:14px;font-weight:700;color:{B['primary']};margin-top:6px">+{r['pts_earned']} ⭐</div>
          </div></div>""",unsafe_allow_html=True)

    pb_d=max(r["distance_km"] for r in ss.runs); pb_e=max(r["efficiency"] for r in ss.runs); pb_z=max(r["zone_time"] for r in ss.runs)
    st.markdown(f"""<div style='font-size:16px;font-weight:700;margin:16px 0 8px'>Personal Bests 🏅</div>
    <div class="metric-row">
      <div class="m-card"><div class="m-val">{pb_d}</div><div class="m-lbl">KM PB</div></div>
      <div class="m-card"><div class="m-val">{pb_e}%</div><div class="m-lbl">ZONE PB</div></div>
      <div class="m-card"><div class="m-val">{pb_z}</div><div class="m-lbl">ZONE MIN PB</div></div>
    </div>""",unsafe_allow_html=True)

# ── PROFILE ───────────────────────────────────────────────────────────────────
def page_profile():
    st.markdown(f"<div style='font-size:22px;font-weight:800;margin:16px 0 12px'>👤 Profile</div>",unsafe_allow_html=True)
    st.markdown(f"""<div style="text-align:center;padding:16px 0">
      <div style="width:72px;height:72px;border-radius:50%;background:{B['primary']};
                  display:flex;align-items:center;justify-content:center;font-size:32px;margin:0 auto">{B['emoji']}</div>
      <div style="font-size:20px;font-weight:800;margin-top:10px">{ss.name}</div>
      <div style="font-size:13px;color:{B['text_dim']}">Zone 2~3 Runner · London</div>
    </div>""",unsafe_allow_html=True)

    with st.expander("✏️ Edit Profile"):
        nn=st.text_input("Name",value=ss.name); na=st.number_input("Age",18,80,value=ss.age)
        if st.button("Save Profile"):
            ss.name=nn; ss.age=na; ss.max_hr=220-na; st.success(f"Saved! Max HR = {ss.max_hr} bpm"); st.rerun()

    zones_data=[("Zone 1 – Easy","#94A3B8",ss.max_hr*.5,ss.max_hr*.6),
                ("Zone 2 – Aerobic ✓",B["z2"],ss.max_hr*.6,ss.max_hr*.7),
                ("Zone 3 – Tempo ✓",B["z3"],ss.max_hr*.7,ss.max_hr*.8),
                ("Zone 4 – Hard","#F97316",ss.max_hr*.8,ss.max_hr*.9),
                ("Zone 5 – Max","#EF4444",ss.max_hr*.9,ss.max_hr)]
    rows="".join(f"""<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {B['border']}">
      <div style="color:{c};font-weight:700">{n}</div><div style="font-size:14px">{lo:.0f}–{hi:.0f} bpm</div></div>""" for n,c,lo,hi in zones_data)
    st.markdown(f"""<div class="card"><div class="card-label">HR ZONES (Max: {ss.max_hr} bpm)</div>
    <div style="margin-top:8px">{rows}</div></div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="card" style="text-align:center">
      <div style="font-size:22px">{B['emoji']}</div>
      <div style="font-size:16px;font-weight:700;margin-top:6px">{B['name']}</div>
      <div style="font-size:12px;color:{B['text_dim']};margin-top:2px">{B['powered']}</div>
      <div style="font-size:12px;color:{B['text_dim']};margin-top:10px">{B['reward']}</div>
      <div style="font-size:32px;font-weight:900;color:{B['primary']}">{ss.total_pts}</div>
      <a href="{B['cta_url']}" target="_blank"
         style="display:block;margin-top:10px;color:{B['primary']};font-size:14px;font-weight:700">{B['cta']} →</a>
    </div>""",unsafe_allow_html=True)

    with st.expander("⚠️ Reset Data"):
        if st.button("Clear Run History"):
            ss.runs=[]; ss.total_pts=0; st.success("Cleared."); st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
nav_bar()
if   ss.page=="home":    page_home()
elif ss.page=="route":   page_route()
elif ss.page=="running": page_running()
elif ss.page=="summary": page_summary()
elif ss.page=="history": page_history()
elif ss.page=="profile": page_profile()

st.markdown("""<script>
if(navigator.geolocation){navigator.geolocation.watchPosition(
  p=>{window._lat=p.coords.latitude;window._lon=p.coords.longitude;},
  null,{enableHighAccuracy:true,maximumAge:5000});}
</script>""",unsafe_allow_html=True)
