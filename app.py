import streamlit as st
import requests
import pandas as pd
import time
import json
from datetime import datetime
import pytz


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
# BRIGHT LIGHT THEME
# ============================================================

st.markdown(
    """
    <style>
    /* MAIN */
    .stApp { background-color: #f8fafc !important; color: #172033 !important; }
    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
    [data-testid="stHeader"] { background-color: #ffffff !important; }
    .main { background-color: #f8fafc !important; }

    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
    [data-testid="stSidebar"] * { color: #172033 !important; }

    /* TEXT */
    h1, h2, h3, h4, h5, h6 { color: #172033 !important; font-weight: 700 !important; }
    p, label, .stMarkdown { color: #334155 !important; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #64748b !important; }

    /* METRIC */
    [data-testid="stMetric"] { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 16px !important; padding: 18px !important; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05); }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: #64748b !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #172033 !important; font-weight: 700 !important; }

    /* INPUTS & BUTTONS */
    [data-baseweb="select"] { background-color: #ffffff !important; }
    [data-baseweb="select"] * { color: #172033 !important; }
    input, textarea { background-color: #ffffff !important; color: #172033 !important; border: 1px solid #cbd5e1 !important; }
    input::placeholder, textarea::placeholder { color: #94a3b8 !important; }
    .stButton > button { background-color: #ffffff !important; color: #172033 !important; border: 1px solid #cbd5e1 !important; border-radius: 10px !important; font-weight: 600 !important; }
    .stButton > button:hover { background-color: #f0f9ff !important; color: #0369a1 !important; border-color: #7dd3fc !important; }

    /* CUSTOM CARDS */
    .water-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); }
    .online-card { background-color: #ecfdf5; border: 1px solid #86efac; border-radius: 12px; padding: 14px; color: #166534 !important; font-weight: 700; }
    .offline-card { background-color: #fef2f2; border: 1px solid #fca5a5; border-radius: 12px; padding: 14px; color: #991b1b !important; font-weight: 700; }
    
    hr { border-color: #e2e8f0 !important; }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TIMEZONE & CONFIG
# ============================================================

TH_TZ = pytz.timezone("Asia/Bangkok")
REFRESH_SECONDS = 2

# Firebase
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_SENSOR_PATH = "/devices/uno-r4/status"
FIREBASE_URL = FIREBASE_DB_URL + FIREBASE_SENSOR_PATH + ".json"


# ============================================================
# LINE NOTIFY / MESSAGING API
# ============================================================

LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"

def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}", 
        "Content-Type": "application/json"
    }
    messages = [
        {"type": "text", "text": message}
    ]
    payload = {
        "to": TARGET_USER_ID, 
        "messages": messages
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return res.status_code == 200
    except Exception as e:
        print("LINE API Error:", e)
        return False


# ============================================================
# DATA FUNCTIONS
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

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except:
        return default

def sensor_is_online(data):
    if not isinstance(data, dict):
        return False
    sensor_keys = ["tds", "turbidity", "do"]
    for key in sensor_keys:
        if key in data and data.get(key) is not None:
            try:
                float(data.get(key))
                return True
            except:
                pass
    return False


# ============================================================
# PROCESS DATA
# ============================================================

live_data = read_firebase()

tds = safe_float(live_data.get("tds")) if isinstance(live_data, dict) else 0.0
turbidity = safe_float(live_data.get("turbidity")) if isinstance(live_data, dict) else 0.0
do_value = safe_float(live_data.get("do")) if isinstance(live_data, dict) else 0.0

sensor_online = sensor_is_online(live_data)

if "history" not in st.session_state:
    st.session_state.history = []

if sensor_online:
    now = datetime.now(TH_TZ)
    st.session_state.history.append({
        "เวลา": now.strftime("%H:%M:%S"),
        "TDS": tds,
        "Turbidity": turbidity,
        "DO": do_value
    })
    st.session_state.history = st.session_state.history[-60:]


# ============================================================
# WATER QUALITY LIMIT
# ============================================================

TDS_MAX = 1000.0
TURBIDITY_MAX = 100.0
DO_MIN = 4.0

risk = []
if sensor_online:
    if tds > TDS_MAX: risk.append(f"TDS สูง {tds:.1f} ppm")
    if turbidity > TURBIDITY_MAX: risk.append(f"ความขุ่นสูง {turbidity:.1f} NTU")
    if do_value < DO_MIN: risk.append(f"DO ต่ำ {do_value:.2f} mg/L")

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
        st.caption("กำลังรับค่าจาก ESP32 ผ่าน Firebase")
    else:
        st.markdown('<div class="offline-card">🔴 SENSOR OFFLINE</div>', unsafe_allow_html=True)
        st.caption("ไม่พบค่าจาก ESP32")

    st.divider()
    st.subheader("📊 Parameters")
    st.write("🧂 TDS")
    st.write("🌫️ Turbidity")
    st.write("🫧 DO")

    st.divider()
    st.write("🔄 Auto Refresh")
    st.info(f"อัปเดตทุก {REFRESH_SECONDS} วินาที")

    st.divider()
    st.write("🕒 เวลา")
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
    st.write("📍 จุดตรวจวัด : แม่น้ำบางปะกง")
    st.caption("ESP32 → Firebase → Dashboard")

    if sensor_online:
        st.success("🟢 SENSOR ONLINE · รับค่าจาก ESP32 แล้ว")
    else:
        st.error("🔴 SENSOR OFFLINE · ไม่พบข้อมูลจากเซนเซอร์")

    st.divider()
    st.subheader("📡 ค่าจากเซนเซอร์แบบ Real-time")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🧂 TDS", f"{tds:.1f} ppm")
    col2.metric("🌫️ Turbidity", f"{turbidity:.1f} NTU")
    col3.metric("🫧 DO", f"{do_value:.2f} mg/L")

    st.divider()
    st.subheader("🤖 สถานะคุณภาพน้ำ")
    if not sensor_online:
        st.info("⏳ กำลังรอข้อมูลจากเซนเซอร์...")
    elif water_normal:
        st.success("✅ ค่าคุณภาพน้ำอยู่ในเกณฑ์ปกติ")
    else:
        st.warning("⚠️ พบค่าที่ควรเฝ้าระวัง")
        for item in risk: st.write("• " + item)

    st.divider()
    st.subheader("📈 กราฟค่าจากเซนเซอร์")
    if len(st.session_state.history) > 0:
        graph_df = pd.DataFrame(st.session_state.history).set_index("เวลา")
        selected_parameter = st.selectbox("เลือกค่าที่ต้องการดู", ["TDS", "Turbidity", "DO"], key="graph_parameter")
        st.line_chart(graph_df[[selected_parameter]], use_container_width=True)
    else:
        st.info("⏳ รอข้อมูลจากเซนเซอร์...")


# ============================================================
# TAB 2: WATER USAGE ADVICE
# ============================================================

with tab2:
    st.title("💧 คำแนะนำการใช้น้ำ")
    st.caption("คำแนะนำจากค่าที่ตรวจวัดได้จาก ESP32")

    if not sensor_online:
        st.warning("🔴 ยังไม่มีข้อมูลจากเซนเซอร์")
    else:
        st.subheader("📊 ผลวิเคราะห์ปัจจุบัน")
        if tds <= TDS_MAX: st.success(f"🧂 TDS {tds:.1f} ppm — อยู่ในเกณฑ์")
        else: st.warning(f"⚠️ TDS {tds:.1f} ppm — ควรเฝ้าระวัง")

        if turbidity <= TURBIDITY_MAX: st.success(f"🌫️ Turbidity {turbidity:.1f} NTU — อยู่ในเกณฑ์")
        else: st.warning(f"⚠️ Turbidity {turbidity:.1f} NTU — ความขุ่นสูง")

        if do_value >= DO_MIN: st.success(f"🫧 DO {do_value:.2f} mg/L — อยู่ในเกณฑ์")
        else: st.warning(f"⚠️ DO {do_value:.2f} mg/L — ออกซิเจนละลายต่ำ")

        st.divider()
        st.subheader("🌱 แนวทางการใช้น้ำ")
        if len(risk) == 0:
            st.success("✅ สามารถนำข้อมูลไปประกอบการวางแผนใช้น้ำเพื่อการเกษตรได้")
        else:
            st.warning("⚠️ พบค่าที่ควรเฝ้าระวัง ไม่ควรตัดสินใจจากค่าการวัดเพียงครั้งเดียว")


# ============================================================
# TAB 3: REPORT / CLUE (พร้อมแจ้งเตือน LINE รูปแบบใหม่)
# ============================================================

with tab3:
    st.title("📍 แจ้งเบาะแส")
    st.caption("แจ้งข้อมูลความผิดปกติที่พบในแหล่งน้ำ")

    st.markdown(
        """
        <div class="water-card">
        <h3>📢 แจ้งปัญหาคุณภาพน้ำ</h3>
        ใช้สำหรับบันทึกข้อมูลเมื่อพบความผิดปกติของแม่น้ำบางปะกง หรือพบการลักลอบทิ้งขยะ
        </div>
        """,
        unsafe_allow_html=True
    )

    report_type = st.selectbox(
        "ประเภทเหตุการณ์",
        ["ทิ้งขยะลงแม่น้ำ", "น้ำมีสีผิดปกติ", "น้ำมีกลิ่นผิดปกติ", "น้ำขุ่นผิดปกติ", "พบสิ่งปนเปื้อน", "พบการปล่อยน้ำเสีย", "อื่น ๆ"]
    )

    report_detail = st.text_area("รายละเอียดพฤติกรรม", placeholder="กรอกรายละเอียดที่พบ...")

    col_lat, col_lon = st.columns(2)
    with col_lat:
        report_lat = st.text_input("พิกัด GPS (ละติจูด)", placeholder="เช่น 13.6900")
    with col_lon:
        report_lon = st.text_input("พิกัด GPS (ลองจิจูด)", placeholder="เช่น 101.1700")

    report_image = st.text_input("ลิงก์รูปภาพหลักฐาน (เช่น Google Drive)", placeholder="https://drive.google.com/...")

    if st.button("📤 บันทึกข้อมูลแจ้งเบาะแส", use_container_width=True):

        report_time = datetime.now(TH_TZ).strftime("%d/%m/%Y %H:%M:%S")

        # จัดการค่าว่าง
        detail_text = report_detail.strip() if report_detail.strip() else "ไม่ได้ระบุ"
        lat_text = report_lat.strip() if report_lat.strip() else "0.0"
        lon_text = report_lon.strip() if report_lon.strip() else "0.0"
        image_text = report_image.strip() if report_image.strip() else "ไม่มีภาพ"
        maps_link = f"https://www.google.com/maps?q={lat_text},{lon_text}"

        report_data = {
            "เวลา": report_time,
            "ประเภท": report_type,
            "รายละเอียด": detail_text,
            "พิกัด": f"{lat_text}, {lon_text}"
        }

        st.session_state["last_report"] = report_data

        # --- จัดรูปแบบข้อความแจ้งเตือนตามภาพ ---
        msg = (
            f"🚨 แจ้งเบาะแส ({report_type})!\n"
            f"📝 รายละเอียดพฤติกรรม: {detail_text}\n"
            f"🌐 พิกัด GPS: {lat_text}, {lon_text}\n"
            f"🗺️ Google Maps: {maps_link}\n"
            f"🖼️ ภาพถ่ายหลักฐาน: {image_text}\n"
            f"⏰ เวลาแจ้ง: {report_time} (ICT)\n"
            f"⚠️\n"
            f"โปรดส่งเจ้าหน้าที่เข้าตรวจสอบพื้นที่ด่วน!"
        )

        # ส่งข้อความ
        line_status = send_line_notification(msg)

        if line_status:
            st.success("✅ บันทึกข้อมูลและส่งแจ้งเตือนไปยัง LINE เรียบร้อยแล้ว")
        else:
            st.warning("⚠️ บันทึกข้อมูลแล้ว แต่ไม่สามารถส่งแจ้งเตือนไป LINE ได้ (เช็ค Token/User ID)")


    if "last_report" in st.session_state:
        st.divider()
        st.subheader("📋 รายการล่าสุด")
        st.json(st.session_state["last_report"])


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption("EEC Community Water Intelligence System")
st.caption(f"🕒 อัปเดตล่าสุด : {datetime.now(TH_TZ).strftime('%d/%m/%Y %H:%M:%S')}")


# ============================================================
# AUTO REFRESH
# ============================================================

time.sleep(REFRESH_SECONDS)
st.rerun()
