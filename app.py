import streamlit as st
import requests
import pandas as pd
import time
import json
import base64
from datetime import datetime, timedelta
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
    sensor_keys = ["tds", "orp"]
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

tds = safe_float(live_data.get("tds")) if isinstance(live_data, dict) else 250.0
orp_value = safe_float(live_data.get("orp")) if isinstance(live_data, dict) else 220.0

sensor_online = sensor_is_online(live_data)

# สร้างข้อมูลย้อนหลังจำลองระหว่างวันที่ 22-24 ส.ค. 2569 สำหรับกราฟ
if "historical_august" not in st.session_state:
    mock_data = []
    start_time = datetime(2026, 8, 22, 0, 0, 0, tzinfo=TH_TZ)
    end_time = datetime(2026, 8, 24, 23, 0, 0, tzinfo=TH_TZ)
    
    current_t = start_time
    import random
    random.seed(42)
    
    while current_t <= end_time:
        mock_data.append({
            "เวลา": current_t.strftime("%d/%m/%Y %H:%M"),
            "TDS": round(240 + random.uniform(-20, 30), 1),
            "ORP": round(210 + random.uniform(-30, 40), 1)
        })
        current_t += timedelta(hours=3)
    st.session_state.historical_august = mock_data


# ============================================================
# WATER QUALITY LIMIT
# ============================================================

TDS_MAX = 1000.0
ORP_MIN = 150.0 
ORP_MAX = 400.0 

risk = []
if sensor_online:
    if tds > TDS_MAX: risk.append(f"TDS สูง {tds:.1f} ppm")
    if orp_value < ORP_MIN: risk.append(f"ORP ต่ำเกินไป {orp_value:.1f} mV")
    elif orp_value > ORP_MAX: risk.append(f"ORP สูงเกินเกณฑ์ธรรมชาติ {orp_value:.1f} mV")

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
    st.write("⚡ ORP")

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
    
    col1, col2 = st.columns(2)
    col1.metric("🧂 TDS", f"{tds:.1f} ppm")
    col2.metric("⚡ ORP", f"{orp_value:.1f} mV")

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
    st.subheader("📈 กราฟแสดงข้อมูลย้อนหลังระหว่างวันที่ 22-24 ส.ค. 2569")
    
    graph_df = pd.DataFrame(st.session_state.historical_august)
    graph_df = graph_df.set_index("เวลา")
    
    selected_parameter = st.selectbox("เลือกค่าที่ต้องการดู", ["TDS", "ORP"], key="graph_parameter")
    st.line_chart(graph_df[[selected_parameter]], use_container_width=True)


# ============================================================
# TAB 2: WATER USAGE ADVICE
# ============================================================

with tab2:
    st.title("💧 คำแนะนำการใช้น้ำ")
    st.caption("คำแนะนำจากค่าที่ตรวจวัดได้จาก ESP32 และเกณฑ์ความเค็ม")

    if not sensor_online:
        st.warning("🔴 ยังไม่มีข้อมูลจากเซนเซอร์ (แสดงผลจากค่าเริ่มต้น)")
    
    st.subheader("📊 ผลวิเคราะห์ปัจจุบัน")
    
    # TDS Analysis based on Salinity Criteria
    if tds < 450:
        st.success(f"🧂 TDS {tds:.1f} ppm — ปลอดภัยสูง (พืชทุกชนิดเติบโตได้ดี)")
    elif 450 <= tds <= 1000:
        st.info(f"ℹ️ TDS {tds:.1f} ppm — ปลอดภัยปานกลาง (พืชทนเค็มต่ำ ผลผลิตอาจลดลง 10-25%)")
    elif 1000 < tds <= 2000:
        st.warning(f"⚠️ TDS {tds:.1f} ppm — เฝ้าระวัง (พืชทั่วไปใบไหม้ ขอบใบแห้ง ชะงักการโต)")
    elif 2000 < tds <= 3000:
        st.error(f"🔴 TDS {tds:.1f} ppm — อันตราย (เฉพาะพืชทนเค็มสูงเท่านั้น พืชทั่วไปตาย)")
    else:
        st.error(f"🚨 TDS {tds:.1f} ppm — วิกฤต! (น้ำเค็มเกินไป ไม่ควรใช้เด็ดขาด)")

    # ORP Analysis
    if 150 <= orp_value <= 400:
        st.success(f"⚡ ORP {orp_value:.1f} mV — เหมาะสม (ปลา/กุ้ง และ พืช)")
    elif orp_value > 400 and orp_value <= 650:
        st.info(f"⚡ ORP {orp_value:.1f} mV — น้ำมีค่าการออกซิไดซ์สูง")
    elif orp_value > 650:
        st.warning(f"⚠️ ORP {orp_value:.1f} mV — สูงมาก (เทียบเท่าน้ำผ่านการฆ่าเชื้อ ไม่เหมาะกับการเกษตรทั่วไป)")
    elif orp_value >= 50 and orp_value < 150:
        st.warning(f"⚠️ ORP {orp_value:.1f} mV — ต่ำ (เริ่มมีลักษณะเทียบเท่าน้ำเสียที่ผ่านการเติมอากาศ)")
    else:
        st.error(f"🔴 ORP {orp_value:.1f} mV — ต่ำมาก (ความเสี่ยงน้ำเน่าเสีย/สภาวะขาดออกซิเจน)")

    st.divider()

    # แสดงตารางเกณฑ์ความเค็มของน้ำ (TDS / EC)
    st.subheader("📌 เกณฑ์ระดับความเค็มของน้ำและกลุ่มพืชที่เหมาะสม")
    salinity_criteria = pd.DataFrame([
        {
            "กลุ่มพืช / สถานะ": "ปลอดภัยสูง (พืชไวต่อเกลือ)", 
            "ค่า TDS (ppm)": "น้อยกว่า 450", 
            "ค่า EC (µS/cm)": "น้อยกว่า 700", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทุกชนิดเติบโตได้ดีที่สุด ไม่ส่งผลกระทบต่อรากและการดูดซึมอาหาร", 
            "ตัวอย่างชนิดพืช": "ทุเรียน, สตรอว์เบอร์รี, กล้วยไม้, ส้ม, มะนาว, ผักสลัด"
        },
        {
            "กลุ่มพืช / สถานะ": "ปลอดภัยปานกลาง (พืชทนเค็มต่ำ)", 
            "ค่า TDS (ppm)": "450 – 1,000", 
            "ค่า EC (µS/cm)": "700 – 1,500", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "ผลผลิตอาจลดลง 10-25% หากดินระบายน้ำไม่ดีจะเกิดคราบเกลือสะสม", 
            "ตัวอย่างชนิดพืช": "ข้าว, ข้าวโพด, อ้อย, พริก, มะเขือเทศ, กะหล่ำปลี"
        },
        {
            "กลุ่มพืช / สถานะ": "เฝ้าระวัง (พืชทนเค็มปานกลาง)", 
            "ค่า TDS (ppm)": "1,000 – 2,000", 
            "ค่า EC (µS/cm)": "1,500 – 3,000", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทั่วไปใบจะเริ่มไหม้ ขอบใบแห้ง ชะงักการโต ต้องใช้กับพืชที่ทนเค็มได้ดีเท่านั้น", 
            "ตัวอย่างชนิดพืช": "ปาล์มน้ำมัน, หม่อน, คะน้า, หน่อไม้ฝรั่ง, บรอกโคลี"
        },
        {
            "กลุ่มพืช / สถานะ": "อันตราย (เฉพาะพืชทนเค็มสูง)", 
            "ค่า TDS (ppm)": "2,000 – 3,000", 
            "ค่า EC (µS/cm)": "3,000 – 4,500", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชส่วนใหญ่ตาย หรือผลผลิตลดลงมากกว่า 50% รากไม่สามารถดูดน้ำได้", 
            "ตัวอย่างชนิดพืช": "มะพร้าว, อินทผลัม, แคนตาลูป, ผักบุ้งทะเล"
        },
        {
            "กลุ่มพืช / สถานะ": "วิกฤต (ไม่ควรใช้เด็ดขาด)", 
            "ค่า TDS (ppm)": "มากกว่า 3,000", 
            "ค่า EC (µS/cm)": "มากกว่า 4,500", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "น้ำเค็มเกินไป ดินจะเสียอย่างรวดเร็ว พืชทั่วไปแห้งตายทันที", 
            "ตัวอย่างชนิดพืช": "ใช้ได้เฉพาะพืชป่าชายเลน หรือพืชทนเค็มจัดบางชนิด"
        }
    ])
    st.table(salinity_criteria)

    # แสดงตารางเกณฑ์ ORP
    st.subheader("📌 เกณฑ์การใช้งานค่า ORP (อ้างอิง)")
    orp_criteria = pd.DataFrame([
        {"ช่วงค่า (mV)": "+150 ถึง +250", "การใช้งาน": "เพาะเลี้ยงสัตว์น้ำ (ปลา/กุ้ง)", "ประโยชน์/ผลลัพธ์": "น้ำสะอาด สมดุล อัตรารอดตายสูง สัตว์น้ำไม่เครียด"},
        {"ช่วงค่า (mV)": "+200 ถึง +400", "การใช้งาน": "ปลูกพืช/ไฮโดรโปนิกส์", "ประโยชน์/ผลลัพธ์": "รากพืชแข็งแรง ดูดซึมปุ๋ยได้ดี ป้องกันรากเน่า"},
        {"ช่วงค่า (mV)": "> +650", "การใช้งาน": "ฆ่าเชื้อระบบน้ำการเกษตร", "ประโยชน์/ผลลัพธ์": "กำจัดเชื้อโรค แบคทีเรีย และสาหร่ายในน้ำ"},
        {"ช่วงค่า (mV)": "+50 ถึง +200", "การใช้งาน": "บำบัดน้ำเสียชุมชน (เติมอากาศ)", "ประโยชน์/ผลลัพธ์": "จุลินทรีย์ย่อยสลายของเสียได้ดี น้ำไม่เน่าเหม็น"},
        {"ช่วงค่า (mV)": "-50 ถึง -200", "การใช้งาน": "บำบัดน้ำเสียชุมชน (ไม่เติมอากาศ)", "ประโยชน์/ผลลัพธ์": "กำจัดสารประกอบไนโตรเจน บำบัดตะกอนเลน"}
    ])
    st.table(orp_criteria)
    
    st.divider()
    
    st.subheader("🌱 แนวทางการใช้น้ำ")
    if tds <= 1000 and 150 <= orp_value <= 400:
        st.success("✅ สามารถนำข้อมูลไปประกอบการวางแผนใช้น้ำเพื่อการเกษตรและประมงได้ตามกลุ่มพืชที่เหมาะสม")
    else:
        st.warning("⚠️ พบค่าความเค็มหรือ ORP ที่ควรเฝ้าระวัง โปรดตรวจสอบเกณฑ์ความเหมาะสมของพืชก่อนนำไปใช้งาน")


# ============================================================
# TAB 3: REPORT / CLUE
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

    uploaded_image = st.file_uploader("🖼️ อัปโหลดรูปภาพหลักฐาน", type=["png", "jpg", "jpeg"])

    if st.button("📤 บันทึกข้อมูลแจ้งเบาะแส", use_container_width=True):

        report_time = datetime.now(TH_TZ).strftime("%d/%m/%Y %H:%M:%S")

        detail_text = report_detail.strip() if report_detail.strip() else "ไม่ได้ระบุ"
        lat_text = report_lat.strip() if report_lat.strip() else "0.0"
        lon_text = report_lon.strip() if report_lon.strip() else "0.0"
        maps_link = f"https://www.google.com/maps?q={lat_text},{lon_text}"

        image_text = "ไม่มีภาพ"
        if uploaded_image is not None:
            with st.spinner("⏳ กำลังอัปโหลดรูปภาพไปยัง Google Drive..."):
                drive_url = upload_image_to_drive(uploaded_image)
                if drive_url:
                    image_text = drive_url
                else:
                    image_text = "อัปโหลดรูปภาพล้มเหลว"

        report_data = {
            "เวลา": report_time,
            "ประเภท": report_type,
            "รายละเอียด": detail_text,
            "พิกัด": f"{lat_text}, {lon_text}"
        }

        st.session_state["last_report"] = report_data

        msg = (
            f"🚨 แจ้งเบาะแส ({report_type})!\n"
            f"📝 รายละเอียดพฤติกรรม: {detail_text}\n"
            f"🌐 พิกัด GPS: {lat_text}, {lon_text}\n"
            f"🗺️ Google Maps: {maps_link}\n"
            f"🖼️ ภาพถ่ายหลักฐาน (Google Drive): {image_text}\n"
            f"⏰ เวลาแจ้ง: {report_time} (ICT)\n"
            f"⚠️\n"
            f"โปรดส่งเจ้าหน้าที่เข้าตรวจสอบพื้นที่ด่วน!"
        )

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
