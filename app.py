import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz
import pandas as pd


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

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background-color: #f8fafc !important;
        color: #172033 !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important;
    }

    .main {
        background-color: #f8fafc !important;
    }


    /* ========================================================
       HEADER
       ======================================================== */

    [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }

    [data-testid="stSidebar"] * {
        color: #172033 !important;
    }


    /* ========================================================
       HEADINGS
       ======================================================== */

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: #172033 !important;
        font-weight: 700 !important;
    }


    /* ========================================================
       TEXT
       ======================================================== */

    .stMarkdown,
    .stText,
    p,
    label {
        color: #334155 !important;
    }


    /* ========================================================
       CAPTION
       ======================================================== */

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {
        color: #64748b !important;
    }


    /* ========================================================
       METRIC CARDS
       ======================================================== */

    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        padding: 18px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {
        color: #64748b !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        color: #172033 !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] * {
        color: #475569 !important;
    }


    /* ========================================================
       INPUT
       ======================================================== */

    input,
    textarea {
        background-color: #ffffff !important;
        color: #172033 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #94a3b8 !important;
    }


    /* ========================================================
       SELECTBOX
       ======================================================== */

    [data-baseweb="select"] {
        background-color: #ffffff !important;
    }

    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
    }

    [data-baseweb="select"] * {
        color: #172033 !important;
    }


    /* ========================================================
       BUTTON
       ======================================================== */

    .stButton > button {
        background-color: #ffffff !important;
        color: #172033 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        min-height: 42px;
    }

    .stButton > button:hover {
        background-color: #f0f9ff !important;
        color: #0369a1 !important;
        border-color: #7dd3fc !important;
    }


    /* ========================================================
       TABS
       ======================================================== */

    button[data-baseweb="tab"] {
        color: #64748b !important;
        font-weight: 600 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0284c7 !important;
    }


    /* ========================================================
       EXPANDER
       ======================================================== */

    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
    }


    /* ========================================================
       FILE UPLOADER
       ======================================================== */

    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1px dashed #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }


    /* ========================================================
       ALERT
       ======================================================== */

    [data-testid="stAlert"] {
        border-radius: 12px !important;
    }


    /* ========================================================
       DATAFRAME
       ======================================================== */

    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
    }


    /* ========================================================
       MAP
       ======================================================== */

    [data-testid="stDeckGlJsonChart"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid #e2e8f0 !important;
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    hr {
        border-color: #e2e8f0 !important;
    }


    /* ========================================================
       SCROLLBAR
       ======================================================== */

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f8fafc;
    }

    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TIMEZONE
# ============================================================

TH_TZ = pytz.timezone("Asia/Bangkok")


# ============================================================
# FIREBASE
# ============================================================

FIREBASE_WEB_API_KEY = (
    "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"
)

FIREBASE_DB_URL = (
    "https://cwis-c2ea8-default-rtdb."
    "asia-southeast1.firebasedatabase.app"
)

FIREBASE_SENSOR_PATH = (
    "/devices/uno-r4/status"
)

SENSOR_OFFLINE_TIMEOUT = 30


# ============================================================
# FIREBASE AUTH
# ============================================================

@st.cache_data(ttl=3000)
def get_firebase_token():

    auth_url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    )

    try:

        response = requests.post(
            auth_url,
            json={
                "returnSecureToken": True
            },
            timeout=5
        )

        if response.status_code == 200:

            return response.json().get(
                "idToken"
            )

    except Exception as e:

        print(
            "Firebase Auth Error:",
            e
        )

    return None


# ============================================================
# READ FIREBASE
# ============================================================

def read_sensor_data(id_token):

    if not id_token:
        return None

    url = (
        f"{FIREBASE_DB_URL}"
        f"{FIREBASE_SENSOR_PATH}.json"
        f"?auth={id_token}"
    )

    try:

        response = requests.get(
            url,
            timeout=5
        )

        if response.status_code == 200:

            return response.json()

    except Exception as e:

        print(
            "Firebase Read Error:",
            e
        )

    return None


# ============================================================
# WATER QUALITY
# ============================================================

def calculate_water_quality(
    tds,
    do_value,
    turbidity
):

    reasons = []

    if tds > 1000:

        reasons.append(
            f"TDS {tds:.1f} ppm สูง"
        )

    if do_value < 4:

        reasons.append(
            f"DO {do_value:.2f} mg/L ต่ำ"
        )

    if turbidity > 100:

        reasons.append(
            f"ความขุ่น {turbidity:.1f} NTU สูง"
        )

    if reasons:

        return False, reasons

    return True, []


# ============================================================
# MAP
# ============================================================

# แสดงเพียง 1 จุด
BANG_PAKONG_SENSOR = pd.DataFrame(
    [
        {
            "lat": 13.6900,
            "lon": 101.1700
        }
    ]
)


# ============================================================
# HISTORY
# ============================================================

if "water_history" not in st.session_state:

    st.session_state.water_history = []


def add_history(
    tds,
    turbidity,
    do_value
):

    now = datetime.now(
        TH_TZ
    ).strftime(
        "%H:%M:%S"
    )

    st.session_state.water_history.append(
        {
            "เวลา": now,
            "TDS": float(tds),
            "Turbidity": float(turbidity),
            "DO": float(do_value)
        }
    )

    st.session_state.water_history = (
        st.session_state.water_history[-30:]
    )


# ============================================================
# GET DATA
# ============================================================

id_token = get_firebase_token()

live_data = read_sensor_data(
    id_token
)


# ============================================================
# DEFAULT SENSOR VALUES
# ============================================================

tds = 0.0
turbidity = 0.0
do_value = 0.0

sensor_connected = False
last_update = None
seconds_since_update = None


# ============================================================
# PROCESS FIREBASE DATA
# ============================================================

if isinstance(
    live_data,
    dict
):

    try:

        if "tds" in live_data:

            tds = float(
                live_data["tds"]
            )

        if "turbidity" in live_data:

            turbidity = float(
                live_data["turbidity"]
            )

        if "do" in live_data:

            do_value = float(
                live_data["do"]
            )

        # ----------------------------------------------------
        # UPDATED AT
        # ----------------------------------------------------

        if "updatedAt" in live_data:

            timestamp = float(
                live_data["updatedAt"]
            )

            if timestamp > 100000000000:

                timestamp /= 1000

            seconds_since_update = (
                time.time()
                - timestamp
            )

            last_update = (
                datetime
                .fromtimestamp(
                    timestamp,
                    TH_TZ
                )
                .strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
            )

            sensor_connected = (
                0
                <= seconds_since_update
                <= SENSOR_OFFLINE_TIMEOUT
            )

    except Exception as e:

        print(
            "Sensor Processing Error:",
            e
        )


# ============================================================
# ADD HISTORY
# ============================================================

if live_data:

    add_history(
        tds,
        turbidity,
        do_value
    )


# ============================================================
# WATER QUALITY
# ============================================================

water_safe, risk_reasons = (
    calculate_water_quality(
        tds,
        do_value,
        turbidity
    )
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "💧 Water Monitor"
    )

    st.caption(
        "EEC Community Water"
    )

    st.divider()

    if id_token:

        st.success(
            "🟢 Firebase เชื่อมต่อแล้ว"
        )

    else:

        st.error(
            "🔴 Firebase Authentication ล้มเหลว"
        )

    st.divider()

    st.subheader(
        "📡 สถานะระบบ"
    )

    if sensor_connected:

        st.success(
            "🟢 SENSOR ONLINE"
        )

    else:

        st.error(
            "🔴 SENSOR OFFLINE"
        )

    st.divider()

    st.info(
        "🕒 เวลาไทย\n\n"
        + datetime.now(
            TH_TZ
        ).strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )


# ============================================================
# TABS
# ============================================================

tab_dashboard, tab_advice, tab_report = st.tabs(
    [
        "📊 ภาพรวมน้ำ",
        "💧 คำแนะนำ",
        "📍 แจ้งเบาะแส"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:

    st.caption(
        "EEC · AGRI-WATER INTELLIGENCE"
    )

    st.title(
        "💧 ระบบตรวจสอบคุณภาพน้ำ"
    )

    st.write(
        "📍 จุดตรวจวัด : แม่น้ำบางปะกง"
    )


    # ========================================================
    # SENSOR STATUS
    # ========================================================

    if sensor_connected:

        age = int(
            max(
                0,
                seconds_since_update
            )
        )

        st.success(
            f"🟢 SENSOR ONLINE · "
            f"ข้อมูลล่าสุด {age} วินาทีที่แล้ว"
        )

    else:

        st.error(
            "🔴 SENSOR OFFLINE · "
            "ไม่มีข้อมูลใหม่เกิน 30 วินาที"
        )


    if last_update:

        st.caption(
            f"อัปเดตล่าสุด : {last_update}"
        )


    st.divider()


    # ========================================================
    # SENSOR VALUES
    # ========================================================

    st.subheader(
        "📡 ค่าคุณภาพน้ำปัจจุบัน"
    )

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "🧂 TDS",
            f"{tds:.1f} ppm"
        )


    with col2:

        st.metric(
            "🌫️ Turbidity",
            f"{turbidity:.1f} NTU"
        )


    with col3:

        st.metric(
            "🫧 DO",
            f"{do_value:.2f} mg/L"
        )


    st.divider()


    # ========================================================
    # OTHER VALUES
    # ========================================================

    st.subheader(
        "📋 ข้อมูลเพิ่มเติม"
    )

    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "⚗️ pH",
            "--"
        )

        st.caption(
            "ยังไม่มีข้อมูล pH จาก ESP32"
        )


    with col2:

        st.metric(
            "🌡️ Temperature",
            "--"
        )

        st.caption(
            "ยังไม่มีข้อมูล Temperature จาก ESP32"
        )


    st.divider()


    # ========================================================
    # QUALITY
    # ========================================================

    st.subheader(
        "🤖 ผลประเมินคุณภาพน้ำ"
    )


    if water_safe:

        st.success(
            "✅ คุณภาพน้ำอยู่ในเกณฑ์ปกติ"
        )

    else:

        st.warning(
            "⚠️ คุณภาพน้ำมีค่าที่ควรเฝ้าระวัง"
        )

        for reason in risk_reasons:

            st.write(
                f"• {reason}"
            )


    st.divider()


    # ========================================================
    # MAP
    # ========================================================

    st.subheader(
        "🗺️ จุดตรวจวัดแม่น้ำบางปะกง"
    )

    st.caption(
        "แสดงเพียง 1 จุดตรวจวัด"
    )

    st.map(
        BANG_PAKONG_SENSOR,
        latitude="lat",
        longitude="lon",
        size=300,
        zoom=10
    )


    st.divider()


    # ========================================================
    # GRAPH
    # ========================================================

    st.subheader(
        "📈 กราฟคุณภาพน้ำ"
    )

    if st.session_state.water_history:

        chart_df = pd.DataFrame(
            st.session_state.water_history
        )

        chart_df = chart_df.set_index(
            "เวลา"
        )

        selected_chart = st.selectbox(
            "เลือกค่าที่ต้องการดู",
            [
                "TDS",
                "Turbidity",
                "DO"
            ]
        )

        st.line_chart(
            chart_df[
                [selected_chart]
            ],
            use_container_width=True
        )

    else:

        st.info(
            "กำลังรอข้อมูลสำหรับกราฟ"
        )


    st.divider()


    # ========================================================
    # FIREBASE DEBUG
    # ========================================================

    with st.expander(
        "🔧 Firebase Debug"
    ):

        st.write(
            "Firebase Database"
        )

        st.code(
            FIREBASE_DB_URL
        )

        st.write(
            "Firebase Path"
        )

        st.code(
            FIREBASE_SENSOR_PATH
        )

        st.write(
            "ข้อมูลจาก Firebase"
        )

        if live_data:

            st.json(
                live_data
            )

        else:

            st.warning(
                "ยังไม่มีข้อมูล"
            )


    st.divider()


    if st.button(
        "🔄 รีเฟรชข้อมูล",
        use_container_width=True
    ):

        st.rerun()


# ============================================================
# WATER ADVICE
# ============================================================

with tab_advice:

    st.title(
        "💧 คำแนะนำการใช้น้ำ"
    )

    if water_safe:

        st.success(
            "✅ คุณภาพน้ำอยู่ในเกณฑ์ปกติ"
        )

        st.write(
            "ข้อมูลคุณภาพน้ำอยู่ในช่วงที่ระบบ "
            "กำหนดให้เป็นปกติ"
        )

    else:

        st.warning(
            "⚠️ ควรเฝ้าระวังคุณภาพน้ำ"
        )

        st.write(
            "พบค่าบางรายการสูงหรือต่ำกว่า "
            "เกณฑ์ที่ระบบกำหนด"
        )

        for reason in risk_reasons:

            st.write(
                f"• {reason}"
            )


    st.divider()


    st.subheader(
        "📋 เกณฑ์เบื้องต้นของระบบ"
    )

    criteria = pd.DataFrame(
        {
            "Parameter": [
                "TDS",
                "DO",
                "Turbidity"
            ],
            "เกณฑ์": [
                "< 1,000 ppm",
                "> 4.0 mg/L",
                "< 100 NTU"
            ]
        }
    )

    st.dataframe(
        criteria,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# REPORT
# ============================================================

with tab_report:

    st.title(
        "📍 แจ้งเบาะแสแหล่งน้ำ"
    )

    st.info(
        "หากพบแหล่งน้ำผิดปกติ "
        "สามารถกรอกรายละเอียดเพื่อแจ้งข้อมูลได้"
    )

    report_detail = st.text_area(
        "รายละเอียด",
        placeholder=(
            "เช่น พบคราบน้ำมัน "
            "น้ำมีสีผิดปกติ มีกลิ่น "
            "หรือพบการปล่อยน้ำเสีย"
        ),
        height=150
    )


    if st.button(
        "📤 ส่งข้อมูลแจ้งเบาะแส",
        use_container_width=True
    ):

        if not report_detail.strip():

            st.warning(
                "⚠️ กรุณากรอกรายละเอียด"
            )

        else:

            message = (
                "📍 แจ้งเบาะแสแหล่งน้ำ\n\n"
                "รายละเอียด:\n"
                f"{report_detail}\n\n"
                "เวลา: "
                f"{datetime.now(TH_TZ).strftime('%d/%m/%Y %H:%M:%S')}"
            )

            st.success(
                "✅ เตรียมข้อมูลแจ้งเบาะแสแล้ว"
            )

            st.code(
                message
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "💧 EEC Community Water Intelligence System"
)
