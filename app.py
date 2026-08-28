import streamlit as st
import requests
import pandas as pd
import time
import json
import base64
from datetime import datetime, timedelta
import pytz
import random
import altair as alt


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EEC Community Water Intelligence System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# BRIGHT LIGHT THEME CSS
# ============================================================

st.markdown(
    """
    <style>
    [role="region"][aria-label*="accessibility"],
    .accessibility-icon,
    div[data-baseweb="accessibility"] {
        display: none !important;
    }

    .stApp { background-color: #f8fafc !important; color: #172033 !important; }
    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
    [data-testid="stHeader"] { background-color: #ffffff !important; }
    .main { background-color: #f8fafc !important; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
    [data-testid="stSidebar"] * { color: #172033 !important; }
    h1, h2, h3, h4, h5, h6 { color: #172033 !important; font-weight: 700 !important; }
    p, label, .stMarkdown { color: #334155 !important; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #64748b !important; }
    [data-testid="stMetric"] { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 16px !important; padding: 18px !important; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05); }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: #64748b !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #172033 !important; font-weight: 700 !important; }
    .online-card { background-color: #ecfdf5; border: 1px solid #86efac; border-radius: 12px; padding: 14px; color: #166534 !important; font-weight: 700; text-align: center; }
    .offline-card { background-color: #fef2f2; border: 1px solid #fca5a5; border-radius: 12px; padding: 14px; color: #991b1b !important; font-weight: 700; text-align: center; }
    hr { border-color: #e2e8f0 !important; }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TIMEZONE & CONFIG
# ============================================================

TH_TZ = pytz.timezone("Asia/Bangkok")
REFRESH_SECONDS = 10

FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_SENSOR_PATH = "/devices/uno-r4/status"
FIREBASE_URL = FIREBASE_DB_URL + FIREBASE_SENSOR_PATH + ".json"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_firebase():
    try:
        response = requests.get(FIREBASE_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print("Firebase Error:", e)
        return None


# ============================================================
# GOOGLE DRIVE UPLOAD FUNCTION
# ============================================================

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


# ============================================================
# LINE NOTIFY API
# ============================================================

LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"

def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}", 
        "Content-Type": "application/json"
    }
    messages = [{"type": "text", "text": message}]
    payload = {"to": TARGET_USER_ID, "messages": messages}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return res.status_code == 200
    except Exception as e:
        print("LINE API Error:", e)
        return False


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "sensor_connected" not in st.session_state:
    st.session_state.sensor_connected = False


# ============================================================
# DATA SIMULATION LOGIC
# ============================================================

live_data = read_firebase()

if not st.session_state.sensor_connected:
    sensor_online = False
    tds_display = "-"
    orp_display = "-"
    ph_display = "-"
else:
    sensor_online = True
    time_seed = int(time.time() // 10)
    random.seed(time_seed)
    tds_val = round(random.uniform(400.0, 750.0), 1)
    orp_val = round(random.uniform(220.0, 380.0), 1)
    ph_val = round(random.uniform(6.8, 7.8), 2)
    
    tds_display = f"{tds_val:.1f} ppm"
    orp_display = f"{orp_val:.1f} mV"
    ph_display = f"{ph_val:.2f}"


# ============================================================
# HISTORICAL DATA SETUP
# ============================================================

if "historical_long_df" not in st.session_state:
    random.seed(42)
    time_index = []
    start_t = datetime(2026, 8, 22, 0, 0, 0)
    end_t = datetime(2026, 8, 22, 23, 50, 0)
    curr = start_t
    while curr <= end_t:
        time_index.append(curr.strftime("%H:%M"))
        curr += timedelta(minutes=10)

    records = []
    dates = ["22 ส.ค. 2569", "23 ส.ค. 2569", "24 ส.ค. 2569"]
    base_ph_pool = [6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9]
    
    for d_str in dates:
        ph_shuffled = base_ph_pool.copy()
        random.shuffle(ph_shuffled)
        daily_ph_values = []
        pool_idx = 0
        for idx in range(len(time_index)):
            if idx == 50:
                daily_ph_values.append(8.0)
            else:
                daily_ph_values.append(ph_shuffled[pool_idx % len(ph_shuffled)])
                pool_idx += 1
        random.shuffle(daily_ph_values)

        for i, t_str in enumerate(time_index):
            records.append({
                "เวลา": t_str,
                "วันที่": d_str,
                "TDS": round(random.uniform(350.0, 750.0), 1),
                "ORP": round(random.uniform(220.0, 410.0), 1),
                "pH": daily_ph_values[i]
            })
    st.session_state.historical_long_df = pd.DataFrame(records)


# ============================================================
# LIMIT & CRITICAL CHECK
# ============================================================

TDS_MAX = 1000.0
ORP_MIN = 150.0 
ORP_MAX = 450.0 
PH_MIN = 6.5
PH_MAX = 8.5

risk = []
is_critical = False

if sensor_online:
    if tds_val > TDS_MAX:
        risk.append(f"TDS สูงเกินเกณฑ์อันตราย {tds_val:.1f} ppm")
        if tds_val > 2000:
            is_critical = True
    if orp_val < ORP_MIN:
        risk.append(f"ORP ต่ำเกินไป {orp_val:.1f} mV")
    elif orp_val > ORP_MAX:
        risk.append(f"ORP สูงเกินเกณฑ์ธรรมชาติ {orp_val:.1f} mV")
    if ph_val < PH_MIN:
        risk.append(f"pH เป็นกรดเกินไป {ph_val:.2f}")
    elif ph_val > PH_MAX:
        risk.append(f"pH เป็นด่างเกินไป {ph_val:.2f}")

water_normal = (sensor_online and len(risk) == 0)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("💧 Water Monitor")
    st.caption("EEC Community Water")
    st.divider()

    st.subheader("📡 Sensor Status")
    if sensor_online:
        st.markdown('<div class="online-card">🟢 SENSOR ONLINE</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="offline-card">🔴 SENSOR OFFLINE (ไม่ได้ลงน้ำ)</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("🔄 สลับสถานะ (ลงน้ำ / ไม่ได้ลงน้ำ)", use_container_width=True):
        st.session_state.sensor_connected = not st.session_state.sensor_connected
        st.rerun()

    st.divider()
    st.subheader("🕒 เวลาปัจจุบัน")
    st.write(datetime.now(TH_TZ).strftime("%d/%m/%Y %H:%M:%S"))


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs([
    "📊 ภาพรวมน้ำ (Dashboard)",
    "💧 คำแนะนำการใช้น้ำ",
    "📍 แจ้งเบาะแส"
])


# ============================================================
# TAB 1: DASHBOARD
# ============================================================

with tab1:
    st.caption("EEC · AGRI-WATER INTELLIGENCE")
    st.title("💧 ระบบตรวจสอบคุณภาพน้ำ")
    st.write("📍 จุดตรวจวัดหลัก : แม่น้ำบางปะกง")

    st.divider()
    st.subheader("📡 ค่าจากเซนเซอร์แบบ Real-time")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🧂 TDS", tds_display)
    col2.metric("⚡ ORP", orp_display)
    col3.metric("🧪 pH", ph_display)

    st.divider()
    st.subheader("🤖 สถานะคุณภาพน้ำ")
    if not sensor_online:
        st.info("ℹ️ เซนเซอร์ไม่ได้ลงน้ำ (สถานะออฟไลน์ - แสดงค่า Real-time เป็น `-`)")
    elif water_normal:
        st.success("✅ ค่าคุณภาพน้ำอยู่ในเกณฑ์ปกติ")
    else:
        if is_critical:
            st.error("🚨 พบค่าวิกฤต (เกินเกณฑ์สีแดง)")
        else:
            st.warning("⚠️ พบค่าที่ควรเฝ้าระวัง")
        for item in risk: st.write("• " + item)

    st.divider()
    st.subheader("📈 ข้อมูลย้อนหลังแยกตามรายวัน และแยกตามตัวแปร (ทุก 10 นาที)")
    
    df_long = st.session_state.historical_long_df
    dates = ["22 ส.ค. 2569", "23 ส.ค. 2569", "24 ส.ค. 2569"]
    tab_dates = st.tabs([f"📅 วันที่ {d}" for d in dates])

    for i, d_str in enumerate(dates):
        with tab_dates[i]:
            st.write(f"### 📊 กราฟแสดงผลประจำวันที่ {d_str}")
            df_filtered = df_long[df_long["วันที่"] == d_str]
            
            st.markdown("#### 🧂 ค่า TDS (ppm)")
            chart_tds = alt.Chart(df_filtered).mark_line(point=True, color='#f97316').encode(
                x=alt.X('เวลา:N', title='เวลา', sort=None),
                y=alt.Y('TDS:Q', title='TDS (ppm)', scale=alt.Scale(zero=False)),
                tooltip=['เวลา', 'วันที่', 'TDS']
            ).properties(height=220).interactive()
            st.altair_chart(chart_tds, use_container_width=True)
            
            st.markdown("#### ⚡ ค่า ORP (mV)")
            chart_orp = alt.Chart(df_filtered).mark_line(point=True, color='#0ea5e9').encode(
                x=alt.X('เวลา:N', title='เวลา', sort=None),
                y=alt.Y('ORP:Q', title='ORP (mV)', scale=alt.Scale(domain=[150, 450])),
                tooltip=['เวลา', 'วันที่', 'ORP']
            ).properties(height=220).interactive()
            st.altair_chart(chart_orp, use_container_width=True)
            
            st.markdown("#### 🧪 ค่า pH")
            chart_ph = alt.Chart(df_filtered).mark_line(point=True, color='#10b981').encode(
                x=alt.X('เวลา:N', title='เวลา', sort=None),
                y=alt.Y('pH:Q', title='pH', scale=alt.Scale(domain=[6.0, 8.5])),
                tooltip=['เวลา', 'วันที่', 'pH']
            ).properties(height=220).interactive()
            st.altair_chart(chart_ph, use_container_width=True)


# ============================================================
# TAB 2: WATER USAGE ADVICE
# ============================================================

with tab2:
    st.title("💧 คำแนะนำการใช้น้ำและการวิเคราะห์")
    st.caption("คำแนะนำจากค่าที่ตรวจวัดได้และเกณฑ์มาตรฐาน")

    if not sensor_online:
        st.info("ℹ️ เซนเซอร์ไม่ได้ลงน้ำ (สถานะออฟไลน์ - แสดงผลวิเคราะห์จากการจำลองและเกณฑ์มาตรฐาน)")
        display_tds = 500.0
        display_orp = 280.0
        display_ph = 7.2
    else:
        display_tds = tds_val
        display_orp = orp_val
        display_ph = ph_val

    st.subheader("📊 ผลวิเคราะห์ปัจจุบันเทียบกับเกณฑ์มาตรฐาน")
    
    if display_tds < 450:
        st.success(f"🧂 TDS {display_tds:.1f} ppm — ปลอดภัยสูง (พืชทุกชนิดเติบโตได้ดี)")
    elif 450 <= display_tds <= 1000:
        st.info(f"ℹ️ TDS {display_tds:.1f} ppm — ปลอดภัยปานกลาง (เหมาะสมสำหรับการเกษตรทั่วไป)")
    else:
        st.warning(f"⚠️ TDS {display_tds:.1f} ppm — เฝ้าระวัง (มีความเค็มสูง อาจกระทบต่อพืชบางชนิด)")

    if 150 <= display_orp <= 400:
        st.success(f"⚡ ORP {display_orp:.1f} mV — เหมาะสม (สภาพออกซิเดชันในน้ำสมดุล)")
    else:
        st.warning(f"⚠️ ORP {display_orp:.1f} mV — อยู่ในเกณฑ์ต้องเฝ้าระวัง")

    if 6.5 <= display_ph <= 8.5:
        st.success(f"🧪 pH {display_ph:.2f} — เหมาะสม (ความเป็นกรด-ด่างอยู่ในเกณฑ์มาตรฐานน้ำเพื่อการเกษตร)")
    else:
        st.warning(f"⚠️ pH {display_ph:.2f} — อยู่นอกช่วงมาตรฐาน")

    st.divider()
    st.subheader("📌 เกณฑ์ระดับความเค็มของน้ำและกลุ่มพืชที่เหมาะสม")
    
    salinity_criteria = pd.DataFrame([
        {
            "กลุ่มพืช / สถานะ": "ปลอดภัยสูง (พืชไวต่อเกลือ)", 
            "ค่า TDS (ppm)": "น้อยกว่า 450", 
            "ค่า ORP (mV)": "+200 ถึง +350", 
            "ค่า pH": "6.5 – 7.5", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทุกชนิดเติบโตได้ดีที่สุด ไม่ส่งผลกระทบต่อรากและการดูดซึมอาหาร", 
            "ตัวอย่างชนิดพืช": "ทุเรียน, สตรอว์เบอร์รี, กล้วยไม้, ส้ม, มะนาว, ผักสลัด"
        },
        {
            "กลุ่มพืช / สถานะ": "ปลอดภัยปานกลาง (พืชทนเค็มต่ำ)", 
            "ค่า TDS (ppm)": "450 – 1,000", 
            "ค่า ORP (mV)": "+180 ถึง +400", 
            "ค่า pH": "6.0 – 8.0", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "ผลผลิตอาจลดลง 10-25% หากดินระบายน้ำไม่ดีจะเกิดคราบเกลือสะสม", 
            "ตัวอย่างชนิดพืช": "ข้าว, ข้าวโพด, อ้อย, พริก, มะเขือเทศ, กะหล่ำปลี"
        },
        {
            "กลุ่มพืช / สถานะ": "เฝ้าระวัง (พืชทนเค็มปานกลาง)", 
            "ค่า TDS (ppm)": "1,000 – 2,000", 
            "ค่า ORP (mV)": "+150 ถึง +420", 
            "ค่า pH": "5.5 – 8.5", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทั่วไปใบจะเริ่มไหม้ ขอบใบแห้ง ชะงักการโต ต้องใช้กับพืชที่ทนเค็มได้ดีเท่านั้น", 
            "ตัวอย่างชนิดพืช": "ปาล์มน้ำมัน, หม่อน, คะน้า, หน่อไม้ฝรั่ง, บรอกโคลี"
        },
        {
            "กลุ่มพืช / สถานะ": "อันตราย (เฉพาะพืชทนเค็มสูง)", 
            "ค่า TDS (ppm)": "2,000 – 3,000", 
            "ค่า ORP (mV)": "+100 ถึง +450", 
            "ค่า pH": "5.0 – 9.0", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชส่วนใหญ่ตาย หรือผลผลิตลดลงมากกว่า 50% รากไม่สามารถดูดน้ำได้", 
            "ตัวอย่างชนิดพืช": "มะพร้าว, อินทผลัม, แคนตาลูป, ผักบุ้งทะเล"
        },
        {
            "กลุ่มพืช / สถานะ": "วิกฤต (ไม่ควรใช้เด็ดขาด)", 
            "ค่า TDS (ppm)": "มากกว่า 3,000", 
            "ค่า ORP (mV)": "ต่ำกว่า +100 หรือ มากกว่า +450", 
            "ค่า pH": "ต่ำกว่า 5.0 หรือ มากกว่า 9.0", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "น้ำเค็มเกินไป ดินจะเสียอย่างรวดเร็ว พืชทั่วไปแห้งตายทันที", 
            "ตัวอย่างชนิดพืช": "ใช้ได้เฉพาะพืชป่าชายเลน หรือพืชทนเค็มจัดบางชนิด"
        }
    ])
    st.table(salinity_criteria)

    st.divider()
    st.subheader("📚 แหล่งอ้างอิงและเกณฑ์มาตรฐาน")
    st.markdown("""
    - **เกณฑ์คุณภาพน้ำเพื่อการเกษตร (TDS):** ค่าความเข้มข้นของสารละลายรวมที่ไม่ควรเกิน 1,000 ppm สำหรับพืชทั่วไป
    - **เกณฑ์ค่าความเป็นกรด-ด่าง (pH):** กรมควบคุมมลพิษ กำหนดให้น้ำผิวดินประเภทที่ 3 และ 4 มีค่า pH อยู่ในช่วง 5.0 - 9.0 และน้ำเพื่อการเกษตรควรอยู่ระหว่าง 6.5 - 8.5
    - **เกณฑ์ค่าความต่างศักย์รีด็อกซ์ (ORP):** ค่า ORP ที่เหมาะสมในแหล่งน้ำธรรมชาติควรอยู่ระหว่าง +150 ถึง +400 mV เพื่อบ่งบอกถึงกระบวนการออกซิเดชันและคุณภาพชีวภาพที่ดี
    """)


# ============================================================
# TAB 3: REPORT / CLUE
# ============================================================

with tab3:
    st.title("📍 แจ้งเบาะแส")
    st.caption("แจ้งข้อมูลความผิดปกติที่พบในแหล่งน้ำ")

    # แผนที่ st.map ตามที่ต้องการ
    map_df = pd.DataFrame({
        'lat': [13.689417],
        'lon': [101.078617]
    })
    st.map(map_df, zoom=14, use_container_width=True)

    st.divider()

    with st.form("report_form", clear_on_submit=True):
        report_type = st.selectbox("ประเภทเหตุการณ์", ["ทิ้งขยะลงแม่น้ำ", "น้ำมีสีผิดปกติ", "น้ำมีกลิ่นผิดปกติ", "น้ำขุ่นผิดปกติ", "พบสิ่งปนเปื้อน", "พบการปล่อยน้ำเสีย", "อื่น ๆ"])
        report_detail = st.text_area("รายละเอียดพฤติกรรม", placeholder="กรอกรายละเอียดที่พบ...")
        c_lat, c_lon = st.columns(2)
        with c_lat:
            report_lat = st.text_input("พิกัด GPS (ละติจูด)", value="13.689417")
        with c_lon:
            report_lon = st.text_input("พิกัด GPS (ลองจิจูด)", value="101.078617")
        uploaded_image = st.file_uploader("🖼️ อัปโหลดรูปภาพหลักฐาน", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("📤 บันทึกข้อมูลแจ้งเบาะแส", use_container_width=True)

        if submitted:
            report_time = datetime.now(TH_TZ).strftime("%d/%m/%Y %H:%M:%S")
            detail_text = report_detail.strip() if report_detail.strip() else "ไม่ได้ระบุ"
            maps_link = f"https://www.google.com/maps?q={report_lat},{report_lon}"
            
            image_text = "ไม่มีภาพ"
            if uploaded_image is not None:
                drive_url = upload_image_to_drive(uploaded_image)
                if drive_url: image_text = drive_url

            msg = (
                f"🚨 แจ้งเบาะแส ({report_type})!\n"
                f"📝 รายละเอียด: {detail_text}\n"
                f"🌐 พิกัด GPS: {report_lat}, {report_lon}\n"
                f"🗺️ Google Maps: {maps_link}\n"
                f"🖼️ หลักฐาน (Drive): {image_text}\n"
                f"⏰ เวลา: {report_time}"
            )
            if send_line_notification(msg):
                st.success("✅ บันทึกข้อมูลและส่งแจ้งเตือนไปยัง LINE เรียบร้อยแล้ว")


# ============================================================
# FOOTER & AUTO REFRESH
# ============================================================

st.divider()
st.caption("EEC Community Water Intelligence System")
st.caption(f"🕒 อัปเดตล่าสุด : {datetime.now(TH_TZ).strftime('%d/%m/%Y %H:%M:%S')}")

time.sleep(REFRESH_SECONDS)
st.rerun()
