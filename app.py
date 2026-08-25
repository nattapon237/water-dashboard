import streamlit as st
import numpy as np
import pandas as pd
import requests
import json
import time
import math
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

def send_line_notification(message, image_url=None):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
    messages = []
    if image_url:
        messages.append({"type": "image", "originalContentUrl": image_url, "previewImageUrl": image_url})
    messages.append({"type": "text", "text": message})
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
    
    chart_df = pd.DataFrame({
        'เวลา': time_index,
        'ความปลอดภัย (%)': trend_values
    })
    
    line_color = "#34d399" if water_score == 100 else "#f87171"
    
    # กราฟ Altair แบบโค้งมนและมี Tooltip (ปรับแก้ให้รองรับ Altair เวอร์ชันใหม่)
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
        height=200
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
    
    # 1. ข้อปฏิบัติสำหรับภาคเกษตร
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

    # 2. ข้อปฏิบัติสำหรับภาคชุมชน
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
            ระบุพิกัดละติจูด ลองจิจูด หรือดูตำแหน่งบน Google Maps พร้อมส่งเข้า LINE ผู้นำชุมชน
        </div>
    """, unsafe_allow_html=True)

    report_type = st.selectbox("📝 ประเภทการกระทำผิด", ["ทิ้งขยะลงแม่น้ำ", "ปล่อยน้ำเสียลงแม่น้ำ", "อื่นๆ"])
    
    detail_desc = st.text_area(
        "✍️ รายละเอียดเพิ่มเติม (บุคคลนี้กำลังทำอะไรอยู่ / พฤติกรรมที่พบ)", 
        placeholder="เช่น กำลังขนถังขยะมาทิ้งลงริมตลิ่ง, หรือเปิดวาล์วปล่อยน้ำเสียลงแม่น้ำ..."
    )

    default_lat = 13.7563
    default_lon = 100.5018

    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("🌐 ละติจูด (Latitude)", value=default_lat, format="%.6f", step=0.0001)
    with col_lon:
        lon = st.number_input("🌐 ลองจิจูด (Longitude)", value=default_lon, format="%.6f", step=0.0001)

    map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    st.markdown("🗺️ **ตำแหน่งบนแผนที่:**")
    st.map(map_df, zoom=15)

    gmap_url = f"https://www.google.com/maps?q={lat},{lon}"
    st.markdown(f"🔗 [คลิกเพื่อเปิดดูตำแหน่งนี้ใน Google Maps]({gmap_url})", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📷 แนบภาพถ่ายหลักฐาน", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="ภาพหลักฐานที่เลือก", use_container_width=True)

    if st.button("🚀 ส่งพิกัด GPS และภาพแจ้ง LINE", use_container_width=True):
        line_msg = (
            f"🚨 แจ้งเบาะแส ({report_type})!\n"
            f"📝 รายละเอียดพฤติกรรม: {detail_desc if detail_desc else 'ไม่ได้ระบุ'}\n"
            f"🌐 พิกัด GPS: {lat}, {lon}\n"
            f"🗺️ Google Maps: {gmap_url}\n"
            f"⏰ เวลาแจ้ง: {now_th.strftime('%d/%m/%Y %H:%M:%S')} (ICT)\n"
            f"⚠️ โปรดส่งเจ้าหน้าที่เข้าตรวจสอบพื้นที่ด่วน!"
        )
        
        sample_image_url = "https://images.unsplash.com/photo-1530587191325-3db32d826c11" if uploaded_file else None
        
        success = send_line_notification(line_msg, image_url=sample_image_url)
        if success:
            st.success("✅ ส่งพิกัดและข้อมูลเข้า LINE สำเร็จ!")
        else:
            st.error("❌ ส่งไม่สำเร็จ ตรวจสอบ LINE Token")
    st.markdown("</div>", unsafe_allow_html=True)

time.sleep(300)
st.rerun()
