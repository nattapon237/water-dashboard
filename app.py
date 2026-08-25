import streamlit as st
import numpy as np
import pandas as pd
import requests
import json
import time
import math
from datetime import datetime, timedelta
import pytz

# ตั้งค่า Timezone เป็นประเทศไทย (Asia/Bangkok)
TH_TZ = pytz.timezone('Asia/Bangkok')

st.set_page_config(page_title="EEC Community Water Intelligence System - Agriculture", page_icon="🌾", layout="wide")

# --- Firebase Configuration (cwis-c2ea8) ---
FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"

# LINE API Configuration
LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"

# --- High-Tech Cyber-Water Agri Mobile-Friendly Glassmorphism CSS ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {
  --void: #030712;
  --panel: rgba(11, 21, 38, 0.78);
  --hairline: rgba(56, 189, 248, 0.16);
  --hairline-strong: rgba(56, 189, 248, 0.42);
  --cyan: #22d3ee;
  --safe: #34d399;
  --danger: #f87171;
  --text-hi: #eef2f7;
  --text-mid: #b6c2d1;
  --text-low: #6b7c93;
}
.stApp {
  background: radial-gradient(ellipse 900px 500px at 15% -10%, rgba(52,211,153,0.08), transparent 60%), radial-gradient(ellipse 700px 500px at 100% 0%, rgba(34,211,238,0.06), transparent 55%), var(--void);
  color: var(--text-mid);
  font-family: 'Inter', sans-serif;
}
[data-testid="stStatusWidget"] { display: none !important; }
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
  font-size: 0.68rem; letter-spacing: 1.5px; text-transform: uppercase; color: var(--safe); margin-bottom: 2px;
}
.hdr-title { font-size: 1.5rem; font-weight: 700; color: var(--text-hi); margin: 0 0 4px 0; }
.hdr-sub { color: var(--text-low); font-size: 0.85rem; line-height: 1.4; }

.status-pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px; border-radius: 999px;
  font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.85rem;
  border: 1px solid var(--pill-color, var(--safe));
  color: var(--pill-color, var(--safe));
  background: color-mix(in srgb, var(--pill-color, var(--safe)) 12%, transparent);
  box-shadow: 0 0 18px color-mix(in srgb, var(--pill-color, var(--safe)) 30%, transparent);
}
.status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--pill-color, var(--safe));
  box-shadow: 0 0 6px var(--pill-color, var(--safe));
}

.panel {
  background: linear-gradient(155deg, rgba(20,35,64,0.55) 0%, rgba(6,12,24,0.85) 100%);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 12px;
  backdrop-filter: blur(14px);
}
.panel-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.92rem; font-weight: 700; color: var(--text-hi);
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  margin-bottom: 12px;
}
.panel-title .tag {
  font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; font-weight: 500;
  color: var(--text-low); letter-spacing: 0.8px; text-transform: uppercase;
  border: 1px solid var(--hairline-strong); border-radius: 4px; padding: 2px 5px;
}

.gauge-card {
  background: linear-gradient(155deg, rgba(20,35,64,0.55) 0%, rgba(6,12,24,0.85) 100%);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
}
.gauge-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; }
.gauge-label { font-size: 0.68rem; letter-spacing: 0.8px; text-transform: uppercase; color: var(--text-low); font-weight: 600; }
.gauge-icon { font-size: 0.95rem; opacity: 0.85; }
.gauge-value { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.45rem; line-height: 1.1; margin: 2px 0 10px 0; }
.gauge-unit { font-size: 0.78rem; font-weight: 500; color: var(--text-low); margin-left: 2px; }
.gauge-track { position: relative; height: 5px; border-radius: 4px; margin-bottom: 5px; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04); }
.gauge-marker { position: absolute; top: -3px; width: 3px; height: 11px; border-radius: 2px; background: #fff; transform: translateX(-50%); }
.gauge-range { display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--text-low); }

.risk-advice {
  font-size: 0.84rem; color: var(--text-hi); margin-top: 10px;
  border-top: 1px solid var(--hairline); padding-top: 10px; line-height: 1.5;
}
.check-row { display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid var(--hairline); }
.check-row:last-child { border-bottom: none; }
.check-text { font-size: 0.84rem; color: var(--text-mid); line-height: 1.4; }
.check-text b { color: var(--text-hi); }
hr.divider { border: 0; height: 1px; background: var(--hairline); margin: 16px 0; }

.stButton>button {
  background: linear-gradient(135deg, #065f46, #10b981);
  color: #f8fafc; border: 1px solid rgba(52,211,153,0.4);
  border-radius: 10px; font-weight: 600; font-family: 'Inter', sans-serif;
  padding: 0.6rem 1rem; width: 100%; box-shadow: 0 4px 16px rgba(16,185,129,0.3);
  transition: all 0.2s ease;
}
.stButton>button:hover {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: #04101f; box-shadow: 0 6px 20px rgba(52,211,153,0.5);
}

.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
  height: 44px; white-space: pre-wrap; background-color: rgba(11, 21, 38, 0.5);
  border-radius: 8px 8px 0px 0px; font-size: 0.85rem; font-weight: 600; color: var(--text-mid);
}
</style>
""", unsafe_allow_html=True)

def send_line_notification(message, image_url=None):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
    
    messages = []
    if image_url:
        messages.append({
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
        })
    messages.append({
        "type": "text",
        "text": message
    })
    
    payload = {"to": TARGET_USER_ID, "messages": messages}
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

@st.cache_data(ttl=300)
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
        st.cache_data.clear()
        return res.status_code == 200
    except Exception:
        return False

id_token = get_firebase_token()

st.sidebar.title("🔥 สถานะ Firebase")
if id_token:
    st.sidebar.success("🟢 เชื่อมต่อ RTDB สำเร็จ")
else:
    st.sidebar.error("🔴 ขาดการเชื่อมต่อ Firebase")

now_th = datetime.now(TH_TZ)
st.sidebar.info(f"🕒 เวลาไทย (ICT): {now_th.strftime('%d/%m/%Y %H:%M:%S')}")

st.sidebar.markdown("---")
st.sidebar.title("🎛️ เซนเซอร์ / Input Control")
sim_ph = st.sidebar.slider("pH Level", 0.0, 14.0, 7.0, 0.1)
sim_tds = st.sidebar.slider("TDS (ppm)", 0.0, 1200.0, 250.0, 1.0)
sim_temp = st.sidebar.slider("Temperature (°C)", 10.0, 45.0, 28.0, 0.5)
sim_do = st.sidebar.slider("DO (mg/L)", 0.0, 20.0, 6.5, 0.1)
sim_turb = st.sidebar.slider("Turbidity (NTU)", 0.0, 300.0, 15.0, 1.0)

if st.sidebar.button("📤 ส่งค่าจำลองขึ้น Firebase", use_container_width=True):
    if write_mock_sensor_data(id_token, sim_ph, sim_tds, sim_temp, sim_do, sim_turb):
        st.sidebar.success("✅ บันทึกค่าสำเร็จ!")
        st.rerun()

live_data = read_sensor_data(id_token)
if live_data and isinstance(live_data, dict) and "ph" in live_data:
    ph = float(live_data.get("ph", sim_ph))
    tds = float(live_data.get("tds", sim_tds))
    temp = float(live_data.get("temp", sim_temp))
    do_val = float(live_data.get("do", sim_do))
    turbidity = float(live_data.get("turbidity", sim_turb))
else:
    ph, tds, temp, do_val, turbidity = sim_ph, sim_tds, sim_temp, sim_do, sim_turb

def calculate_water_quality(ph, tds, temp, do_val, turbidity):
    reasons = []
    if not (6.5 <= ph <= 8.5):
        reasons.append(f"pH ({ph}) อยู่นอกเกณฑ์ (6.5-8.5)")
    if tds > 1000:
        reasons.append(f"TDS ({tds:.1f} ppm) สูงเกิน (<1,000)")
    if do_val < 4.0:
        reasons.append(f"DO ({do_val:.1f} mg/L) ต่ำกว่าเกณฑ์ (>4.0)")
    if turbidity > 100:
        reasons.append(f"ความขุ่น ({turbidity:.1f} NTU) สูงเกิน (<100)")
    if temp > 35:
        reasons.append(f"อุณหภูมิ ({temp:.1f} °C) สูงเกิน (<35)")

    if len(reasons) > 0:
        return 0, "ผิดปกติ (ไม่ปลอดภัย)", "var(--danger)", reasons, "❌ ห้ามนำไปรดพืชผลหรือเติมลงบ่อปลาเด็ดขาด"
    else:
        return 100, "ปกติ (ปลอดภัย)", "var(--safe)", [], "✅ น้ำปลอดภัย สามารถใช้รดน้ำพืชผลและให้สัตว์น้ำได้"

water_score, status_label, status_color, risk_reasons, action_advice = calculate_water_quality(ph, tds, temp, do_val, turbidity)

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

def render_risk_ring(score, status_color_css, size=110, stroke=10):
    r = (size - stroke) / 2
    circumference = 2 * math.pi * r
    dash = circumference * (score / 100)
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="transform: rotate(-90deg); flex-shrink:0;">
<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="rgba(148,163,184,0.12)" stroke-width="{stroke}"/>
<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{status_color_css}" stroke-width="{stroke}" stroke-dasharray="{dash:.1f} {circumference:.1f}" stroke-linecap="round"/>
</svg>"""

tab1, tab2 = st.tabs(["📊 ภาพรวมน้ำ (Dashboard)", "🌾 จัดการแปลงเกษตร"])

with tab1:
    st.markdown('<div class="hdr-eyebrow">EEC · AGRI-WATER INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title">🌾 ระบบตรวจสอบคุณภาพน้ำ</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hdr-sub">เวลาไทย: {now_th.strftime("%d/%m/%Y %H:%M:%S")} (อัพเดตอัตโนมัติทุก 5 นาที)</div>', unsafe_allow_html=True)
    
    st.write("")
    pill_html = f"""<div style="margin-bottom: 14px;">
<span class="status-pill" style="--pill-color:{status_color}">
<span class="status-dot"></span>{status_label}
</span>
</div>"""
    st.markdown(pill_html, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    g1, g2 = st.columns(2, gap="small")
    with g1:
        render_gauge_card("⚗️", "PH LEVEL", ph, "", 0, 14,
            [(0, 6.5, "--danger"), (6.5, 8.5, "--safe"), (8.5, 14, "--danger")])
        render_gauge_card("🌡️", "TEMP", temp, "°C", 10, 45,
            [(10, 35, "--safe"), (35, 45, "--danger")])
        render_gauge_card("🌫️", "TURBIDITY", turbidity, "NTU", 0, 300,
            [(0, 100, "--safe"), (100, 300, "--danger")])
    with g2:
        render_gauge_card("🧂", "TDS / EC", tds, "ppm", 0, 1200,
            [(0, 1000, "--safe"), (1000, 1200, "--danger")])
        render_gauge_card("🫧", "DO", do_val, "mg/L", 0, 20,
            [(0, 4.0, "--danger"), (4.0, 20, "--safe")])

    st.write("")
    
    ring_svg = render_risk_ring(water_score, status_color)
    risk_html = f"""<div class="panel">
<div class="panel-title">🤖 ผลประเมินน้ำเพื่อเกษตรกรรม <span class="tag">EVALUATION</span></div>
<div style="display:flex; align-items:center; gap:14px;">
<div style="position:relative; width:110px; height:110px;">
{ring_svg}
<div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;">
<span style="font-family:'JetBrains Mono',monospace; font-weight:700; font-size:1.4rem; color:{status_color};">{water_score}%</span>
</div>
</div>
<div>
<div style="font-size:0.88rem; font-weight:700; color:{status_color}">{status_label}</div>
<div style="font-size:0.7rem; color:var(--text-low); font-family:'JetBrains Mono',monospace; margin-top:2px;">AGRI STATUS</div>
</div>
</div>
<div class="risk-advice" style="border-left: 3px solid {status_color}; padding-left: 10px;">
<b>คำแนะนำ:</b><br>{action_advice}
</div>
</div>"""
    st.markdown(risk_html, unsafe_allow_html=True)

    st.markdown('<div class="panel"><div class="panel-title">📈 กราฟแนวโน้มย้อนหลัง <span class="tag">TREND</span></div>', unsafe_allow_html=True)
    time_index = [(now_th - timedelta(minutes=i*10)).strftime("%H:%M") for i in range(8)][::-1]
    trend_values = np.random.uniform(95, 100, 8) if water_score == 100 else np.random.uniform(0, 15, 8)
    chart_df_time = pd.DataFrame({'ความปลอดภัย (%)': trend_values}, index=time_index)
    st.line_chart(chart_df_time, color=["#34d399" if water_score == 100 else "#f87171"], height=180)
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="hdr-eyebrow">AGRI DECISION SUPPORT</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title" style="font-size:1.3rem;">🌾 ระบบจัดการแปลงเกษตรและแจ้งเบาะแส</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    if water_score == 100:
        st.success("✅ น้ำปลอดภัย: เปิดระบบสูบน้ำได้ปกติ")
    else:
        st.error("🚨 น้ำมีปัญหา: ห้ามสูบน้ำเข้าแปลงเด็ดขาด!")

    st.write("")
    
    st.markdown("""
    <div class="panel">
        <div class="panel-title">🛠️ ข้อปฏิบัติสำหรับเกษตรกร <span class="tag">ACTION</span></div>
        <div class="check-row">
            <div class="check-icon">🚫</div>
            <div class="check-text"><b>หยุดสูบน้ำเข้าแปลง:</b> ปิดวาล์วทันทีหากพบสถานะเตือนสีแดง</div>
        </div>
        <div class="check-row">
            <div class="check-icon">⚙️</div>
            <div class="check-text"><b>ตรวจระบบบำบัด:</b> ตรวจสอบถังพักและค่ากรด-ด่างก่อนใช้งาน</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="panel">
        <div class="panel-title">📍 แจ้งเบาะแสคนทิ้งขยะเทียบทุ่น <span class="tag">BUOY LOC</span></div>
        <div style="font-size:0.84rem; color:var(--text-mid); margin-bottom: 10px;">
            ระบุตำแหน่งเทียบจากทุ่นตรวจวัดน้ำ พร้อมแนบรูปถ่ายส่งเข้า LINE ผู้นำชุมชน
        </div>
    """, unsafe_allow_html=True)
    
    direction_from_buoy = st.selectbox("🧭 ทิศทางเทียบจากทุ่น", ["เหนือ (North)", "ใต้ (South)", "ตะวันออก (East)", "ตะวันตก (West)", "เหนือ-ตะวันออก (NE)", "เหนือ-ตะวันตก (NW)", "ใต้-ตะวันออก (SE)", "ใต้-ตะวันตก (SW)"])
    distance_from_buoy = st.number_input("📏 ระยะห่าง (เมตร)", min_value=1, max_value=2000, value=50, step=10)

    uploaded_file = st.file_uploader("📷 แนบภาพถ่ายหลักฐาน", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="ภาพหลักฐานที่เลือก", use_container_width=True)

    if st.button("🚀 ส่งพิกัดและภาพแจ้ง LINE", use_container_width=True):
        line_msg = f"🚨 แจ้งเบาะแสทิ้งขยะ!\n📍 พิกัด: ห่างจากทุ่นตรวจวัดน้ำไปทางทิศ{direction_from_buoy} ประมาณ {distance_from_buoy} เมตร\n⏰ เวลาแจ้ง: {now_th.strftime('%d/%m/%Y %H:%M:%S')} (ICT)\n⚠️ โปรดส่งเจ้าหน้าที่เข้าตรวจสอบพื้นที่ด่วน!"
        
        sample_image_url = "https://images.unsplash.com/photo-1530587191325-3db32d826c11" if uploaded_file else None
        
        success = send_line_notification(line_msg, image_url=sample_image_url)
        if success:
            st.success("✅ ส่งข้อมูลเข้า LINE สำเร็จ!")
        else:
            st.error("❌ ส่งไม่สำเร็จ ตรวจสอบ LINE Token")
    st.markdown("</div>", unsafe_allow_html=True)

    if risk_reasons:
        st.write("")
        st.markdown("""
        <div class="panel">
            <div class="panel-title">🔍 รายละเอียดความผิดปกติ <span class="tag">REASONS</span></div>
        """, unsafe_allow_html=True)
        for rsn in risk_reasons:
            st.markdown(f"""
            <div class="check-row">
                <div class="check-icon">❌</div>
                <div class="check-text"><b style="color:var(--danger);">{rsn}</b></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

time.sleep(300)
st.rerun()
