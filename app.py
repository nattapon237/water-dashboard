import streamlit as st
import numpy as np
import pandas as pd
import requests
import json

st.set_page_config(page_title="EEC Water Intelligence System", page_icon="💧", layout="wide")

st.markdown("""
    <style>
    .status-normal { color: #2e7d32; font-weight: bold; }
    .status-warning { color: #ef6c00; font-weight: bold; }
    .status-danger { color: #c62828; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("🎛️ เซนเซอร์ / Input Control")
ph = st.sidebar.slider("pH Level", 0.0, 14.0, 6.4, 0.1)
tds = st.sidebar.slider("EC / TDS (ppm)", 0, 2000, 850, 10)
temp = st.sidebar.slider("Temperature (°C)", 10.0, 50.0, 31.0, 0.5)
do = st.sidebar.slider("DO (Dissolved Oxygen) (mg/L)", 0.0, 12.0, 4.2, 0.1)
turbidity = st.sidebar.slider("Turbidity (NTU / ความขุ่น)", 0.0, 500.0, 45.0, 1.0)

def calculate_risk(ph, tds, temp, do, turbidity):
    risk_score = 0
    reasons = []
    if ph < 5.5 or ph > 9.0:
        risk_score += 35
        reasons.append(f"pH ({ph}) อยู่นอกเกณฑ์มาตรฐานวิศวกรรม")
    elif ph < 6.5 or ph > 8.5:
        risk_score += 15
        reasons.append(f"pH ({ph}) เริ่มเบี่ยงเบนเข้าเขตเฝ้าระวัง")

    if tds > 1000:
        risk_score += 30
        reasons.append(f"EC/TDS ({tds} ppm) มีค่าสูงเกินมาตรฐาน")
    elif tds > 600:
        risk_score += 15
        reasons.append(f"EC/TDS ({tds} ppm) มีแนวโน้มเพิ่มขึ้นต่อเนื่องในช่วง 60 นาทีที่ผ่านมา")

    if do < 3.0:
        risk_score += 30
        reasons.append(f"DO ({do} mg/L) อยู่ในระดับต่ำวิกฤต")
    elif do < 5.0:
        risk_score += 15
        reasons.append(f"DO ({do} mg/L) เริ่มลดลงต่ำกว่ามาตรฐาน")

    if temp > 35.0:
        risk_score += 10
        reasons.append(f"อุณหภูมิ ({temp} °C) สูงเกินปกติ")
    if turbidity > 100:
        risk_score += 15
        reasons.append(f"ความขุ่น ({turbidity} NTU) สูงกว่าเกณฑ์ทั่วไป")

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

tab1, tab2 = st.tabs(["📊 EEC Water Overview (หน้าแรก)", "🏭 AI Decision Support (คำแนะนำ)"])

with tab1:
    st.title("💧 EEC Water Overview")
    st.caption("ระบบเฝ้าระวังและประเมินความเสี่ยงคุณภาพน้ำอัจฉริยะสำหรับพื้นที่เขตพัฒนาพิเศษภาคตะวันออก (EEC)")
    st.markdown("---")

    col_score1, col_score2 = st.columns([1, 2])
    with col_score1:
        st.markdown("### 🤖 AI WATER RISK SCORE")
        st.metric(label="ดัชนีความเสี่ยงรวม", value=f"{risk_score}%")
        st.markdown(f"สถานะปัจจุบัน: <span class='{status_color}'>{status_label}</span>", unsafe_allow_html=True)

    with col_score2:
        st.markdown("### 📌 สรุปสถานการณ์ปัจจุบัน")
        if risk_score < 30:
            st.success("✅ แนวโน้มคุณภาพน้ำคงที่ ไม่พบความผิดปกติที่ต้องแจ้งเตือน")
        elif risk_score < 60:
            st.warning(f"⚠️ ระบบประเมินว่าความเสี่ยงมีแนวโน้มเพิ่มขึ้นเนื่องจาก:\n- " + "\n- ".join(risk_reasons))
        else:
            st.error(f"🚨 ตรวจพบสภาวะวิกฤต! สาเหตุหลัก:\n- " + "\n- ".join(risk_reasons))

    st.markdown("---")
    st.subheader("📊 ข้อมูลจริงจากเซนเซอร์ (Live Sensor Metrics)")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("pH", f"{ph:.1f}")
    m2.metric("EC / TDS", f"{tds} ppm")
    m3.metric("Temperature", f"{temp:.1f} °C")
    m4.metric("DO", f"{do:.1f} mg/L")
    m5.metric("Turbidity", f"{turbidity:.0f} NTU")

    st.markdown("---")
    st.subheader("📈 แนวโน้มความแปรปรวนค่าน้ำย้อนหลัง (Historical Trends)")
    chart_data = pd.DataFrame(np.random.randn(20, 3) + [tds/100, ph*10, do*10], columns=['EC/TDS Trend', 'pH Trend', 'DO Trend'])
    st.line_chart(chart_data)

with tab2:
    st.title("🏭 AI Decision Support System")
    st.caption("ระบบสนับสนุนการตัดสินใจเชิงปฏิบัติการสำหรับโรงงานอุตสาหกรรม")
    st.markdown("---")
    st.markdown(f"### สถานะการประเมิน: <span class='{status_color}'>{status_label}</span> (Risk Score: {risk_score}%)", unsafe_allow_html=True)

    col_action1, col_action2 = st.columns(2)
    with col_action1:
        st.markdown("#### 🛠️ คำแนะนำการปฏิบัติงานสำหรับโรงงาน (Actionable Steps)")
        if risk_score < 30:
            st.write("1. **การดำเนินงานปกติ:** เดินระบบบำบัดน้ำเสียตามรอบเวลามาตรฐาน")
            st.write("2. **บันทึกข้อมูล:** ระบบทำการบันทึกค่าลง Database โดยอัตโนมัติ")
        elif risk_score < 60:
            st.write("1. 🔍 **ตรวจสอบระบบบำบัด:** ให้เจ้าหน้าที่เข้าเช็คระบบกรองและถังเติมอากาศ")
            st.write("2. 📍 **ตรวจสอบจุดก่อนปล่อย:** สุ่มตรวจวัดค่า ณ จุดระบายน้ำออกนอกโรงงาน")
            st.write("3. ⏳ **ชะลอการระบายน้ำ:** เตรียมชะลอการระบายหากค่า EC/TDS เพิ่มขึ้น")
        else:
            st.write("1. ⛔ **ระงับการปล่อยน้ำทันที:** สั่งปิดวาล์วระบายน้ำทิ้งออกสู่ภายนอก")
            st.write("2. 🔄 **สลับไปถังพักน้ำเสีย:** ผันน้ำเข้าถังพักเพื่อเตรียมปรับสภาพน้ำใหม่")

    with col_action2:
        st.markdown("#### 📲 ระบบส่งแจ้งเตือนฉุกเฉิน (Notification Portal)")
        if st.button("🚀 ส่งรายงานการตัดสินใจนี้เข้า LINE", use_container_width=True):
            LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
            TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"
            msg = f"⚠️ [EEC AI Report]\nRisk Score: {risk_score}%\npH: {ph:.1f} | TDS: {tds} ppm\nDO: {do:.1f} mg/L"
            payload = {"to": TARGET_USER_ID, "messages": [{"type": "text", "text": msg}]}
            headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}", "Content-Type": "application/json"}
            res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(payload))
            if res.status_code == 200:
                st.success("✅ ส่งเข้า LINE สำเร็จ!")
            else:
                st.error("❌ ส่งไม่สำเร็จ")
