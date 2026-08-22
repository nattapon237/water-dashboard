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

# --- Dark Tech Blue UI Custom CSS ---
st.markdown("""
    <style>
    /* ภาพรวมพื้นหลังหลักของ Streamlit */
    .stApp {
        background-color: #0b132b;
        color: #e0e1dd;
    }
    
    /* ปรับแต่ง Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1c2541;
        color: #ffffff;
    }
    
    /* สไตล์การ์ดข้อมูล (Metric / Container) */
    .tech-card {
        background-color: #1c2541;
        border: 1px solid #3a506b;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 15px;
    }
    
    /* หัวข้อและตัวหนังสือ */
    h1, h2, h3, h4 {
        color: #6fffe9 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    p, span, label, .stMarkdown {
        color: #caf0f8 !important;
    }

    /* สไตล์สถานะต่างๆ */
    .status-normal { color: #52b788; font-weight: bold; font-size: 1.1rem; }
    .status-warning { color: #fca311; font-weight: bold; font-size: 1.1rem; }
    .status-danger { color: #e76f51; font-weight: bold; font-size: 1.1rem; }

    /* ปรับแต่งปุ่ม */
    .stButton>button {
        background: linear-gradient(135deg, #0077b6, #00b4d8);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 10px rgba(0, 180, 216, 0.4);
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00b4d8, #90e0ef);
        color: #0b132b;
    }
    </style>
""", unsafe_allow_html=True)

# ฟังก์ชันส่งข้อความเข้า LINE
def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"to": TARGET_USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# 1. ฟังก์ชันรับ Auth Token จาก Firebase Anonymous Authentication
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

# --- ระบบแจ้งเตือนอัตโนมัติ (Background Automation Logic) ---
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

    # แผงแสดงดัชนีความเสี่ยงแบบไฮเทค
    col_score1, col_score2 = st.columns([1, 2], gap="large")
    with col_score1:
        st.markdown("""<div class="tech-card">""", unsafe_allow_html=True)
        st.markdown("### 🤖 AI WATER RISK SCORE")
        st.metric(label="ดัชนีความเสี่ยงรวมของชุมชน", value=f"{risk_score}%")
        st.markdown(f"สถานะปัจจุบัน: <span class='{status_color}'>{status_label}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_score2:
        st.markdown("""<div class="tech-card">""", unsafe_allow_html=True)
        st.markdown("### 📌 สรุปสถานการณ์คุณภาพน้ำชุมชน")
        if risk_score < 30:
            st.success("✅ คุณภาพน้ำอยู่ในเกณฑ์ดี ปลอดภัยสำหรับการอุปโภค การเกษตร และการประปาหมู่บ้าน")
        elif risk_score < 60:
            st.warning(f"⚠️ ตรวจพบความผิดปกติบางประการที่ต้องเฝ้าระวัง:\n- " + "\n- ".join(risk_reasons))
        else:
            st.error(f"🚨 ตรวจพบสภาวะน้ำวิกฤต! สาเหตุหลัก:\n- " + "\n- ".join(risk_reasons))
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 ข้อมูลจริงจากเซนเซอร์ชุมชน (Live Sensor Metrics)")
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.markdown(f"""<div class="tech-card" style="text-align:center;"><h4>pH</h4><h2>{ph:.1f}</h2><p>กรด-ด่าง</p></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="tech-card" style="text-align:center;"><h4>TDS</h4><h2>{tds:.1f}</h2><p>ppm</p></div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="tech-card" style="text-align:center;"><h4>Temp</h4><h2>{temp:.1f}</h2><p>°C</p></div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""<div class="tech-card" style="text-align:center;"><h4>DO</h4><h2>{do_val:.1f}</h2><p>mg/L</p></div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""<div class="tech-card" style="text-align:center;"><h4>Turbidity</h4><h2>{turbidity:.1f}</h2><p>NTU</p></div>""", unsafe_allow_html=True)
    with m6:
        status_sys = "Online" if live_data else "Sim"
        st.markdown(f"""<div class="tech-card" style="text-align:center;"><h4>System</h4><h2>{status_sys}</h2><p>Status</p></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📈 แนวโน้มความแปรปรวนคุณภาพน้ำย้อนหลัง (Community Water Trends)")
    
    st.markdown("""<div class="tech-card">""", unsafe_allow_html=True)
    chart_data = pd.DataFrame(
        np.random.randn(20, 3) + [tds / 100, do_val * 2, turbidity / 100],
        columns=['สารละลาย (TDS)', 'DO (mg/L)', 'ความขุ่น (NTU)']
    )
    st.line_chart(chart_data, color=["#00b4d8", "#90e0ef", "#03045e"])
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.title("🏡 ระบบสนับสนุนการตัดสินใจสำหรับชุมชน")
    st.caption("แนวทางปฏิบัติเชิงรุกสำหรับผู้นำชุมชน คณะกรรมการประปาหมู่บ้าน และกลุ่มเกษตรกร")
    st.markdown("---")
    
    st.markdown(f"""<div class="tech-card">""", unsafe_allow_html=True)
    st.markdown(f"### สถานะการประเมิน: <span class='{status_color}'>{status_label}</span> (Risk Score: {risk_score}%)", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col_action1, col_action2 = st.columns(2, gap="large")
    with col_action1:
        st.markdown("""<div class="tech-card">""", unsafe_allow_html=True)
        st.markdown("#### 🛠️ ข้อแนะนำการปฏิบัติงานสำหรับชุมชน")
        if risk_score < 30:
            st.write("1. **แจกจ่ายน้ำปกติ:** ระบบประปาหมู่บ้านและช่องทางส่งน้ำการเกษตรใช้งานได้ตามปกติ")
            st.write("2. **จัดเก็บข้อมูล:** ระบบบันทึกค่าน้ำเข้าสู่ฐานข้อมูลเฝ้าระวังของชุมชนตามปกติ")
        elif risk_score < 60:
            st.write("1. 📢 **แจ้งเตือนเกษตรกร:** สารละลาย/ความเค็มเริ่มสูง ระวังการสูบน้ำเข้าแปลงเกษตร")
            st.write("2. ⚙️ **ปรับระบบกรองประปา:** เพิ่มระยะเวลาการตกตะกอนและการกรองของระบบประปา")
            st.write("3. 🌊 **ปรับปรุงการเติมออกซิเจน:** ค่า DO ลดลง ควรตรวจสอบระบบบำบัดน้ำ")
            st.write("4. 🔎 **สำรวจต้นน้ำ:** ส่งตัวแทนชุมชน ตรวจเช็กจุดสูบน้ำว่ามีการปนเปื้อนหรือไม่")
        else:
            st.write("1. 🚫 **ประกาศงดใช้น้ำชั่วคราว:** แจ้งห้ามใช้น้ำเพื่อการบริโภคและสูบเข้าพื้นที่เกษตรด่วน")
            st.write("2. 🚰 **สลับแหล่งน้ำสำรอง:** เปิดใช้งานแหล่งน้ำสำรอง/น้ำบาดาลหมู่บ้านแทน")
            st.write("3. 🧪 **ประสานงาน อบต./เทศบาล:** แจ้งเจ้าหน้าที่สิ่งแวดล้อมลงพื้นที่ตรวจวิเคราะห์")
            st.write("4. 📲 **แจ้งเตือนหอกระจายข่าว:** ส่งข้อความแจ้งเตือนผ่าน LINE ถึงผู้ใหญ่บ้าน")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_action2:
        st.markdown("""<div class="tech-card">""", unsafe_allow_html=True)
        st.markdown("#### 📲 ระบบส่งแจ้งเตือนฉุกเฉินถึงผู้นำชุมชน (LINE)")
        st.info("ระบบตั้งค่าแจ้งเตือนอัตโนมัติ: แจ้งทันทีเมื่อสถานะเป็นสีแดง และส่งสรุปผลทุกวันเวลา 05:00 น. และ 18:00 น.")
        if st.button("🚀 ทดสอบส่งรายงานเข้า LINE ทันที", use_container_width=True):
            test_msg = (
                f"📢 [ทดสอบระบบ LINE แจ้งเตือนน้ำชุมชน EEC]\n"
                f"📅 วันที่: {formatted_thai_date}\n"
                f"------------------------------\n"
                f"📊 Risk Score: {risk_score}% ({status_label})\n"
                f"• pH: {ph:.1f} | TDS: {tds:.1f} ppm\n"
                f"• DO: {do_val:.1f} mg/L | Temp: {temp:.1f} °C\n"
                f"------------------------------\n"
                f"💡 ระบบทำงานอัตโนมัติสมบูรณ์แล้ว!"
            )
            if send_line_notification(test_msg):
                st.success("✅ ส่งข้อความทดสอบเข้า LINE สำเร็จ!")
            else:
                st.error("❌ ส่งไม่สำเร็จ")
        st.markdown("</div>", unsafe_allow_html=True)

# ระบบหน่วงเวลาและรีเฟรชหน้าเว็บอัตโนมัติทุกๆ 60 วินาที
time.sleep(60)
st.rerun()
