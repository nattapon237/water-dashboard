import streamlit as st
import numpy as np
import pandas as pd
import requests
import json
import time
import math
from datetime import datetime

st.set_page_config(page_title="EEC Community Water Intelligence System", page_icon="💧", layout="wide")

# --- Firebase Configuration (cwis-c2ea8) ---
FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"

# LINE API Configuration
LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"

# --- High-Tech Cyber-Water Glassmorphism CSS ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {
  --void: #030712;
  --panel: rgba(11, 21, 38, 0.78);
  --panel-solid: #0b1526;
  --hairline: rgba(56, 189, 248, 0.16);
  --hairline-strong: rgba(56, 189, 248, 0.42);
  --cyan: #22d3ee;
  --violet: #a78bfa;
  --orange: #fb923c;
  --safe: #34d399;
  --warn: #fbbf24;
  --danger: #f87171;
  --text-hi: #eef2f7;
  --text-mid: #b6c2d1;
  --text-low: #6b7c93;
}
.stApp {
  background: radial-gradient(ellipse 900px 500px at 15% -10%, rgba(34,211,238,0.09), transparent 60%), radial-gradient(ellipse 700px 500px at 100% 0%, rgba(167,139,250,0.06), transparent 55%), var(--void);
  color: var(--text-mid);
  font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
  background-color: #050c18;
  border-right: 1px solid var(--hairline);
}
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 {
  font-family: 'Space Grotesk', sans-serif !important;
  color: var(--text-hi) !important;
  letter-spacing: 0.2px;
}
p, span, label, .stMarkdown, li { color: var(--text-mid); }
.hdr-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--cyan);
  margin-bottom: 2px;
}
.hdr-title { font-size: 1.9rem; font-weight: 700; color: var(--text-hi); margin: 0 0 4px 0; }
.hdr-sub { color: var(--text-low); font-size: 0.92rem; }
.status-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 999px;
  font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.95rem;
  border: 1px solid var(--pill-color, var(--safe));
  color: var(--pill-color, var(--safe));
  background: color-mix(in srgb, var(--pill-color, var(--safe)) 12%, transparent);
  box-shadow: 0 0 22px color-mix(in srgb, var(--pill-color, var(--safe)) 35%, transparent);
  float: right;
}
.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--pill-color, var(--safe));
  box-shadow: 0 0 8px var(--pill-color, var(--safe));
}
.panel {
  background: linear-gradient(155deg, rgba(20,35,64,0.55) 0%, rgba(6,12,24,0.85) 100%);
  border: 1px solid var(--hairline);
  border-radius: 16px;
  padding: 20px 22px;
  height: 100%;
  backdrop-filter: blur(14px);
}
.panel-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.98rem; font-weight: 700; color: var(--text-hi);
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 14px;
}
.panel-title .tag {
  font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 500;
  color: var(--text-low); letter-spacing: 1px; text-transform: uppercase;
  border: 1px solid var(--hairline-strong); border-radius: 5px; padding: 2px 6px;
}
.gauge-card {
  background: linear-gradient(155deg, rgba(20,35,64,0.55) 0%, rgba(6,12,24,0.85) 100%);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  padding: 16px 16px 14px 16px;
}
.gauge-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
.gauge-label {
  font-size: 0.72rem; letter-spacing: 1px; text-transform: uppercase;
  color: var(--text-low); font-weight: 600;
}
.gauge-icon { font-size: 1.05rem; opacity: 0.85; }
.gauge-value {
  font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.65rem;
  line-height: 1.1; margin: 2px 0 12px 0;
}
.gauge-unit { font-size: 0.85rem; font-weight: 500; color: var(--text-low); margin-left: 3px; }
.gauge-track {
  position: relative; height: 6px; border-radius: 4px; margin-bottom: 6px;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
}
.gauge-marker {
  position: absolute; top: -3px; width: 3px; height: 12px; border-radius: 2px;
  background: #fff; box-shadow: 0 0 6px rgba(255,255,255,0.9), 0 0 2px #000;
  transform: translateX(-50%);
}
.gauge-range {
  display: flex; justify-content: space-between;
  font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--text-low);
}
.risk-wrap { display: flex; align-items: center; gap: 22px; }
.risk-figure { font-family: 'JetBrains Mono', monospace; font-weight: 700; }
.risk-status-label { font-size: 0.95rem; font-weight: 600; margin-top: 2px; }
.risk-advice {
  font-size: 0.83rem; color: var(--text-low); margin-top: 10px;
  border-top: 1px solid var(--hairline); padding-top: 10px; line-height: 1.5;
}
.check-row {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 10px 0; border-bottom: 1px solid var(--hairline);
}
.check-row:last-child { border-bottom: none; }
.check-icon { font-size: 1rem; margin-top: 1px; }
.check-text { font-size: 0.88rem; color: var(--text-mid); line-height: 1.45; }
.check-text b { color: var(--text-hi); }
.data-badge {
  font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
  color: var(--cyan); background: rgba(34,211,238,0.08);
  border: 1px solid rgba(34,211,238,0.25); border-radius: 8px;
  padding: 8px 14px; display: inline-block;
}
hr.divider { border: 0; height: 1px; background: var(--hairline); margin: 22px 0; }
.stButton>button {
  background: linear-gradient(135deg, #0f5f8a, #0ea5e9);
  color: #f8fafc; border: 1px solid var(--hairline-strong);
  border-radius: 10px; font-weight: 600; font-family: 'Inter', sans-serif;
  padding: 0.6rem 1.2rem; box-shadow: 0 4px 18px rgba(14,165,233,0.35);
  transition: all 0.2s ease;
}
.stButton>button:hover {
  background: linear-gradient(135deg, #0ea5e9, #22d3ee);
  color: #04101f; box-shadow: 0 6px 24px rgba(34,211,238,0.55);
  transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"to": TARGET_USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        return res.status_code == 200
    except Exception:
        return False

@st.cache_data(ttl=3000)
def get_firebase_token():
    auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    try:
        res = requests.post(auth_url, json={"returnSecureToken": True}, timeout=5)
        if res.status_code == 200:
            return res.json().get("idToken")
        return None
    except Exception:
        return None

def read_sensor_data(id_token):
    if not id_token:
        return None
    url = f"{FIREBASE_DB_URL}/devices/uno-r4/status.json?auth={id_token}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None

def write_mock_sensor_data(id_token, ph_val, tds_val, temp_val, do_val, turb_val):
    if not id_token:
        return False
    url = f"{FIREBASE_DB_URL}/devices/uno-r4/status.json?auth={id_token}"
    payload = {
        "ph": ph_val, "tds": tds_val, "temp": temp_val,
        "do": do_val, "turbidity": turb_val, "updatedAt": int(time.time())
    }
    try:
        res = requests.put(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

id_token = get_firebase_token()

st.sidebar.title("🔥 สถานะ Firebase")
if id_token:
    st.sidebar.success("🟢 เชื่อมต่อ RTDB สำเร็จ")
else:
    st.sidebar.error("🔴 ขาดการเชื่อมต่อ Firebase")

st.sidebar.markdown("---")
st.sidebar.title("🎛️ เซนเซอร์ / Input Control")
sim_ph = st.sidebar.slider("pH Level", 0.0, 14.0, 6.4, 0.1)
sim_tds = st.sidebar.slider("EC / TDS (ppm)", 0.0, 1200.0, 158.1, 0.1)
sim_temp = st.sidebar.slider("Temperature (°C)", 10.0, 45.0, 24.5, 0.5)
sim_do = st.sidebar.slider("DO (mg/L)", 0.0, 20.0, 9.2, 0.1)
sim_turb = st.sidebar.slider("Turbidity (NTU)", 0.0, 300.0, 0.0, 0.1)

if st.sidebar.button("📤 ส่งค่าจำลองขึ้น Firebase", use_container_width=True):
    if write_mock_sensor_data(id_token, sim_ph, sim_tds, sim_temp, sim_do, sim_turb):
        st.sidebar.success("✅ บันทึกค่าขึ้น Firebase เรียบร้อย!")
        st.rerun()

live_data = read_sensor_data(id_token)
if live_data and isinstance(live_data, dict) and "ph" in live_data:
    ph = float(live_data.get("ph", sim_ph))
    tds = float(live_data.get("tds", sim_tds))
    temp = float(live_data.get("temp", sim_temp))
    do_val = float(live_data.get("do", sim_do))
    turbidity = float(live_data.get("turbidity", sim_turb))
    data_source_badge = "📡 ข้อมูลสดจาก Firebase Realtime Database"
else:
    ph, tds, temp, do_val, turbidity = sim_ph, sim_tds, sim_temp, sim_do, sim_turb
    data_source_badge = "⚠️ ใช้ค่าจำลองจากแถบด้านข้าง (ยังไม่มีข้อมูลสด)"

def calculate_risk(ph, tds, temp, do_val, turbidity):
    score = 0
    reasons = []
    if not (6.5 <= ph <= 8.5):
        score += 30; reasons.append(f"pH ({ph}) อยู่นอกเกณฑ์มาตรฐาน")
    if tds > 600:
        score += 30; reasons.append(f"TDS ({tds:.1f} ppm) สูงเกินเกณฑ์")
    if do_val < 5.0:
        score += 25; reasons.append(f"DO ({do_val:.1f} mg/L) ต่ำเกินไป")
    if turbidity > 100:
        score += 15; reasons.append(f"ความขุ่น ({turbidity:.1f} NTU) สูงเกินไป")
    return min(score, 99), reasons

risk_score, risk_reasons = calculate_risk(ph, tds, temp, do_val, turbidity)

if risk_score >= 60:
    status_label, status_label_en, status_color = "ไม่ดี (อันตราย)", "DANGER", "var(--danger)"
elif risk_score >= 30:
    status_label, status_label_en, status_color = "ปานกลาง (เฝ้าระวัง)", "WARNING", "var(--warn)"
else:
    status_label, status_label_en, status_color = "ดี (ปกติ / ปลอดภัย)", "GOOD", "var(--safe)"

now = datetime.now()
current_time_str = now.strftime("%H:%M")
current_date_str = now.strftime("%Y-%m-%d")

# --- UI HELPERS ---
def zone_color(value, zones):
    for lo, hi, color in zones:
        if lo <= value < hi:
            return color
    return zones[-1][2]

def gradient_from_zones(zones, vmin, vmax):
    span = vmax - vmin
    stops = []
    for lo, hi, color in zones:
        p1 = max(0, min(100, (lo - vmin) / span * 100))
        p2 = max(0, min(100, (hi - vmin) / span * 100))
        stops.append(f"var({color}) {p1:.1f}%, var({color}) {p2:.1f}%")
    return "linear-gradient(90deg, " + ", ".join(stops) + ")"

def render_gauge_card(icon, label, value, unit, vmin, vmax, zones, fmt="{:.1f}"):
    clipped = max(vmin, min(vmax, value))
    pct = (clipped - vmin) / (vmax - vmin) * 100
    color = zone_color(value, zones)
    gradient = gradient_from_zones(zones, vmin, vmax)
    html = f"""<div class="gauge-card">
<div class="gauge-top">
<span class="gauge-label">{label}</span>
<span class="gauge-icon">{icon}</span>
</div>
<div class="gauge-value" style="color:{color}">{fmt.format(value)}<span class="gauge-unit">{unit}</span></div>
<div class="gauge-track" style="background:{gradient}">
<div class="gauge-marker" style="left:{pct:.1f}%"></div>
</div>
<div class="gauge-range"><span>{vmin}</span><span>{vmax}</span></div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_risk_ring(score, status_color_css, size=132, stroke=12):
    r = (size - stroke) / 2
    circumference = 2 * math.pi * r
    dash = circumference * (score / 100)
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="transform: rotate(-90deg); flex-shrink:0;">
<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="rgba(148,163,184,0.12)" stroke-width="{stroke}"/>
<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{status_color_css}" stroke-width="{stroke}" stroke-dasharray="{dash:.1f} {circumference:.1f}" stroke-linecap="round"/>
</svg>"""

tab1, tab2 = st.tabs(["📊 ภาพรวมคุณภาพน้ำ (Dashboard)", "🏡 ระบบสนับสนุนการตัดสินใจ"])

with tab1:
    hcol1, hcol2 = st.columns([3, 1])
    with hcol1:
        st.markdown('<div class="hdr-eyebrow">EEC · WATER TELEMETRY</div>', unsafe_allow_html=True)
        st.markdown('<div class="hdr-title">💧 ระบบตรวจสอบคุณภาพน้ำชุมชน</div>', unsafe_allow_html=True)
        st.markdown('<div class="hdr-sub">แสดงสถานะความพร้อมและคุณภาพน้ำสำหรับการอุปโภคบริโภค</div>', unsafe_allow_html=True)
    with hcol2:
        pill_html = f"""<div style="text-align:right; padding-top: 8px;">
<span class="status-pill" style="--pill-color:{status_color}">
<span class="status-dot"></span>{status_label}
</span>
</div>"""
        st.markdown(pill_html, unsafe_allow_html=True)

    st.markdown(f'<div class="data-badge">{data_source_badge}</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # 5 เกจวัดค่าพารามิเตอร์
    g1, g2, g3, g4, g5 = st.columns(5, gap="medium")
    with g1:
        render_gauge_card("⚗️", "PH LEVEL", ph, "", 0, 14,
            [(0, 5.5, "--danger"), (5.5, 6.5, "--warn"), (6.5, 8.5, "--safe"), (8.5, 9.0, "--warn"), (9.0, 14, "--danger")])
    with g2:
        render_gauge_card("🧂", "TDS / EC", tds, "ppm", 0, 1200,
            [(0, 600, "--safe"), (600, 1000, "--warn"), (1000, 1200, "--danger")])
    with g3:
        render_gauge_card("🌡️", "TEMPERATURE", temp, "°C", 10, 45,
            [(10, 35, "--safe"), (35, 45, "--danger")])
    with g4:
        render_gauge_card("🫧", "DISSOLVED O₂", do_val, "mg/L", 0, 20,
            [(0, 3, "--danger"), (3, 5, "--warn"), (5, 20, "--safe")])
    with g5:
        render_gauge_card("🌫️", "TURBIDITY", turbidity, "NTU", 0, 300,
            [(0, 100, "--safe"), (100, 300, "--danger")])

    st.write("")
    col2, col3 = st.columns([1.6, 1], gap="medium")

    with col2:
        st.markdown('<div class="panel" style="margin-bottom: 0;"><div class="panel-title">📈 แนวโน้มคุณภาพน้ำ (ดี / ไม่ดี) <span class="tag">TREND STATUS</span></div>', unsafe_allow_html=True)
        chart_data_1 = pd.DataFrame({
            'สถานะภาพน้ำ (ดี=สูง, ไม่ดี=ต่ำ)': np.random.uniform(70, 95, 10) if risk_score < 30 else np.random.uniform(20, 45, 10)
        })
        st.area_chart(chart_data_1, color=["#34d399" if risk_score < 30 else "#f87171"], height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        status_text_desc = "น้ำอยู่ในเกณฑ์ **ดี (ปลอดภัย)** สามารถใช้งานได้ตามปกติ" if risk_score < 30 else "น้ำอยู่ในเกณฑ์ **ไม่ดี (ต้องระวัง)** ควรตรวจสอบระบบกรอง"
        ring_svg = render_risk_ring(risk_score, status_color)
        risk_html = f"""<div class="panel">
<div class="panel-title">🤖 สรุปภาพรวมคุณภาพน้ำ <span class="tag">EVALUATION</span></div>
<div class="risk-wrap">
<div style="position:relative; width:132px; height:132px;">
{ring_svg}
<div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;">
<span class="risk-figure" style="font-size:1.9rem; color:{status_color};">{risk_score}%</span>
</div>
</div>
<div>
<div class="risk-status-label" style="color:{status_color}">{status_label}</div>
<div style="font-size:0.78rem; color:var(--text-low); font-family:'JetBrains Mono',monospace;">STATUS SCORE</div>
</div>
</div>
<div class="risk-advice">💡 <b>คำแนะนำ:</b> {status_text_desc}</div>
</div>"""
        st.markdown(risk_html, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="hdr-eyebrow">DECISION SUPPORT</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title" style="font-size:1.5rem;">🏡 ระบบสนับสนุนการตัดสินใจสำหรับชุมชน</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    if risk_score < 30:
        st.success("✅ สถานะน้ำในระบบปกติ ดีเยี่ยม พร้อมแจกจ่ายเพื่ออุปโภคบริโภค")
    else:
        st.warning("⚠️ ตรวจพบความผิดปกติของค่าน้ำ กรุณาตรวจสอบระบบประปาหมู่บ้าน")

time.sleep(60)
st.rerun()
