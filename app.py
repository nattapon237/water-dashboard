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
    st.markdown('<div class="hdr-title">💧 ระบบตรวจสอบคุณภาพน้ำ</div>', unsafe_allow_html=True)
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
    
    reasons_list_html = ""
    if risk_reasons:
        reasons_list_html = "<div style='margin-top: 8px; font-size: 0.82rem; color: #f87171;'>"
        for rsn in risk_reasons:
            reasons_list_html += f"• {rsn}<br>"
        reasons_list_html += "</div>"
    else:
        reasons_list_html = "<div style='margin-top: 8px; font-size: 0.82rem; color: #34d399;'>• ทุกค่าอยู่ในเกณฑ์มาตรฐานปกติ</div>"

    ring_svg = render_risk_ring(water_score, status_color)
    risk_html = f"""<div class="panel">
<div class="panel-title">🤖 ผลประเมินน้ำเพื่อเกษตรกรรม <span class="tag">EVALUATION</span></div>
<div style="display: flex; align-items: center; gap: 16px; margin-top: 12px;">
{ring_svg}
<div>
<div style="font-size: 1.1rem; font-weight: 700; color: {status_color};">{status_label}</div>
<div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">คะแนนความปลอดภัย: <b>{water_score}/100</b></div>
{reasons_list_html}
</div>
</div>
<div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(148,163,184,0.15); font-size: 0.85rem; color: #cbd5e1;">
{action_advice}
</div>
</div>"""
    st.markdown(risk_html, unsafe_allow_html=True)

with tab2:
    st.markdown("### 💧 คำแนะนำการใช้น้ำตามค่าเซนเซอร์ปัจจุบัน")
    st.info(action_advice)
    if risk_reasons:
        st.warning("⚠️ ข้อควรระวัง:\n" + "\n".join([f"- {r}" for r in risk_reasons]))
    else:
        st.success("✅ น้ำมีคุณภาพดี เหมาะสำหรับการเกษตรและการประมงเบื้องต้น")

with tab3:
    st.markdown("### 📍 แจ้งเบาะแส / ปัญหาคุณภาพน้ำ")
    with st.form("report_form"):
        reporter_name = st.text_input("ชื่อ-นามสกุลผู้แจ้ง")
        issue_desc = st.text_area("รายละเอียดปัญหาที่พบ")
        uploaded_file = st.file_uploader("แนบรูปภาพประกอบ", type=["jpg", "jpeg", "png"])
        submit_btn = st.form_submit_button("📤 ส่งรายงานปัญหา")
        
        if submit_btn:
            if reporter_name and issue_desc:
                img_url = upload_image_to_drive(uploaded_file) if uploaded_file else "ไม่มีรูปภาพ"
                line_msg = f"🚨 แจ้งเบาะแสปัญหาคุณภาพน้ำ\nผู้แจ้ง: {reporter_name}\nรายละเอียด: {issue_desc}\nรูปภาพ: {img_url}"
                send_line_notification(line_msg)
                st.success("✅ ส่งรายงานและแจ้งเตือนผ่าน LINE สำเร็จเรียบร้อยแล้ว!")
            else:
                st.error("❌ กรุณากรอกชื่อและรายละเอียดปัญหาให้ครบถ้วน")
