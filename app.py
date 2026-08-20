import streamlit as st
import numpy as np
import pandas as pd
import requests
import json
import time

st.set_page_config(page_title="EEC Community Water Intelligence System", page_icon="💧", layout="wide")

# --- Firebase Configuration (cwis-c2ea8) ---
FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"

# สไตล์ CSS
st.markdown("""
    <style>
    .status-normal { color: #2e7d32; font-weight: bold; }
    .status-warning { color: #ef6c00; font-weight: bold; }
    .status-danger { color: #c62828; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

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
sim_tds = st.sidebar.slider("EC / TDS (ppm) (ความขุ่น/สารละลาย)", 0, 2000, 850, 10)
sim_temp = st.sidebar.slider("Temperature (°C) (อุณหภูมิ)", 10.0, 50.0, 31.0, 0.5)
sim_do = st.sidebar.slider("DO (mg/L) (ออกซิเจนในน้ำ)", 0.0, 12.0, 4.2, 0.1)
sim_turb = st.sidebar.slider("Turbidity (NTU) (ความขุ่นสะสม)", 0.0, 500.0, 45.0, 1.0)

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
    tds = int(live_data.get("tds", sim_tds))
    temp = float(live_data.get("temp", sim_temp))
    do = float(live_data.get("do", sim_do))
    turbidity = float(live_data.get("turbidity", sim_turb))
    data_source_badge = "📡 ข้อมูลสดจาก Firebase Realtime Database (`/devices/uno-r4/status`)"
else:
    ph, tds, temp, do, turbidity = sim_ph, sim_tds, sim_temp, sim_do, sim_turb
    data_source_badge = "⚠️ ยังไม่มีข้อมูลสดใน Firebase (กำลังใช้ค่าจำลองจากแถบด้านข้าง)"

# ฟังก์ชันคำนวณความเสี่ยง
def calculate_risk(ph, tds, temp, do, turbidity):
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
        reasons.append(f"EC/TDS ({tds} ppm) มีค่าความเค็ม/สารละลายสูงเกินเกณฑ์ประปาชุมชน")
    elif tds > 600:
        risk_score += 15
        reasons.append(f"EC/TDS ({tds} ppm) มีแนวโน้มเพิ่มขึ้น เสี่ยงกระทบพืชสวนและการประปา")

    if do < 3.0:
        risk_score += 30
        reasons.append(f"DO ({do} mg/L) ออกซิเจนต่ำวิกฤต เสี่ยงสัตว์น้ำในแหล่งน้ำชุมชนน็อกน้ำ")
    elif do < 5.0:
        risk_score += 15
        reasons.append(f"DO ({do} mg/L) ออกซิเจนเริ่มลดลง ควรเปิดเครื่องเติมอากาศชุมชน")

    if temp > 35.0:
        risk_score += 10
        reasons.append(f"อุณหภูมิ ({temp} °C) สูงเกินไป กระทบต่อระบบนิเวศแหล่งน้ำ")
    if turbidity > 100:
        risk_score += 15
        reasons.append(f"ความขุ่น ({turbidity} NTU) สูงกว่าเกณฑ์ ต้องเพิ่มกระบวนการตกตะกอน")

    return min(risk_score, 99), reasons

risk_score, risk_reasons = calculate_risk(ph, tds, temp, do, turbidity)

if risk_score >= 60:
    status_label = "🔴 เสี่ยงอันตราย (Danger)"
    status_color = "status-danger"
elif risk_score >= 30:
    status_label = "🟠 เฝ้าระวัง (Warning)"
    status_color = "status-warning"
else:
    status_label = "🟢 ปกติ (Normal)"
    status_color = "status-normal"

# จัดการแท็บหน้าเว็บ
tab1, tab2 = st.tabs(["📊 EEC Water Overview (หน้าแรก)", "🏡 ระบบสนับสนุนการตัดสินใจสำหรับชุมชน"])

with tab1:
    st.title("💧 EEC Community Water Overview")
    st.caption("ระบบเฝ้าระวังและประเมินความเสี่ยงคุณภาพน้ำอัจฉริยะเพื่อการอุปโภค บริโภค และการเกษตรของชุมชน")
    st.info(data_source_badge)
    st.markdown("---")

    col_score1, col_score2 = st.columns([1, 2])
    with col_score1:
        st.markdown("### 🤖 AI WATER RISK SCORE")
        st.metric(label="ดัชนีความเสี่ยงรวมของชุมชน", value=f"{risk_score}%")
        st.markdown(f"สถานะปัจจุบัน: <span class='{status_color}'>{status_label}</span>", unsafe_allow_html=True)

    with col_score2:
        st.markdown("### 📌 สรุปสถานการณ์คุณภาพน้ำชุมชน")
        if risk_score < 30:
            st.success("✅ คุณภาพน้ำอยู่ในเกณฑ์ดี ปลอดภัยสำหรับการอุปโภค การเกษตร และการประปาหมู่บ้าน")
        elif risk_score < 60:
            st.warning(f"⚠️ ตรวจพบความผิดปกติบางประการที่ต้องเฝ้าระวัง:\n- " + "\n- ".join(risk_reasons))
        else:
            st.error(f"🚨 ตรวจพบสภาวะน้ำวิกฤต! สาเหตุหลัก:\n- " + "\n- ".join(risk_reasons))

    st.markdown("---")
    st.subheader("📊 ข้อมูลจริงจากเซนเซอร์ชุมชน (Live Sensor Metrics)")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("pH (กรด-ด่าง)", f"{ph:.1f}")
    m2.metric("EC / TDS", f"{tds} ppm")
    m3.metric("อุณหภูมิ", f"{temp:.1f} °C")
    m4.metric("DO (ออกซิเจน)", f"{do:.1f} mg/L")
    m5.metric("ความขุ่น", f"{turbidity:.0f} NTU")

    st.markdown("---")
    st.subheader("📈 แนวโน้มความแปรปรวนคุณภาพน้ำย้อนหลัง (Community Water Trends)")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3) + [tds / 100, ph * 10, do * 10],
        columns=['ความขุ่น/สารละลาย (TDS)', 'ค่าความเป็นกรด-ด่าง (pH)', 'ออกซิเจนในน้ำ (DO)']
    )
    st.line_chart(chart_data)

with tab2:
    st.title("🏡 ระบบสนับสนุนการตัดสินใจสำหรับชุมชน")
    st.caption("แนวทางปฏิบัติเชิงรุกสำหรับผู้นำชุมชน คณะกรรมการประปาหมู่บ้าน และกลุ่มเกษตรกร")
    st.markdown("---")
    st.markdown(f"### สถานะการประเมิน: <span class='{status_color}'>{status_label}</span> (Risk Score: {risk_score}%)", unsafe_allow_html=True)

    col_action1, col_action2 = st.columns(2)
    with col_action1:
        st.markdown("#### 🛠️ ข้อแนะนำการปฏิบัติงานสำหรับชุมชน (Community Actions)")
        if risk_score < 30:
            st.write("1. **แจกจ่ายน้ำปกติ:** ระบบประปาหมู่บ้านและช่องทางส่งน้ำการเกษตรใช้งานได้ตามปกติ")
            st.write("2. **จัดเก็บข้อมูล:** ระบบบันทึกค่าน้ำเข้าสู่ฐานข้อมูลเฝ้าระวังของชุมชนตามปกติ")
        elif risk_score < 60:
            st.write("1. 📢 **แจ้งเตือนเกษตรกร:** สารละลาย/ความเค็มเริ่มสูง ระวังการสูบน้ำเข้าแปลงเกษตรที่ไวต่อค่าน้ำ")
            st.write("2. ⚙️ **ปรับระบบกรองประปา:** เพิ่มระยะเวลาการตกตะกอนและการกรองของระบบประปาหมู่บ้าน")
            st.write("3. 🌊 **เดินเครื่องเติมอากาศ:** สั่งเปิดกังหันน้ำ/เครื่องเติมอากาศในสระน้ำชุมชนเพื่อเพิ่มค่า DO")
            st.write("4. 🔎 **สำรวจต้นน้ำ:** ส่งตัวแทนชุมชน ตรวจเช็กจุดสูบน้ำหรือแหล่งน้ำต้นน้ำว่ามีการปนเปื้อนหรือไม่")
        else:
            st.write("1. 🚫 **ประกาศงดใช้น้ำชั่วคราว:** แจ้งห้ามใช้น้ำเพื่อการบริโภคและสูบเข้าพื้นที่การเกษตรด่วน")
            st.write("2. 🚰 **สลับแหล่งน้ำสำรอง:** เปิดใช้งานแหล่งน้ำสำรอง/น้ำบาดาลหมู่บ้านแทนแหล่งน้ำหลัก")
            st.write("3. 🧪 **ประสานงาน อบต./เทศบาล:** แจ้งเจ้าหน้าที่สิ่งแวดล้อมท้องถิ่นลงพื้นที่ตรวจวิเคราะห์เคมีฉุกเฉิน")
            st.write("4. 📲 **แจ้งเตือนหอกระจายข่าว:** ส่งข้อความแจ้งเตือนผ่าน LINE ถึงผู้ใหญ่บ้านและคณะกรรมการหมู่บ้าน")

    with col_action2:
        st.markdown("#### 📲 ระบบส่งแจ้งเตือนฉุกเฉินถึงผู้นำชุมชน (LINE Notification)")
        st.info("ส่งรายงานสถานการณ์และคำแนะนำ AI ตรงถึง LINE ของผู้ใหญ่บ้าน / ประธานประปาหมู่บ้าน")
        if st.button("🚀 ส่งรายงานเตือนภัยชุมชนเข้า LINE", use_container_width=True):
            LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
            TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"
            msg = (
                f"📢 [รายงานสถานการณ์น้ำชุมชน EEC]\n"
                f"------------------------------\n"
                f"📊 Risk Score: {risk_score}% ({status_label})\n"
                f"• pH: {ph:.1f} | TDS: {tds} ppm\n"
                f"• DO: {do:.1f} mg/L | Temp: {temp:.1f}°C\n"
                f"------------------------------\n"
                f"💡 แนวทางปฏิบัติสำหรับชุมชน:\n"
                + ("• ใช้งานได้ตามปกติ" if risk_score < 30 else "• แจ้งเตือนเฝ้าระวัง และตรวจสอบระบบกรองประปาหมู่บ้านด่วน")
            )
            payload = {"to": TARGET_USER_ID, "messages": [{"type": "text", "text": msg}]}
            headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
            res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(payload))
            if res.status_code == 200:
                st.success("✅ ส่งรายงานเตือนภัยเข้า LINE ผู้นำชุมชนสำเร็จ!")
            else:
                st.error("❌ ส่งไม่สำเร็จ")
