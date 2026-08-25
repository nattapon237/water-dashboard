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

TH_TZ = pytz.timezone('Asia/Bangkok')

st.set_page_config(page_title="EEC Community Water Intelligence System - Agriculture", page_icon="🌾", layout="wide")

# โหลด CSS จากไฟล์ style.css ภายนอก
try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"

LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"

# Google Apps Script Web App URL สำหรับอัปโหลดรูปภาพเข้า Google Drive อัตโนมัติ
GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyn2ty8P73SvsRu-YQJSwIKFUpN3TDGpkRqHJt3y9VqroBSGjz6rGte4lHdjQAP-WQheg/exec"

def upload_image_to_drive(uploaded_file):
    if not uploaded_file:
        return None
    try:
        bytes_data = uploaded_file.getvalue()
        base64_data = base64.b64encode(bytes_data).decode('utf-8')
        payload = {
            "filename": uploaded_file.name,
            "mimeType": uploaded_file.type,
            "base64Data": base64_data
        }
        res = requests.post(GOOGLE_APPS_SCRIPT_URL, json=payload, timeout=30)
        if res.status_code == 200:
            res_json = res.json()
            if res_json.get("status") == "success":
                return res_json.get("url")
    except Exception as e:
        print(f"Error uploading to Drive: {e}")
    return None

# ฟังก์ชันส่งข้อความแจ้งเตือนผ่าน LINE
def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
    messages = [
        {"type": "text", "text": message}
    ]
    payload = {"to": TARGET_USER_ID, "messages": messages}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
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
        return 0, "น้ำไม่ปลอดภัย", "var(--danger)", reasons, "❌ ห้ามนำไปรดพืชผลหรือเติมลงบ่อปลาเด็ดขาด"
    else:
        return 100, "ปกติ (ปลอดภัย)", "var(--safe)", [], "✅ น้ำปลอดภัย สามารถใช้รดน้ำพืชผลและให้สัตว์น้ำได้"

water_score, status_label, status_color, risk_reasons, action_advice = calculate_water_quality(ph, tds, temp, do_val, turbidity)

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

# 3 แท็บหลัก
tab1, tab2, tab3 = st.tabs(["📊 ภาพรวมน้ำ (Dashboard)", "💧 คำแนะนำการใช้น้ำ", "📍 แจ้งเบาะแส"])

with tab1:
    st.markdown('<div class="hdr-eyebrow">EEC · AGRI-WATER INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title">💧 ระบบตรวจสอบคุณภาพน้ำ (Live Dashboard)</div>', unsafe_allow_html=True)
    
    # แบ่งส่วน Header ออกเป็น 2 ฝั่ง (ซ้าย: เวลา/สถานะ, ขวา: อัพเดต)
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        pill_html = f"""<div style="margin-top: 5px; margin-bottom: 14px;">
<span class="status-pill" style="--pill-color:{status_color}">
<span class="status-dot"></span>{status_label}
</span>
</div>"""
        st.markdown(pill_html, unsafe_allow_html=True)
    with h_col2:
        st.markdown(f'<div class="hdr-sub" style="text-align: right; margin-top: 10px;">อัปเดตล่าสุด: {now_th.strftime("%H:%M:%S")}<br>(Auto-refresh 5 นาที)</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ------------------ ส่วน Gauge Cards (แบ่ง 3 คอลัมน์) ------------------
    g1, g2, g3 = st.columns(3, gap="medium")
    with g1:
        render_gauge_card("⚗️", "PH LEVEL", ph, "", 0, 14,
            [(0, 6.5, "--danger"), (6.5, 8.5, "--safe"), (8.5, 14, "--danger")])
        render_gauge_card("🫧", "DISSOLVED OXYGEN (DO)", do_val, "mg/L", 0, 20,
            [(0, 4.0, "--danger"), (4.0, 20, "--safe")])
    with g2:
        render_gauge_card("🌡️", "TEMPERATURE", temp, "°C", 10, 45,
            [(10, 35, "--safe"), (35, 45, "--danger")])
        render_gauge_card("🌫️", "TURBIDITY", turbidity, "NTU", 0, 300,
            [(0, 100, "--safe"), (100, 300, "--danger")])
    with g3:
        render_gauge_card("🧂", "TDS / EC", tds, "ppm", 0, 1200,
            [(0, 1000, "--safe"), (1000, 1200, "--danger")])
        # กล่องแสดงภาพรวมสั้นๆ แทนที่ว่าง
        st.markdown(f"""
        <div class="panel" style="height: 98px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background: rgba(255,255,255,0.02);">
            <div style="font-size: 0.8rem; color: var(--text-mid);">คุณภาพน้ำโดยรวม</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {status_color};">{status_label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    # ------------------ ส่วน Assessment และ Map (แบ่ง 2 คอลัมน์กว้างๆ) ------------------
    col_assess, col_map = st.columns([1.2, 1], gap="large")
    
    with col_assess:
        reasons_list_html = ""
        if risk_reasons:
            reasons_list_html = "<div style='margin-top: 8px; font-size: 0.85rem; color: #f87171;'>"
            for rsn in risk_reasons:
                reasons_list_html += f"• {rsn}<br>"
            reasons_list_html += "</div>"
        else:
            reasons_list_html = "<div style='margin-top: 8px; font-size: 0.85rem; color: #34d399;'>• ทุกพารามิเตอร์อยู่ในเกณฑ์มาตรฐานปกติ พร้อมใช้งาน</div>"

        ring_svg = render_risk_ring(water_score, status_color)
        risk_html = f"""<div class="panel" style="height: 100%;">
<div class="panel-title">🤖 ผลประเมินน้ำเพื่อเกษตรกรรม <span class="tag">AI EVALUATION</span></div>
<div style="display:flex; align-items:center; gap:20px; margin-top: 15px;">
<div style="position:relative; width:110px; height:110px;">
{ring_svg}
<div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;">
<span style="font-family:'JetBrains Mono',monospace; font-weight:700; font-size:1.5rem; color:{status_color};">{water_score}%</span>
</div>
</div>
<div>
<div style="font-size:1rem; font-weight:700; color:{status_color}">{status_label}</div>
<div style="font-size:0.75rem; color:var(--text-low); font-family:'JetBrains Mono',monospace; margin-top:2px;">AGRI-SAFETY STATUS</div>
</div>
</div>
<div style="margin-top: 15px;">
{reasons_list_html}
</div>
<div class="risk-advice" style="border-left: 4px solid {status_color}; padding-left: 12px; margin-top: 15px; background: rgba(0,0,0,0.1); padding: 10px; border-radius: 0 8px 8px 0;">
<b>💡 คำแนะนำเบื้องต้น:</b><br>{action_advice}
</div>
</div>"""
        st.markdown(risk_html, unsafe_allow_html=True)
        
    with col_map:
        st.markdown("""
        <div class="panel" style="height: 100%; display: flex; flex-direction: column;">
            <div class="panel-title">📍 ตำแหน่งสถานีวัดคุณภาพน้ำ <span class="tag">SENSOR LOCATION</span></div>
            <div style="font-size: 0.8rem; color: var(--text-mid); margin-bottom: 10px;">พิกัด: อ่างเก็บน้ำพื้นที่ระยอง (EEC)</div>
        """, unsafe_allow_html=True)
        
        # ตัวอย่างพิกัดจุดติดตั้งเซนเซอร์ (เช่น พื้นที่ EEC ระยอง)
        sensor_lat, sensor_lon = 12.6814, 101.2816
        sensor_df = pd.DataFrame({'lat': [sensor_lat], 'lon': [sensor_lon]})
        
        # แสดง Map
        st.map(sensor_df, zoom=11, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    
    # ------------------ ส่วนกราฟแนวโน้ม (Trend Chart) ------------------
    st.markdown('<div class="panel"><div class="panel-title">📈 กราฟแนวโน้มย้อนหลัง 1 ชั่วโมง <span class="tag">TREND HISTORY</span></div>', unsafe_allow_html=True)
    
    time_index = [(now_th - timedelta(minutes=i*10)).strftime("%H:%M") for i in range(8)][::-1]
    trend_values = np.random.uniform(95, 100, 8) if water_score == 100 else np.random.uniform(0, 15, 8)
    
    chart_df = pd.DataFrame({
        'เวลา': time_index,
        'ความปลอดภัย (%)': trend_values
    })
    
    line_color = "#34d399" if water_score == 100 else "#f87171"
    
    base_line = alt.Chart(chart_df).mark_line(
        interpolate='monotone',
        strokeWidth=3
    ).encode(
        x=alt.X('เวลา:N', sort=None, axis=alt.Axis(labelAngle=0, title=None, grid=False)),
        y=alt.Y('ความปลอดภัย (%):Q', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(grid=True, gridColor='rgba(148,163,184,0.1)')),
        color=alt.value(line_color)
    )

    points = alt.Chart(chart_df).mark_circle(
        size=60,
        opacity=1
    ).encode(
        x=alt.X('เวลา:N', sort=None),
        y=alt.Y('ความปลอดภัย (%):Q'),
        color=alt.value(line_color),
        tooltip=['เวลา', 'ความปลอดภัย (%)']
    )

    chart = (base_line + points).properties(
        height=250
    ).interactive().configure_view(
        stroke=None
    )
    
    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="hdr-eyebrow">WATER USAGE ADVICE</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title" style="font-size:1.3rem;">💧 คำแนะนำการใช้น้ำ</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    if water_score == 100:
        st.success("✅ น้ำปลอดภัย: เปิดระบบสูบน้ำได้ปกติ")
    else:
        st.error("🚨 น้ำมีปัญหา: ห้ามสูบน้ำเข้าแปลงเด็ดขาด!")

    st.write("")
    
    st.markdown("""
    <div class="panel">
        <div class="panel-title">🛠️ คำแนะนำการใช้น้ำสำหรับภาคเกษตร <span class="tag">AGRICULTURE</span></div>
        <div class="check-row">
            <div class="check-icon">🚫</div>
            <div class="check-text"><b>หยุดสูบน้ำเข้าแปลง:</b> ปิดวาล์วและระบบชลประทานทันทีหากพบสถานะเตือนสีแดง</div>
        </div>
        <div class="check-row">
            <div class="check-icon">⚙️</div>
            <div class="check-text"><b>ตรวจระบบกรอง/บำบัด:</b> ตรวจสอบค่า pH และความขุ่นในถังพักน้ำก่อนนำไปรดพืชผล</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    st.markdown("""
    <div class="panel">
        <div class="panel-title">🏘️ คำแนะนำการใช้น้ำสำหรับภาคชุมชน <span class="tag">COMMUNITY</span></div>
        <div class="check-row">
            <div class="check-icon">⚠️</div>
            <div class="check-text"><b>งดใช้น้ำดิบชั่วคราว:</b> หลีกเลี่ยงการใช้น้ำจากแหล่งน้ำสาธารณะเพื่อการอุปโภคหรือซักล้าง</div>
        </div>
        <div class="check-row">
            <div class="check-icon">📢</div>
            <div class="check-text"><b>ติดตามประกาศผู้นำชุมชน:</b> รอฟังประกาศสถานการณ์น้ำและแจ้งเตือนการแจกจ่ายน้ำสะอาด</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

with tab3:
    st.markdown('<div class="hdr-eyebrow">INCIDENT REPORTING</div>', unsafe_allow_html=True)
    st.markdown('<div class="hdr-title" style="font-size:1.3rem;">📍 แจ้งเบาะแสทิ้งขยะ / ปล่อยน้ำเสีย</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    st.markdown("""
    <div class="panel">
        <div class="panel-title">📍 ฟอร์มแจ้งเบาะแสผ่านพิกัด GPS <span class="tag">GPS REPORT</span></div>
        <div style="font-size:0.84rem; color:var(--text-mid); margin-bottom: 10px;">
            ระบุพิกัดละติจูด ลองจิจูด หรือดูตำแหน่งบน Google Maps พร้อมแนบรูปภาพหลักฐาน ระบบจะอัปเข้า Google Drive และส่ง LINE ให้ทันที
        </div>
    """, unsafe_allow_html=True)

    report_type = st.selectbox("📝 ประเภทการกระทำผิด", ["ทิ้งขยะลงแม่น้ำ", "ปล่อยน้ำเสียลงแม่น้ำ", "อื่นๆ"], key="rep_type")
    
    detail_desc = st.text_area(
        "✍️ รายละเอียดเพิ่มเติม (บุคคลนี้กำลังทำอะไรอยู่ / พฤติกรรมที่พบ)", 
        placeholder="เช่น กำลังขนถังขยะมาทิ้งลงริมตลิ่ง, หรือเปิดวาล์วปล่อยน้ำเสียลงแม่น้ำ...",
        key="rep_desc"
    )

    default_lat = 13.7563
    default_lon = 100.5018

    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("🌐 ละติจูด (Latitude)", value=default_lat, format="%.6f", step=0.0001, key="rep_lat")
    with col_lon:
        lon = st.number_input("🌐 ลองจิจูด (Longitude)", value=default_lon, format="%.6f", step=0.0001, key="rep_lon")

    map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    st.map(map_df, zoom=15)

    gmap_url = f"https://www.google.com/maps?q={lat},{lon}"
    st.markdown(f"🔗 [คลิกเพื่อเปิดดูตำแหน่งนี้ใน Google Maps]({gmap_url})", unsafe_allow_html=True)

    # อัปโหลดรูปภาพหลักฐานจากเครื่อง
    uploaded_file = st.file_uploader("📸 แนบรูปภาพหลักฐาน", type=["jpg", "jpeg", "png"], key="rep_file")

    if st.button("🚀 ส่งพิกัด GPS และแจ้ง LINE", use_container_width=True):
        with st.spinner("กำลังอัปโหลดรูปภาพเข้า Google Drive และส่งเข้า LINE..."):
            
            # อัปโหลดรูปเข้า Google Drive อัตโนมัติ
            drive_image_url = "ไม่ได้แนบรูปภาพ"
            if uploaded_file is not None:
                uploaded_url = upload_image_to_drive(uploaded_file)
                if uploaded_url:
                    drive_image_url = uploaded_url

            line_msg = (
                f"🚨 แจ้งเบาะแส ({report_type})!\n"
                f"📝 รายละเอียดพฤติกรรม: {detail_desc if detail_desc else 'ไม่ได้ระบุ'}\n"
                f"🌐 พิกัด GPS: {lat}, {lon}\n"
                f"🗺️ Google Maps: {gmap_url}\n"
                f"🖼️ ภาพถ่ายหลักฐาน (Google Drive): {drive_image_url}\n"
                f"⏰ เวลาแจ้ง: {now_th.strftime('%d/%m/%Y %H:%M:%S')} (ICT)\n"
                f"⚠️ โปรดส่งเจ้าหน้าที่เข้าตรวจสอบพื้นที่ด่วน!"
            )
            
            success = send_line_notification(line_msg)
            
            if success:
                st.success("✅ อัปโหลดรูปเข้า Google Drive และส่งแจ้งเตือนเข้า LINE สำเร็จ!")
                time.sleep(1.5)
                
                # ล้างค่าใน Session State
                for key in ["rep_desc", "rep_file"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            else:
                st.error("❌ ส่งไม่สำเร็จ กรุณาตรวจสอบ LINE Token หรือการเชื่อมต่อ")
                
    st.markdown("</div>", unsafe_allow_html=True)

time.sleep(300)
st.rerun()
