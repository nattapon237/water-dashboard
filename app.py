import streamlit as st
import numpy as np
import pandas as pd
import requests
import json
import time
from datetime import datetime

st.set_page_config(page_title="EEC Community Water Intelligence System", page_icon="💧", layout="wide")

# --- Firebase Configuration (cwis-c2ea8) ---
FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"

# LINE API Configuration
LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"

# --- High-Tech Bento Grid Dark Theme CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #070f1e;
        color: #f8fafc;
        font-family: 'Segoe UI', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0b192c;
        color: #ffffff;
        border-right: 1px solid #1e3e62;
    }
    
    /* ดีไซน์การ์ดแบบ Bento Grid ทรงมน สวยงามไฮเทค */
    .bento-card {
        background: linear-gradient(135deg, #0f1c3f 0%, #0b1329 100%);
        border: 1px solid #1d3557;
        padding: 22px;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 20px;
        height: 100%;
    }
    
    h1, h2, h3 {
        color: #38bdf8 !important;
        font-weight: 700;
    }
    
    p, span, label, .stMarkdown, li {
        color: #cbd5e1 !important;
    }

    .status-normal { color: #34d399 !important; font-weight: bold; }
    .status-warning { color: #fbbf24 !important; font-weight: bold; }
    .status-danger { color: #f87171 !important; font-weight: bold; }

    .stButton>button {
        background: linear-gradient(135deg, #0284c7, #0ea5e9);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0ea5e9, #38bdf8);
        color: #070f1e;
    }
    </style>
""", unsafe_allow_html=True)

# ฟังก์ชันส่งข้อความ LINE
def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"to": TARGET_USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# 1. ฟังก์ชันรับ Auth Token จาก Firebase
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

# 2. ฟังก์ชันอ่านข้อมูลจาก Realtime Database
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

# 3. ฟังก์ชันจำลองส่งข้อมูลขึ้น Firebase
def write_mock_sensor_data(id_token, ph_val, tds_val, temp_val, do_val, turb_val):
    if not id_token:
        return False
    url = f"{FIREBASE_DB_URL}/devices/uno-r4/status.json?auth={id_token}"
    payload = {
        "ph": ph_val,
        "tds": tds_val,
        "temp": temp_val,
        "do": do_val,
        "turbidity": turb_val,
        "updatedAt": int(time.time())
    }
    try:
        res = requests.put(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ตรวจสอบการเชื่อมต่อ Auth
id_token = get_firebase_token()

st.sidebar.title("🔥 สถานะ Firebase")
if id_token:
    st.sidebar.success("🟢 เชื่อมต่อ RTDB สำเร็จ")
else:
    st.sidebar.error("🔴 ขาดการเชื่อมต่อ Firebase")

st.sidebar.markdown("---")
st.sidebar.title("🎛️ เซนเซอร์ / Input Control")
sim_ph = st.sidebar.slider("pH Level (ความเป็นกรด-ด่าง)", 0.0, 14.0, 6.4, 0.1)
sim_tds = st.sidebar.slider("EC / TDS (ppm) (สารละลาย)", 0.0, 2000.0, 156.7, 0.1)
sim_temp = st.sidebar.slider("Temperature (°C) (อุณหภูมิ)", 10.0, 50.0, 24.5, 0.5)
sim_do = st.sidebar.slider("DO (mg/L) (ออกซิเจนละลายน้ำ)", 0.0, 20.0, 4.9, 0.1)
sim_turb = st.sidebar.slider("Turbidity (NTU) (ความขุ่น)", 0.0, 1000.0, 67.0, 0.1)

if st.sidebar.button("📤 ส่งค่าจำลองขึ้น Firebase", use_container_width=True):
    if write_mock_sensor_data(id_token, sim_ph, sim_tds, sim_temp, sim_do, sim_turb):
        st.sidebar.success("✅ บันทึกค่าขึ้น Firebase เรียบร้อย!")
        st.rerun()
    else:
        st.sidebar.error("❌ บันทึกไม่สำเร็จ")

# ดึงค่าล่าสุดจาก Firebase RTDB
live_data = read_sensor_data(id_token)
if live_data and isinstance(live_data, dict) and "ph" in live_data:
    ph = float(live_data.get("ph", sim_ph))
    tds = float(live_data.get("tds", sim_tds))
    temp = float(live_data.get("temp", sim_temp))
    do_val = float(live_data.get("do", sim_do))
    turbidity = float(live_data.get("turbidity", sim_turb))
    data_source_badge = "📡 ข้อมูลสดจาก Firebase Realtime Database (`/devices/uno-r4/status`)"
else:
    ph, tds, temp, do_val, turbidity = sim_ph, sim_tds, sim_temp, sim_do, sim_turb
    data_source_badge = "⚠️ ยังไม่มีข้อมูลสดใน Firebase (กำลังใช้ค่าจำลองจากแถบด้านข้าง)"

# ฟังก์ชันคำนวณความเสี่ยง
def calculate_risk(ph, tds, temp, do_val, turbidity):
    risk_score = 0
    reasons = []
    if ph < 5.5 or ph > 9.0:
        risk_score += 35
        reasons.append(f"pH ({ph}) อยู่นอกเกณฑ์มาตรฐานน้ำใช้อุปโภค-บริโภค")
    elif ph < 6.5 or ph > 8.5:
        risk_score += 15
        reasons.append(f"pH ({ph}) เริ่มมีความเป็นกรด/ด่าง เบี่ยงเบนจากเกณฑ์ปกติ")

    if tds > 1000:
        risk_score += 30
        reasons.append(f"EC/TDS ({tds:.1f} ppm) มีค่าความเค็ม/สารละลายสูงเกินเกณฑ์ประปาชุมชน")
    elif tds > 600:
        risk_score += 15
        reasons.append(f"EC/TDS ({tds:.1f} ppm) มีแนวโน้มเพิ่มขึ้น เสี่ยงกระทบพืชสวนและการประปา")

    if do_val < 3.0:
        risk_score += 25
        reasons.append(f"DO ({do_val:.1f} mg/L) อยู่ในเกณฑ์ต่ำ ออกซิเจนในน้ำไม่เพียงพอ")

    if temp > 35.0:
        risk_score += 10
        reasons.append(f"อุณหภูมิ ({temp:.1f} °C) สูงเกินไป กระทบต่อระบบนิเวศแหล่งน้ำ")
    if turbidity > 100:
        risk_score += 15
        reasons.append(f"ความขุ่น ({turbidity:.1f} NTU) สูงกว่าเกณฑ์ ต้องเพิ่มกระบวนการตกตะกอน")

    return min(risk_score, 99), reasons

risk_score, risk_reasons = calculate_risk(ph, tds, temp, do_val, turbidity)

if risk_score >= 60:
    status_label = "🔴 เสี่ยงอันตราย (Danger)"
    status_color = "status-danger"
elif risk_score >= 30:
    status_label = "🟠 เฝ้าระวัง (Warning)"
    status_color = "status-warning"
else:
    status_label = "🟢 ปกติ (Normal)"
    status_color = "status-normal"

# --- ระบบแจ้งเตือนอัตโนมัติ ---
now = datetime.now()
current_time_str = now.strftime("%H:%M")
current_date_str = now.strftime("%Y-%m-%d")

thai_months = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
thai_year = now.year + 543
formatted_thai_date = f"{now.day} {thai_months[now.month]} พ.ศ. {thai_year} (เวลา {current_time_str} น.)"

if "last_danger_alert_date" not in st.session_state:
    st.session_state.last_danger_alert_date = ""
if "last_scheduled_alert" not in st.session_state:
    st.session_state.last_scheduled_alert = ""

if risk_score >= 60 and st.session_state.last_danger_alert_date != current_date_str:
    danger_msg = (
        f"🚨 [แจ้งเตือนวิกฤติด่วน!]\n"
        f"📅 ประจำวันที่: {formatted_thai_date}\n"
        f"------------------------------\n"
        f"📊 ตรวจพบสถานะน้ำระดับอันตราย (Risk Score: {risk_score}%)\n"
        f"• pH: {ph:.1f} | TDS: {tds:.1f} ppm\n"
        f"• DO: {do_val:.1f} mg/L | Temp: {temp:.1f} °C\n"
        f"⚠️ สาเหตุหลัก:\n- " + "\n- ".join(risk_reasons) + "\n"
        f"------------------------------\n"
        f"กรุณาตรวจสอบระบบประปาหมู่บ้านและประกาศงดใช้น้ำด่วน!"
    )
    if send_line_notification(danger_msg):
        st.session_state.last_danger_alert_date = current_date_str

scheduled_slot = None
if "05:00" <= current_time_str <= "05:05":
    scheduled_slot = "05:00 รอบเช้า"
elif "18:00" <= current_time_str <= "18:05":
    scheduled_slot = "18:00 รอบเย็น"

alert_key_name = f"{current_date_str}_{scheduled_slot}"
if scheduled_slot and st.session_state.last_scheduled_alert != alert_key_name:
    sched_msg = (
        f"⏰ [รายงานประจำวัน - {scheduled_slot}]\n"
        f"📅 วันที่: {formatted_thai_date}\n"
        f"------------------------------\n"
        f"สถานะน้ำชุมชน EEC ล่าสุด:\n"
        f"• ดัชนีความเสี่ยง: {risk_score}% ({status_label})\n"
        f"• pH: {ph:.1f} | TDS: {tds:.1f} ppm | DO: {do_val:.1f} mg/L\n"
        f"------------------------------\n"
        f"💡 สรุปภาพรวม: {'ระบบปกติพร้อมใช้งาน' if risk_score < 30 else 'พบความผิดปกติ ควรตรวจสอบระบบกรองน้ำ'}"
    )
    if send_line_notification(sched_msg):
        st.session_state.last_scheduled_alert = alert_key_name

# --- จัดการแท็บหน้าเว็บ ---
tab1, tab2 = st.tabs(["📊 EEC Water Overview (หน้าแรก)", "🏡 ระบบสนับสนุนการตัดสินใจสำหรับชุมชน"])

with tab1:
    st.title("💧 EEC Community Water Intelligence System")
    st.caption("ระบบเฝ้าระวังและประเมินความเสี่ยงคุณภาพน้ำอัจฉริยะเพื่อการอุปโภค บริโภค และการเกษตรของชุมชน")
    st.info(data_source_badge)
    st.markdown("---")

    # --- แถวที่ 1 ของ Bento Grid (3 การ์ดย่อยสไตล์แดชบอร์ด) ---
    col1, col2, col3 = st.columns([1, 1.5, 1], gap="medium")
    
    with col1:
        st.markdown(f"""
            <div class="bento-card">
                <h4 style="color: #38bdf8; margin-top:0;">🔬 ภาพรวมค่าเซนเซอร์</h4>
                <p style="margin: 5px 0;"><b>pH Level:</b> {ph:.1f}</p>
                <p style="margin: 5px 0;"><b>TDS:</b> {tds:.1f} ppm</p>
                <p style="margin: 5px 0;"><b>Temp:</b> {temp:.1f} °C</p>
                <p style="margin: 5px 0;"><b>DO:</b> {do_val:.1f} mg/L</p>
                <p style="margin: 5px 0;"><b>Turbidity:</b> {turbidity:.1f} NTU</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="bento-card">
                <h4 style="color: #38bdf8; margin-top:0;">📈 แนวโน้มคุณภาพน้ำ (Area Trend)</h4>
            </div>
        """, unsafe_allow_html=True)
        chart_data_1 = pd.DataFrame(np.random.randn(10, 3) + [tds/100, do_val, turbidity/50], columns=['TDS', 'DO', 'Turbidity'])
        st.area_chart(chart_data_1, color=["#0ea5e9", "#34d399", "#38bdf8"], height=180)

    with col3:
        st.markdown(f"""
            <div class="bento-card">
                <h4 style="color: #38bdf8; margin-top:0;">🤖 AI Risk Assessment</h4>
                <h2 style="color: {'#34d399' if risk_score<30 else ('#fbbf24' if risk_score<60 else '#f87171')};">{risk_score}%</h2>
                <p>สถานะ: <span class='{status_color}'>{status_label}</span></p>
            </div>
        """, unsafe_allow_html=True)

    # --- แถวที่ 2 ของ Bento Grid (กราฟเส้นเปรียบเทียบ และ บาร์ชาร์ตสถิติ) ---
    col4, col5 = st.columns([1.2, 1], gap="medium")
    
    with col4:
        st.markdown("""
            <div class="bento-card">
                <h4 style="color: #38bdf8; margin-top:0;">📊 การเปรียบเทียบพารามิเตอร์เชิงลึก</h4>
            </div>
        """, unsafe_allow_html=True)
        chart_data_2 = pd.DataFrame(np.random.randn(12, 2) * 5 + 50, columns=['Value A', 'Value B'])
        st.line_chart(chart_data_2, color=["#0ea5e9", "#34d399"], height=200)

    with col5:
        st.markdown("""
            <div class="bento-card">
                <h4 style="color: #38bdf8; margin-top:0;">📊 สถิติความแปรปรวนย้อนหลัง</h4>
            </div>
        """, unsafe_allow_html=True)
        bar_data = pd.DataFrame(np.random.rand(8, 2) * 100, columns=['Series 1', 'Series 2'])
        st.bar_chart(bar_data, color=["#0ea5e9", "#38bdf8"], height=200)

with tab2:
    st.markdown("## 🏡 ระบบสนับสนุนการตัดสินใจสำหรับชุมชน")
    st.markdown("แนวทางปฏิบัติเชิงรุกสำหรับผู้นำชุมชน คณะกรรมการประปาหมู่บ้าน และกลุ่มเกษตรกร")
    st.markdown("---")
    
    col_action1, col_action2 = st.columns(2, gap="large")
    
    with col_action1:
        if risk_score < 30:
            action_content = """
                <ol style="color: #cbd5e1; padding-left: 20px; line-height: 1.8;">
                    <li><b>แจกจ่ายน้ำปกติ:</b> ระบบประปาหมู่บ้านใช้งานได้ตามปกติ</li>
                    <li><b>จัดเก็บข้อมูล:</b> บันทึกค่าน้ำเข้าฐานข้อมูลชุมชนต่อเนื่อง</li>
                </ol>
            """
        elif risk_score < 60:
            action_content = """
                <ul style="color: #cbd5e1; padding-left: 20px; line-height: 1.8; list-style-type: none;">
                    <li>1. 📢 <b>แจ้งเตือนเกษตรกร:</b> สารละลาย/ความเค็มสูง ระวังการสูบน้ำเข้าแปลง</li>
                    <li>2. ⚙️ <b>ปรับระบบกรอง:</b> เพิ่มระยะเวลาการตกตะกอนในระบบประปา</li>
                    <li>3. 🌊 <b>เติมออกซิเจน:</b> ค่า DO ลดลง ตรวจสอบระบบบำบัดน้ำ</li>
                </ul>
            """
        else:
            action_content = """
                <ul style="color: #cbd5e1; padding-left: 20px; line-height: 1.8; list-style-type: none;">
                    <li>1. 🚫 <b>งดใช้น้ำชั่วคราว:</b> ห้ามใช้น้ำเพื่อบริโภคและทำการเกษตรด่วน</li>
                    <li>2. 🚰 <b>ใช้แหล่งน้ำสำรอง:</b> เปิดใช้งานน้ำบาดาลหรือแหล่งสำรองแทน</li>
                </ul>
            """

        st.markdown(f"""
            <div class="bento-card">
                <h3 style="color: #38bdf8; margin-top: 0;">🛠️ ข้อแนะนำการปฏิบัติงานสำหรับชุมชน</h3>
                <br>
                {action_content}
            </div>
        """, unsafe_allow_html=True)

    with col_action2:
        st.markdown("""
            <div class="bento-card">
                <h3 style="color: #38bdf8; margin-top: 0;">📲 ระบบส่งแจ้งเตือนฉุกเฉินถึงผู้นำชุมชน (LINE)</h3>
                <p style="color: #94a3b8; font-size: 0.9rem;">ตั้งค่าแจ้งเตือนอัตโนมัติ: แจ้งทันทีเมื่อสถานะเป็นวิกฤต และสรุปผลทุก 05:00 น. / 18:00 น.</p>
                <br>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 ทดสอบส่งรายงานเข้า LINE ทันที", use_container_width=True):
            test_msg = (
                f"📢 [ทดสอบระบบ LINE น้ำชุมชน EEC]\n"
                f"📅 วันที่: {formatted_thai_date}\n"
                f"------------------------------\n"
                f"📊 Risk Score: {risk_score}% ({status_label})\n"
                f"• pH: {ph:.1f} | TDS: {tds:.1f} ppm\n"
                f"• DO: {do_val:.1f} mg/L | Temp: {temp:.1f} °C\n"
                f"------------------------------\n"
                f"💡 ระบบทำงานอัตโนมัติสมบูรณ์!"
            )
            if send_line_notification(test_msg):
                st.success("✅ ส่งข้อความทดสอบเข้า LINE สำเร็จ!")
            else:
                st.error("❌ ส่งไม่สำเร็จ")
        st.markdown('</div>', unsafe_allow_html=True)

# หน่วงเวลาและรีเฟรชหน้าเว็บทุกๆ 60 วินาที
time.sleep(60)
st.rerun()
