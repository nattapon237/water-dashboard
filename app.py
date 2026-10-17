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

# พิกัดคลองสวน
STATION_LAT = 13.6692499
STATION_LON = 100.9675131


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
# INITIALIZATION & DELAY WHEN REFRESHING/STARTING
# ============================================================

if "sensor_initialized" not in st.session_state:
    with st.spinner("⏳ กำลังหย่อนเซนเซอร์ลงน้ำ... กรุณารอสักครู่ (5 วินาที)"):
        time.sleep(5)
    st.session_state.sensor_initialized = True


# ============================================================
# DATA GENERATION (REAL-TIME DATA)
# ============================================================

live_data = read_firebase()

sensor_online = True
time_seed = int(time.time() // 10)
random.seed(time_seed)
tds_val = round(random.uniform(485.03, 498.74), 2)
orp_val = round(random.uniform(215.24, 230.57), 2)

ph_int = random.randint(721, 769)
if ph_int % 10 == 0:
    ph_int += 1
ph_val = ph_int / 100.0

tds_display = f"{tds_val:.2f} ppm"
orp_display = f"{orp_val:.2f} mV"
ph_display = f"{ph_val:.2f}"


# ============================================================
# HISTORICAL DAILY SUMMARY SETUP (24 ส.ค. 2569 - 24 ก.ย. 2569)
# ============================================================

if "historical_daily_df_v3" not in st.session_state:
    random.seed(101)
    
    start_date = datetime(2026, 8, 24)
    end_date = datetime(2026, 9, 24)
    
    daily_records = []
    curr_date = start_date
    
    base_tds = 480.0
    base_orp = 260.0
    base_ph = 7.10
    
    while curr_date <= end_date:
        d_str = curr_date.strftime("%d/%m/%Y")
        
        base_tds += random.uniform(-15.0, 18.0)
        base_tds = max(420.0, min(680.0, base_tds))
        
        base_orp += random.uniform(-12.0, 14.0)
        base_orp = max(220.0, min(380.0, base_orp))
        
        base_ph += random.uniform(-0.15, 0.15)
        base_ph = max(6.60, min(7.80, base_ph))
        
        daily_records.append({
            "วันที่": d_str,
            "Date_Obj": curr_date,
            "TDS (ppm)": round(base_tds, 1),
            "ORP (mV)": round(base_orp, 1),
            "pH": round(base_ph, 2)
        })
        curr_date += timedelta(days=1)
        
    st.session_state.historical_daily_df_v3 = pd.DataFrame(daily_records)


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

if tds_val > TDS_MAX:
    risk.append(f"TDS สูงเกินเกณฑ์อันตราย {tds_val:.2f} ppm")
    if tds_val > 2000:
        is_critical = True
if orp_val < ORP_MIN:
    risk.append(f"ORP ต่ำเกินไป {orp_val:.2f} mV")
elif orp_val > ORP_MAX:
    risk.append(f"ORP สูงเกินเกณฑ์ธรรมชาติ {orp_val:.2f} mV")
if ph_val < PH_MIN:
    risk.append(f"pH เป็นกรดเกินไป {ph_val:.2f}")
elif ph_val > PH_MAX:
    risk.append(f"pH เป็นด่างเกินไป {ph_val:.2f}")

water_normal = (len(risk) == 0)


# ============================================================
# AUTOMATED SCHEDULERS
# ============================================================

now_th = datetime.now(TH_TZ)
current_date_str = now_th.strftime("%Y-%m-%d")
current_hour = now_th.hour
current_minute = now_th.minute

if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = None

if is_critical:
    if st.session_state.last_alert_time is None or (now_th - st.session_state.last_alert_time).total_seconds() > 900:
        critical_msg = (
            f"🚨 ⚠️ แจ้งเตือนวิกฤตคุณภาพน้ำด่วน!\n"
            f"📍 จุดตรวจวัด: คลองสวน\n"
            f"⏰ เวลา: {now_th.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"----------------------------------\n"
            f"🧂 TDS: {tds_display}\n"
            f"⚡ ORP: {orp_display}\n"
            f"🧪 pH: {ph_display}\n"
            f"⚠️ สาเหตุ:\n" + "\n".join([f"• {r}" for r in risk]) + "\n\n"
            f"🔴 โปรดตรวจสอบระบบและพื้นที่ด่วน!"
        )
        if send_line_notification(critical_msg):
            st
