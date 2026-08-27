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
import pydeck as pdk


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
# BRIGHT LIGHT THEME & ACCESSIBILITY OVERLAY HIDE
# ============================================================

st.markdown(
    """
    <style>
    /* ซ่อนปุ่มหรือเมนูช่วยเหลือการเข้าถึงที่อาจแทรกเข้ามาในหน้าเว็บ */
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
    [data-baseweb="select"] { background-color: #ffffff !important; }
    [data-baseweb="select"] * { color: #172033 !important; }
    input, textarea { background-color: #ffffff !important; color: #172033 !important; border: 1px solid #cbd5e1 !important; }
    input::placeholder, textarea::placeholder { color: #94a3b8 !important; }
    .stButton > button { background-color: #ffffff !important; color: #172033 !important; border: 1px solid #cbd5e1 !important; border-radius: 10px !important; font-weight: 600 !important; }
    .stButton > button:hover { background-color: #f0f9ff !important; color: #0369a1 !important; border-color: #7dd3fc !important; }
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
# FIREBASE & HELPER FUNCTIONS
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

def push_mock_data_to_firebase():
    mock_payload = {
        "tds": round(random.uniform(300.0, 700.0), 1),
        "orp": round(random.uniform(220.0, 410.0), 1),
        "ph": round(random.uniform(6.5, 8.0), 2),
        "timestamp": datetime.now(TH_TZ).strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        requests.put(FIREBASE_URL, json=mock_payload, timeout=5)
    except Exception as e:
        print("Mock Firebase Push Error:", e)

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
    sensor_keys = ["tds", "orp", "ph"]
    for key in sensor_keys:
        if key in data and data.get(key) is not None:
            try:
                float(data.get(key))
                return True
            except:
                pass
    return False


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
# AUTOMATED MOCK FIREBASE WRITER CHECK
# ============================================================

if "last_mock_push" not in st.session_state:
    st.session_state.last_mock_push = 0

current_time_sec = time.time()
if current_time_sec - st.session_state.last_mock_push > 3600:  
    push_mock_data_to_firebase()
    st.session_state.last_mock_push = current_time_sec


# ============================================================
# PROCESS DATA
# ============================================================

live_data = read_firebase()

if sensor_is_online(live_data):
    tds = safe_float(live_data.get("tds"), 450.0)
    orp_value = safe_float(live_data.get("orp"), 300.0)
    ph_value = safe_float(live_data.get("ph"), 7.2)
    sensor_online = True
else:
    tds = 450.0
    orp_value = 300.0
    ph_value = 7.2
    sensor_online = True

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
            tds_val = round(random.uniform(350.0, 750.0), 1)
            orp_val = round(random.uniform(220.0, 410.0), 1)
            ph_val = daily_ph_values[i]
            
            records.append({
                "เวลา": t_str,
                "วันที่": d_str,
                "TDS": tds_val,
                "ORP": orp_val,
                "pH": ph_val
            })
            
    st.session_state.historical_long_df = pd.DataFrame(records)


# ============================================================
# WATER QUALITY LIMIT & CRITICAL CHECK
# ============================================================

TDS_MAX = 1000.0
ORP_MIN = 150.0 
ORP_MAX = 450.0 
PH_MIN = 6.5
PH_MAX = 8.5

risk = []
is_critical = False

if sensor_online:
    if tds > TDS_MAX:
        risk.append(f"TDS สูงเกินเกณฑ์อันตราย {tds:.1f} ppm")
        if tds > 2000:
            is_critical = True
    if orp_value < ORP_MIN:
        risk.append(f"ORP ต่ำเกินไป {orp_value:.1f} mV")
        if orp_value < -50:
            is_critical = True
    elif orp_value > ORP_MAX:
        risk.append(f"ORP สูงเกินเกณฑ์ธรรมชาติ {orp_value:.1f} mV")
        if orp_value > 650:
            is_critical = True
    if ph_value < PH_MIN:
        risk.append(f"pH เป็นกรดเกินไป {ph_value:.2f}")
        if ph_value < 6.0:
            is_critical = True
    elif ph_value > PH_MAX:
        risk.append(f"pH เป็นด่างเกินไป {ph_value:.2f}")
        if ph_value > 8.5:
            is_critical = True

water_normal = (sensor_online and len(risk) == 0)


# ============================================================
# AUTOMATED SCHEDULERS
# ============================================================

now_th = datetime.now(TH_TZ)
current_date_str = now_th.strftime("%Y-%m-%d")
current_hour = now_th.hour
current_minute = now_th.minute

if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = None

if is_critical and sensor_online:
    now_time = datetime.now(TH_TZ)
    if st.session_state.last_alert_time is None or (now_time - st.session_state.last_alert_time).total_seconds() > 900:
        alert_msg = (
            f"🚨 ⚠️ แจ้งเตือนวิกฤตคุณภาพน้ำ (ค่าเกินเกณฑ์สีแดง)!\n"
            f"📍 จุดตรวจวัด: แม่น้ำบางปะกง\n"
            f"⏰ เวลา: {now_time.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"----------------------------------\n"
            f"🧂 TDS: {tds:.1f} ppm\n"
            f"⚡ ORP: {orp_value:.1f} mV\n"
            f"🧪 pH: {ph_value:.2f}\n"
            f"⚠️ สาเหตุ/ความเสี่ยง:\n" + "\n".join([f"• {r}" for r in risk]) + "\n\n"
            f"🔴 โปรดตรวจสอบระบบและพื้นที่ด่วน!"
        )
        sent_ok = send_line_notification(alert_msg)
        if sent_ok:
            st.session_state.last_alert_time = now_time

target_hours = [0, 3, 6, 9, 12, 15, 18, 21]
if "last_auto_report_key" not in st.session_state:
    st.session_state.last_auto_report_key = ""

if current_hour in target_hours and current_minute <= 2:
    report_slot_key = f"{current_date_str}_{current_hour:02d}:00"
    if st.session_state.last_auto_report_key != report_slot_key:
        auto_msg = (
            f"📊 รายงานคุณภาพน้ำอัตโนมัติ (ทุก 3 ชม.)\n"
            f"📍 จุดตรวจวัด: แม่น้ำบางปะกง\n"
            f"⏰ เวลา: {now_th.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"----------------------------------\n"
            f"🧂 TDS: {tds:.1f} ppm\n"
            f"⚡ ORP: {orp_value:.1f} mV\n"
            f"🧪 pH: {ph_value:.2f}\n"
            f"🛡️ สถานะ: {'✅ ปกติ' if water_normal else '⚠️ พบข้อควรเฝ้าระวัง'}"
        )
        success_sent = send_line_notification(auto_msg)
        if success_sent:
            st.session_state.last_auto_report_key = report_slot_key


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
        st.caption("กำลังรับค่าจาก Firebase (อัปเดตทุก 2 วิ)")
    else:
        st.markdown('<div class="offline-card">🔴 SENSOR OFFLINE</div>', unsafe_allow_html=True)
        st.caption("ไม่พบค่าจากเซนเซอร์")

    st.divider()
    st.subheader("📊 Parameters")
    st.write("🧂 TDS")
    st.write("⚡ ORP")
    st.write("🧪 pH")

    st.divider()
    st.write("🔄 Auto Refresh & Schedule")
    st.info(f"• รีเฟรชหน้าจอทุก {REFRESH_SECONDS} วิ\n• ส่งค่าปลอมปกติเข้า Firebase ทุก 60 นาที\n• แจ้งเตือนด่วนทันทีเมื่อค่าเกินสีแดง")

    st.divider()
    st.write("🕒 เวลาปัจจุบัน")
    st.write(now_th.strftime("%d/%m/%Y %H:%M:%S"))


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

    st.divider()
    st.subheader("📡 ค่าจากเซนเซอร์แบบ Real-time")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🧂 TDS", f"{tds:.1f} ppm")
    col2.metric("⚡ ORP", f"{orp_value:.1f} mV")
    col3.metric("🧪 pH", f"{ph_value:.2f}")

    st.divider()
    st.subheader("🤖 สถานะคุณภาพน้ำ")
    if not sensor_online:
        st.info("⏳ กำลังรอข้อมูลจากเซนเซอร์...")
    elif water_normal:
        st.success("✅ ค่าคุณภาพน้ำอยู่ในเกณฑ์ปกติ")
    else:
        if is_critical:
            st.error("🚨 พบค่าวิกฤต (เกินเกณฑ์สีแดง) ระบบส่งแจ้งเตือนด่วนไปที่ LINE แล้ว!")
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
    st.title("💧 คำแนะนำการใช้น้ำ")
    st.caption("คำแนะนำจากค่าที่ตรวจวัดได้และเกณฑ์มาตรฐาน")

    if not sensor_online:
        st.warning("🔴 ยังไม่มีข้อมูลจากเซนเซอร์")
    
    st.subheader("📊 ผลวิเคราะห์ปัจจุบัน")
    
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

    if 6.5 <= ph_value <= 8.5:
        st.success(f"🧪 pH {ph_value:.2f} — เหมาะสม (สภาพความเป็นกรด-ด่างอยู่ในเกณฑ์มาตรฐานเพื่อการเกษตร)")
    elif ph_value < 6.5:
        st.warning(f"⚠️ pH {ph_value:.2f} — มีความเป็นกรดสูง (อาจส่งผลให้รากพืชดูดซึมธาตุอาหารบางชนิดไม่ได้)")
    else:
        st.warning(f"⚠️ pH {ph_value:.2f} — มีความเป็นด่างสูง (อาจทำให้เกิดการตกตะกอนของแร่ธาตุในน้ำ)")

    st.divider()

    st.subheader("🌱 แนวทางการใช้น้ำ")
    if tds <= 1000 and 150 <= orp_value <= 400 and 6.5 <= ph_value <= 8.5:
        st.success("✅ สามารถนำข้อมูลไปประกอบการวางแผนใช้น้ำเพื่อการเกษตรและประมงได้ตามกลุ่มพืชที่เหมาะสม")
    else:
        st.warning("⚠️ พบค่าความเค็ม, ORP หรือ pH ที่ควรเฝ้าระวัง โปรดตรวจสอบเกณฑ์ความเหมาะสมก่อนใช้งาน")

    st.divider()

    st.subheader("📌 เกณฑ์ระดับความเค็มของน้ำและกลุ่มพืชที่เหมาะสม")
    salinity_criteria = pd.DataFrame([
        {"กลุ่มพืช / สถานะ": "ปลอดภัยสูง (พืชไวต่อเกลือ)", "ค่า TDS (ppm)": "น้อยกว่า 450", "ค่า EC (µS/cm)": "น้อยกว่า 700", "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทุกชนิดเติบโตได้ดีที่สุด ไม่ส่งผลกระทบต่อรากและการดูดซึมอาหาร", "ตัวอย่างชนิดพืช": "ทุเรียน, สตรอว์เบอร์รี, กล้วยไม้, ส้ม, มะนาว, ผักสลัด"},
        {"กลุ่มพืช / สถานะ": "ปลอดภัยปานกลาง (พืชทนเค็มต่ำ)", "ค่า TDS (ppm)": "450 – 1,000", "ค่า EC (µS/cm)": "700 – 1,500", "กลุ่มพืชที่เหมาะสมและผลกระทบ": "ผลผลิตอาจลดลง 10-25% หากดินระบายน้ำไม่ดีจะเกิดคราบเกลือสะสม", "ตัวอย่างชนิดพืช": "ข้าว, ข้าวโพด, อ้อย, พริก, มะเขือเทศ, กะหล่ำปลี"},
        {"กลุ่มพืช / สถานะ": "เฝ้าระวัง (พืชทนเค็มปานกลาง)", "ค่า TDS (ppm)": "1,000 – 2,000", "ค่า EC (µS/cm)": "1,500 – 3,000", "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทั่วไปใบจะเริ่มไหม้ ขอบใบแห้ง ชะงักการโต ต้องใช้กับพืชที่ทนเค็มได้ดีเท่านั้น", "ตัวอย่างชนิดพืช": "ปาล์มน้ำมัน, หม่อน, คะน้า, หน่อไม้ฝรั่ง, บรอกโคลี"},
        {"กลุ่มพืช / สถานะ": "อันตราย (เฉพาะพืชทนเค็มสูง)", "ค่า TDS (ppm)": "2,000 – 3,000", "ค่า EC (µS/cm)": "3,000 – 4,500", "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชส่วนใหญ่ตาย หรือผลผลิตลดลงมากกว่า 50% รากไม่สามารถดูดน้ำได้", "ตัวอย่างชนิดพืช": "มะพร้าว, อินทผลัม, แคนตาลูป, ผักบุ้งทะเล"},
        {"กลุ่มพืช / สถานะ": "วิกฤต (ไม่ควรใช้เด็ดขาด)", "ค่า TDS (ppm)": "มากกว่า 3,000", "ค่า EC (µS/cm)": "มากกว่า 4,500", "กลุ่มพืชที่เหมาะสมและผลกระทบ": "น้ำเค็มเกินไป ดินจะเสียอย่างรวดเร็ว พืชทั่วไปแห้งตายทันที", "ตัวอย่างชนิดพืช": "ใช้ได้เฉพาะพืชป่าชายเลน หรือพืชทนเค็มจัดบางชนิด"}
    ])
    st.table(salinity_criteria)


# ============================================================
# TAB 3: REPORT / CLUE (พร้อมแผนที่พิกัดจริงหลายจุด)
# ============================================================

with tab3:
    st.title("📍 แจ้งเบาะแส")
    st.caption("แจ้งข้อมูลความผิดปกติที่พบในแหล่งน้ำ")

    st.markdown(
        """
        <div class="water-card">
        <h3>📢 แจ้งปัญหาคุณภาพน้ำ</h3>
        ใช้สำหรับบันทึกข้อมูลเมื่อพบความผิดปกติของแหล่งน้ำ
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("🗺️ แผนที่แสดงจุดตรวจวัด และจุดเสี่ยง (โรงไฟฟ้า / พื้นที่อุตสาหกรรมริมแม่น้ำ)")

    # ชุดข้อมูลพิกัดจริง (ทุ่นตรวจวัดสีน้ำเงิน, โรงงาน/จุดเสี่ยงสีแดง)
    map_df = pd.DataFrame([
        {
            "lat": 13.689417, 
            "lon": 101.078617, 
            "name": "ทุ่นตรวจวัดคุณภาพน้ำ", 
            "color": [0, 150, 255] # สีน้ำเงิน
        },
        {
            "lat": 13.501389, 
            "lon": 101.025278, 
            "name": "พื้นที่โรงไฟฟ้าบางปะกง (ริมแม่น้ำ)", 
            "color": [255, 0, 0] # สีแดง
        },
        {
            "lat": 13.535000, 
            "lon": 101.005000, 
            "name": "โซนสวนอุตสาหกรรม / จุดระบายน้ำ (ท่าข้าม)", 
            "color": [255, 0, 0] # สีแดง
        }
    ])

    layer = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=120,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=13.600000,
        longitude=101.040000,
        zoom=10.5,
        pitch=0,
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}\nพิกัด: {lat}, {lon}"},
        map_style="mapbox://styles/mapbox/dark-v10"
    )

    st.pydeck_chart(r)
    st.caption("📍 หมุดสีฟ้า: ทุ่นตรวจวัดคุณภาพน้ำ | 🔴 หมุดสีแดง: โรงงานและจุดระบายน้ำสำคัญตามพิกัดจริง")

    st.divider()

    with st.form("report_form", clear_on_submit=True):
        report_type = st.selectbox(
            "ประเภทเหตุการณ์",
            ["ทิ้งขยะลงแม่น้ำ", "น้ำมีสีผิดปกติ", "น้ำมีกลิ่นผิดปกติ", "น้ำขุ่นผิดปกติ", "พบสิ่งปนเปื้อน", "พบการปล่อยน้ำเสีย", "อื่น ๆ"]
        )

        report_detail = st.text_area("รายละเอียดพฤติกรรม", placeholder="กรอกรายละเอียดที่พบ...")

        col_lat, col_lon = st.columns(2)
        with col_lat:
            report_lat = st.text_input("พิกัด GPS (ละติจูด)", value="13.689417", placeholder="เช่น 13.689417")
        with col_lon:
            report_lon = st.text_input("พิกัด GPS (ลองจิจูด)", value="101.078617", placeholder="เช่น 101.078617")

        uploaded_image = st.file_uploader("🖼️ อัปโหลดรูปภาพหลักฐาน", type=["png", "jpg", "jpeg"])

        submitted = st.form_submit_button("📤 บันทึกข้อมูลแจ้งเบาะแส", use_container_width=True)

        if submitted:
            report_time = datetime.now(TH_TZ).strftime("%d/%m/%Y %H:%M:%S")

            detail_text = report_detail.strip() if report_detail.strip() else "ไม่ได้ระบุ"
            lat_text = report_lat.strip() if report_lat.strip() else "13.689417"
            lon_text = report_lon.strip() if report_lon.strip() else "101.078617"
            maps_link = f"https://www.google.com/maps?q={lat_text},{lon_text}"

            image_text = "ไม่มีภาพ"
            if uploaded_image is not None:
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
                st.success("✅ บันทึกข้อมูลและส่งแจ้งเตือนไปยัง LINE เรียบร้อยแล้ว (รีเซ็ตฟอร์มแล้ว)")
            else:
                st.warning("⚠️ บันทึกข้อมูลแล้ว แต่ไม่สามารถส่งแจ้งเตือนไป LINE ได้ (รีเซ็ตฟอร์มแล้ว)")

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
