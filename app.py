import streamlit as st
import numpy as np
import pandas as pd
import requests
import json
import time
import math
import base64
from datetime import datetime, timedelta
import pytz
import altair as alt
import streamlit.components.v1 as components

# ==========================================
# 0. CONFIGURATION & SETUP
# ==========================================
TH_TZ = pytz.timezone('Asia/Bangkok')

st.set_page_config(
    page_title="Smart Water Quality Monitoring System", 
    page_icon="💧", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# กำหนดค่าเกณฑ์ SENSOR (Thresholds สำหรับประเมินคุณภาพน้ำ)
PH_MIN = 6.5
PH_MAX = 8.5
TDS_MAX = 1000.0
ORP_MIN = 200.0
TURBIDITY_MAX = 100.0
DO_MIN = 4.0

# พิกัดจุดติดตั้ง Sensor ตามที่กำหนด
STATION_LAT = 13.689108
STATION_LON = 101.079153

FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"

# ----------------------------------------------------
# Custom CSS สำหรับ Light Theme (ธีมสีขาวสะอาดตา สไตล์โมเดิร์น)
# ----------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #334155;
    }

    .hdr-eyebrow {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #0284c7;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .hdr-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .hdr-sub {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 12px;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        color: var(--pill-color, #0f172a);
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--pill-color, #0f172a);
    }

    .gauge-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .gauge-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .gauge-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .gauge-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #64748b;
        letter-spacing: 0.05em;
    }
    .gauge-icon {
        font-size: 1.1rem;
    }
    .gauge-value {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .gauge-unit {
        font-size: 0.8rem;
        font-weight: 500;
        color: #94a3b8;
        margin-left: 4px;
    }
    .gauge-track {
        position: relative;
        height: 8px;
        border-radius: 4px;
        background: #e2e8f0;
        margin-bottom: 6px;
        overflow: hidden;
    }
    .gauge-marker {
        position: absolute;
        top: -2px;
        width: 4px;
        height: 12px;
        background: #0f172a;
        border-radius: 2px;
        transform: translateX(-50%);
        box-shadow: 0 0 2px rgba(0,0,0,0.3);
    }
    .gauge-range {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        color: #94a3b8;
    }

    .panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }
    .panel-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .tag {
        font-size: 0.65rem;
        padding: 2px 8px;
        background: #e0f2fe;
        color: #0284c7;
        border-radius: 6px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .divider {
        border: none;
        height: 1px;
        background-color: #e2e8f0;
        margin: 16px 0;
    }

    :root {
        --safe: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. FIREBASE AUTH & DATA FETCHING
# ==========================================
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

@st.cache_data(ttl=15)
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

@st.cache_data(ttl=15)
def read_history_data(id_token):
    if not id_token:
        return None
    url = f"{FIREBASE_DB_URL}/devices/uno-r4/history.json?auth={id_token}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None

id_token = get_firebase_token()
live_data = read_sensor_data(id_token)
history_raw = read_history_data(id_token)

# ==========================================
# 2. PARSE SENSOR & ONLINE STATUS
# ==========================================
db_connected = id_token is not None
ph, tds, turbidity, do_val, updated_at = None, None, None, None, None

if live_data and isinstance(live_data, dict):
    ph = live_data.get("ph") if live_data.get("ph") is not None else live_data.get("pH")
    tds = live_data.get("tds") if live_data.get("tds") is not None else live_data.get("TDS")
    turbidity = live_data.get("turbidity") if live_data.get("turbidity") is not None else live_data.get("Turbidity")
    do_val = live_data.get("do") if live_data.get("do") is not None else live_data.get("DO")
    updated_at = live_data.get("updatedAt") or live_data.get("timestamp")

is_online = False
if updated_at is not None:
    try:
        current_epoch = time.time()
        time_diff = current_epoch - int(updated_at)
        if time_diff <= 300: # 5 นาที
            is_online = True
    except:
        pass

# ==========================================
# 4. RULE-BASED WATER QUALITY EVALUATION
# ==========================================
def calculate_water_quality(tds, turbidity, do_val):
    if tds is None or turbidity is None:
        return 0, "รอข้อมูล", "var(--warning)", ["ยังไม่มีข้อมูลจาก Sensor"], "กรุณารอข้อมูลอัปเดตจากอุปกรณ์"

    reasons = []
    status_score = 100

    if tds > TDS_MAX:
        reasons.append(f"ค่า TDS ({tds} ppm) สูงเกินเกณฑ์ (<{TDS_MAX})")
        status_score -= 40

    if turbidity > TURBIDITY_MAX:
        reasons.append(f"ความขุ่น ({turbidity} NTU) สูงเกินเกณฑ์ (<{TURBIDITY_MAX})")
        status_score -= 35

    if do_val is not None and do_val < DO_MIN:
        reasons.append(f"ค่า DO ({do_val} mg/L) ต่ำกว่าเกณฑ์ (>{DO_MIN})")
        status_score -= 25

    if status_score == 100:
        return 100, "ปกติ", "var(--safe)", [], "✅ คุณภาพน้ำอยู่ในเกณฑ์ปกติ เหมาะสมตามระบบนิเวศจำเพาะ"
    elif status_score >= 50:
        return status_score, "เฝ้าระวัง", "var(--warning)", reasons, "⚠️ ควรตรวจสอบความผิดปกติของแหล่งน้ำหรืออัตราการไหล"
    else:
        return max(0, status_score), "ผิดปกติ", "var(--danger)", reasons, "❌ ตรวจพบความผิดปกติของค่าพารามิเตอร์น้ำ ห้ามใช้น้ำชั่วคราว"

water_score, status_label, status_color, risk_reasons, action_advice = calculate_water_quality(tds, turbidity, do_val)

def get_parameter_status(val, param_type):
    if val is None:
        return "รอข้อมูล", "var(--warning)"
    if param_type == "tds":
        if val <= TDS_MAX: return "ปกติ", "var(--safe)"
        return "ผิดปกติ", "var(--danger)"
    elif param_type == "turbidity":
        if val <= TURBIDITY_MAX: return "ปกติ", "var(--safe)"
        return "ผิดปกติ", "var(--danger)"
    elif param_type == "do":
        if val >= DO_MIN: return "ปกติ", "var(--safe)"
        return "เฝ้าระวัง", "var(--warning)"
    return "ปกติ", "var(--safe)"

tds_status, _ = get_parameter_status(tds, "tds")
turb_status, _ = get_parameter_status(turbidity, "turbidity")
do_status, _ = get_parameter_status(do_val, "do")

# ==========================================
# 18. SIDEBAR CONFIGURATION
# ==========================================
st.sidebar.title("💧 WATER QUALITY SYSTEM")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🔌 สถานะระบบ")
if db_connected:
    st.sidebar.markdown("Firebase RTDB: <span style='color:#10b981; font-weight:700;'>🟢 Connected</span>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("Firebase RTDB: <span style='color:#ef4444; font-weight:700;'>🔴 Disconnected</span>", unsafe_allow_html=True)

if is_online:
    st.sidebar.markdown("Sensor Status: <span style='color:#10b981; font-weight:700;'>🟢 SENSOR ONLINE</span>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("Sensor Status: <span style='color:#ef4444; font-weight:700;'>🔴 SENSOR OFFLINE</span>", unsafe_allow_html=True)

now_th = datetime.now(TH_TZ)
st.sidebar.markdown(f"🕒 เวลาไทย: **{now_th.strftime('%d/%m/%Y %H:%M:%S')}**")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("<div style='font-size:0.75rem; color:#64748b; text-align:center; margin-top:20px;'>EEC Water Intelligence System v2.0</div>", unsafe_allow_html=True)

# ==========================================
# 6. GAUGE & UI HELPER FUNCTIONS
# ==========================================
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
    if value is None:
        val_str = "--"
        color = "#94a3b8"
        pct = 0
        gradient = "#e2e8f0"
    else:
        val_str = fmt.format(value)
        clipped = max(vmin, min(vmax, value))
        pct = (clipped - vmin) / (vmax - vmin) * 100
        color = zone_color(value, zones)
        gradient = gradient_from_zones(zones, vmin, vmax)

    html = f"""<div class="gauge-card">
<div class="gauge-top">
<span class="gauge-label">{label}</span>
<span class="gauge-icon">{icon}</span>
</div>
<div class="gauge-value" style="color:{color}">{val_str}<span class="gauge-unit">{unit}</span></div>
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
<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#e2e8f0" stroke-width="{stroke}"/>
<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{status_color_css}" stroke-width="{stroke}" stroke-dasharray="{dash:.1f} {circumference:.1f}" stroke-linecap="round"/>
</svg>"""

# ==========================================
# 20. PAGE TABS STRUCTURE
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 ประวัติข้อมูล", "📍 จุดติดตั้ง Sensor"])

# ==========================================
# TAB 1: DASHBOARD
# ==========================================
with tab1:
    st.markdown('<div class="hdr-eyebrow">SMART WATER QUALITY MONITORING SYSTEM</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title">💧 ระบบตรวจวัดคุณภาพแหล่งน้ำอัจฉริยะ</div>', unsafe_allow_html=True)
    
    updated_str = "รอข้อมูล"
    if updated_at:
        try:
            dt_utc = datetime.fromtimestamp(int(updated_at), tz=pytz.utc)
            dt_th = dt_utc.astimezone(TH_TZ)
            updated_str = dt_th.strftime('%d/%m/%Y %H:%M:%S')
        except:
            updated_str = str(updated_at)
            
    st.markdown(f'<div class="hdr-sub">ระบบตรวจวัดและติดตามคุณภาพน้ำ | อัปเดตล่าสุด: {updated_str}</div>', unsafe_allow_html=True)
    
    status_badge_text = "🟢 SENSOR ONLINE" if is_online else "🔴 SENSOR OFFLINE"
    status_badge_color = "var(--safe)" if is_online else "var(--danger)"
    if not live_data:
        status_badge_text = "🔴 ไม่สามารถเชื่อมต่อ Sensor"
        
    pill_html = f"""<div style="margin-bottom: 14px;">
<span class="status-pill" style="--pill-color:{status_badge_color}">
<span class="status-dot"></span>{status_badge_text}
</span>
</div>"""
    st.markdown(pill_html, unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # CARDS แสดงผลเซนเซอร์จาก ESP32 (TDS, Turbidity, DO/ORP)
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        render_gauge_card("🧂", "TDS SENSOR", tds, "ppm", 0, 1200, 
            [(0, TDS_MAX, "--safe"), (TDS_MAX, 1200, "--danger")], fmt="{:.1f}")
    with c2:
        render_gauge_card("🌫️", "TURBIDITY", turbidity, "NTU", 0, 300, 
            [(0, TURBIDITY_MAX, "--safe"), (TURBIDITY_MAX, 300, "--danger")], fmt="{:.1f}")
    with c3:
        render_gauge_card("🫧", "DO / MAPPED ORP", do_val, "mg/L", 0, 14, 
            [(0, DO_MIN, "--danger"), (DO_MIN, 14, "--safe")], fmt="{:.1f}")

    st.write("")

    reasons_list_html = ""
    if risk_reasons:
        reasons_list_html = "<div style='margin-top: 8px; font-size: 0.85rem; color: #ef4444;'>"
        for rsn in risk_reasons:
            reasons_list_html += f"• {rsn}<br>"
        reasons_list_html += "</div>"
    else:
        reasons_list_html = "<div style='margin-top: 8px; font-size: 0.85rem; color: #10b981;'>• ทุกค่าพารามิเตอร์อยู่ในเกณฑ์มาตรฐานปกติ</div>"

    ring_svg = render_risk_ring(water_score, status_color)
    risk_html = f"""<div class="panel">
<div class="panel-title">🤖 ผลการประเมินคุณภาพน้ำโดยรวม <span class="tag">RULE-BASED EVALUATION</span></div>
<div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
{ring_svg}
<div style="flex-grow: 1;">
<div style="font-size: 1.2rem; font-weight: 700; color: #0f172a;">สถานะคุณภาพน้ำ: <span style="color:{status_color}">{status_label}</span> (คะแนน: {water_score}/100)</div>
<div style="font-size: 0.88rem; color: #475569; margin-top: 6px;"><b>คำแนะนำระบบ:</b> {action_advice}</div>
{reasons_list_html}
</div>
</div>
</div>"""
    st.markdown(risk_html, unsafe_allow_html=True)

    # 13. SENSOR STATUS TABLE
    st.markdown("""
    <div class="panel">
        <div class="panel-title">📋 ตารางสรุปสถานะเซนเซอร์ปัจจุบัน <span class="tag">REAL-TIME TABLE</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    table_data = [
        {"Sensor": "TDS", "ค่า": f"{tds:.1f}" if tds is not None else "--", "หน่วย": "ppm", "สถานะ": tds_status},
        {"Sensor": "Turbidity", "ค่า": f"{turbidity:.1f}" if turbidity is not None else "--", "หน่วย": "NTU", "สถานะ": turb_status},
        {"Sensor": "DO (Mapped ORP)", "ค่า": f"{do_val:.1f}" if do_val is not None else "--", "หน่วย": "mg/L", "สถานะ": do_status},
    ]
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    st.write("")

    # GRAPHS & HISTORY PROCESSING
    st.markdown("""
    <div class="panel">
        <div class="panel-title">📈 กราฟแสดงแนวโน้มคุณภาพน้ำ <span class="tag">REAL-TIME CHARTS</span></div>
    </div>
    """, unsafe_allow_html=True)

    df_history = pd.DataFrame()
    if history_raw and isinstance(history_raw, dict):
        hist_list = []
        for k, v in history_raw.items():
            if isinstance(v, dict):
                ts = v.get("timestamp") or v.get("updatedAt") or k
                try:
                    ts_val = int(ts)
                    dt_val = datetime.fromtimestamp(ts_val, tz=TH_TZ)
                except:
                    dt_val = pd.to_datetime(ts)
                
                hist_list.append({
                    "time": dt_val,
                    "tds": float(v.get("tds") or v.get("TDS", np.nan)),
                    "turbidity": float(v.get("turbidity") or v.get("Turbidity", np.nan)),
                    "do": float(v.get("do") or v.get("DO", np.nan)),
                })
        if hist_list:
            df_history = pd.DataFrame(hist_list)
            df_history = df_history.sort_values("time")

    if not df_history.empty:
        g_col1, g_col2 = st.columns(2, gap="medium")
        with g_col1:
            st.markdown("##### 📈 ค่า TDS ย้อนหลัง")
            chart_tds = alt.Chart(df_history).mark_line(point=True, color="#10b981").encode(
                x=alt.X('time:T', title='เวลา'),
                y=alt.Y('tds:Q', title='TDS (ppm)'),
                tooltip=['time:T', 'tds:Q']
            ).properties(height=230).interactive()
            st.altair_chart(chart_tds, use_container_width=True)

        with g_col2:
            st.markdown("##### 📈 ค่าความขุ่น (Turbidity) ย้อนหลัง")
            chart_turb = alt.Chart(df_history).mark_line(point=True, color="#f59e0b").encode(
                x=alt.X('time:T', title='เวลา'),
                y=alt.Y('turbidity:Q', title='Turbidity (NTU)'),
                tooltip=['time:T', 'turbidity:Q']
            ).properties(height=230).interactive()
            st.altair_chart(chart_turb, use_container_width=True)
    else:
        st.info("ℹ️ ยังไม่มีข้อมูลประวัติเพียงพอสำหรับสร้างกราฟ (กำลังรอข้อมูลจาก /devices/uno-r4/history/)")

    st.write("")

    # SENSOR LOCATION MAP
    st.markdown("""
    <div class="panel">
        <div class="panel-title">📍 แผนที่จุดติดตั้ง Sensor <span class="tag">GIS LOCATION</span></div>
    </div>
    """, unsafe_allow_html=True)

    leaflet_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            #map {{ width: 100%; height: 350px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{STATION_LAT}, {STATION_LON}], 15);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors'
            }}).addTo(map);

            var marker = L.marker([{STATION_LAT}, {STATION_LON}]).addTo(map);
            marker.bindPopup("<b>📍 Sensor Station 01</b><br>จุดตรวจวัดคุณภาพน้ำ 01<br>TDS: {tds if tds is not None else '--'} ppm<br>Turbidity: {turbidity if turbidity is not None else '--'} NTU<br>DO: {do_val if do_val is not None else '--'} mg/L<br>สถานะ: {'Online' if is_online else 'Offline'}<br>พิกัด: {STATION_LAT}, {STATION_LON}").openPopup();
        </script>
    </body>
    </html>
    """
    components.html(leaflet_html, height=370)

# ==========================================
# TAB 2: HISTORY & TABLES
# ==========================================
with tab2:
    st.markdown('<div class="hdr-eyebrow">EEC · HISTORICAL DATA</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title">📈 ประวัติข้อมูลคุณภาพน้ำย้อนหลัง</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-sub">บันทึกข้อมูลย้อนหลังทั้งหมดที่จัดเก็บบน Firebase Realtime Database</div>', unsafe_allow_html=True)
    
    st.write("")
    
    if not df_history.empty:
        st.markdown("#### 📋 ตารางประวัติข้อมูล Sensor")
        display_df = df_history.copy()
        display_df['time'] = display_df['time'].dt.strftime('%d/%m/%Y %H:%M:%S')
        display_df.columns = ['เวลา', 'TDS (ppm)', 'Turbidity (NTU)', 'DO (mg/L)']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ ยังไม่มีข้อมูลประวัติจาก Sensor บน Firebase (/devices/uno-r4/history)")

# ==========================================
# TAB 3: SENSOR LOCATION INFORMATION
# ==========================================
with tab3:
    st.markdown('<div class="hdr-eyebrow">EEC · STATION INFORMATION</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title">📍 ข้อมูลจุดติดตั้งสถานีตรวจวัด</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-sub">รายละเอียดและพิกัดทางภูมิศาสตร์ของสถานีตรวจวัดคุณภาพน้ำอัจฉริยะ</div>', unsafe_allow_html=True)
    
    st.write("")

    col_a, col_b = st.columns([1, 1], gap="medium")
    with col_a:
        st.markdown("""
        <div class="panel">
            <div class="panel-title">📍 จุดติดตั้ง Sensor 01 <span class="tag">STATION INFO</span></div>
            <p><b>ประเภทสถานี:</b> Water Quality Monitoring Station</p>
            <p><b>เซนเซอร์ที่ติดตั้ง:</b></p>
            <ul>
                <li>🧂 TDS Sensor (ตรวจวัดปริมาณของแข็งละลายน้ำ)</li>
                <li>🌫️ Turbidity Sensor (ตรวจวัดความขุ่นของน้ำ)</li>
                <li>🫧 DO / ORP Sensor (ตรวจวัดออกซิเจนละลาย / ศักยภาพการรีดเดอกซ์)</li>
            </ul>
            <p><b>สถานะปัจจุบัน:</b> <span style="color:{}">{}</span></p>
            <p><b>พิกัด (Decimal):</b><br>Latitude: <code>{}</code><br>Longitude: <code>{}</code></p>
            <p><b>พิกัด (DMS):</b><br>13°41'20.79"N, 101°04'44.95"E</p>
        </div>
        """.format(
            "#10b981" if is_online else "#ef4444",
            "🟢 Online" if is_online else "🔴 Offline",
            STATION_LAT, STATION_LON
        ), unsafe_allow_html=True)

    with col_b:
        components.html(leaflet_html, height=370)
