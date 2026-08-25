import streamlit as st
import requests
import pandas as pd
import time
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

    .stApp {
        background-color: #f8fafc !important;
        color: #172033 !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important;
    }

    [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }

    [data-testid="stSidebar"] * {
        color: #172033 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #172033 !important;
        font-weight: 700 !important;
    }

    p, label, .stMarkdown {
        color: #334155 !important;
    }

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {
        color: #64748b !important;
    }

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

    [data-baseweb="select"] {
        background-color: #ffffff !important;
    }

    [data-baseweb="select"] * {
        color: #172033 !important;
    }

    .stButton > button {
        background-color: #ffffff !important;
        color: #172033 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    .stButton > button:hover {
        background-color: #f0f9ff !important;
        color: #0369a1 !important;
        border-color: #7dd3fc !important;
    }

    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
    }

    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
    }

    [data-testid="stDeckGlJsonChart"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid #e2e8f0 !important;
    }

    hr {
        border-color: #e2e8f0 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CONFIG
# ============================================================

TH_TZ = pytz.timezone("Asia/Bangkok")

FIREBASE_DB_URL = (
    "https://cwis-c2ea8-default-rtdb."
    "asia-southeast1.firebasedatabase.app"
)

FIREBASE_SENSOR_PATH = "/devices/uno-r4/status"

FIREBASE_URL = (
    FIREBASE_DB_URL
    + FIREBASE_SENSOR_PATH
    + ".json"
)


# ============================================================
# AUTO REFRESH
# ============================================================

REFRESH_SECONDS = 2


# ============================================================
# FIREBASE READ
# ============================================================

def read_firebase():

    try:

        response = requests.get(
            FIREBASE_URL,
            timeout=5
        )

        if response.status_code == 200:

            return response.json()

        else:

            return None

    except Exception as e:

        print("Firebase Error:", e)

        return None


# ============================================================
# CHECK SENSOR
# ============================================================

def sensor_is_online(data):

    if not isinstance(data, dict):
        return False

    keys = [
        "tds",
        "turbidity",
        "do"
    ]

    for key in keys:

        if key in data:

            value = data[key]

            if value is not None:

                try:

                    float(value)

                    return True

                except:

                    pass

    return False


# ============================================================
# READ VALUES
# ============================================================

live_data = read_firebase()


tds = 0.0
turbidity = 0.0
do_value = 0.0


if isinstance(live_data, dict):

    try:

        if live_data.get("tds") is not None:

            tds = float(
                live_data["tds"]
            )

    except:

        tds = 0.0


    try:

        if live_data.get("turbidity") is not None:

            turbidity = float(
                live_data["turbidity"]
            )

    except:

        turbidity = 0.0


    try:

        if live_data.get("do") is not None:

            do_value = float(
                live_data["do"]
            )

    except:

        do_value = 0.0


# ============================================================
# SENSOR STATUS
# ============================================================

sensor_online = sensor_is_online(
    live_data
)


# ============================================================
# HISTORY
# ============================================================

if "history" not in st.session_state:

    st.session_state.history = []


if sensor_online:

    now = datetime.now(
        TH_TZ
    )

    st.session_state.history.append(
        {
            "เวลา": now.strftime("%H:%M:%S"),
            "TDS": tds,
            "Turbidity": turbidity,
            "DO": do_value
        }
    )

    # เก็บย้อนหลัง 60 ค่า
    st.session_state.history = (
        st.session_state.history[-60:]
    )


# ============================================================
# WATER QUALITY
# ============================================================

risk = []

if tds > 1000:

    risk.append(
        f"TDS สูง {tds:.1f} ppm"
    )

if turbidity > 100:

    risk.append(
        f"ความขุ่นสูง {turbidity:.1f} NTU"
    )

if do_value < 4:

    risk.append(
        f"DO ต่ำ {do_value:.2f} mg/L"
    )


water_normal = (
    sensor_online
    and
    len(risk) == 0
)


# ============================================================
# MAP
# ============================================================

bangpakong_map = pd.DataFrame(
    {
        "lat": [13.6900],
        "lon": [101.1700]
    }
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

    st.subheader(
        "📡 Sensor Status"
    )

    if sensor_online:

        st.success(
            "🟢 SENSOR ONLINE"
        )

        st.caption(
            "กำลังรับค่าจาก Firebase"
        )

    else:

        st.error(
            "🔴 SENSOR OFFLINE"
        )

        st.caption(
            "ไม่พบค่าจาก Firebase"
        )

    st.divider()

    st.write(
        "🔄 Auto Refresh"
    )

    st.info(
        "อัปเดตทุก 2 วินาที"
    )

    st.divider()

    st.write(
        "🕒 เวลา"
    )

    st.write(
        datetime.now(
            TH_TZ
        ).strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )


# ============================================================
# MAIN
# ============================================================

st.caption(
    "EEC · AGRI-WATER INTELLIGENCE"
)

st.title(
    "💧 ระบบตรวจสอบคุณภาพน้ำ"
)

st.write(
    "📍 จุดตรวจวัด : แม่น้ำบางปะกง"
)


# ============================================================
# ONLINE STATUS
# ============================================================

if sensor_online:

    st.success(
        "🟢 SENSOR ONLINE · รับค่าจากเซนเซอร์แล้ว"
    )

else:

    st.error(
        "🔴 SENSOR OFFLINE · ไม่พบข้อมูลจากเซนเซอร์"
    )


st.divider()


# ============================================================
# SENSOR VALUES
# ============================================================

st.subheader(
    "📡 ค่าจากเซนเซอร์แบบ Real-time"
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


# ============================================================
# QUALITY STATUS
# ============================================================

st.subheader(
    "🤖 สถานะคุณภาพน้ำ"
)


if not sensor_online:

    st.info(
        "⏳ กำลังรอข้อมูลจากเซนเซอร์"
    )

elif water_normal:

    st.success(
        "✅ ค่าคุณภาพน้ำอยู่ในเกณฑ์ปกติ"
    )

else:

    st.warning(
        "⚠️ พบค่าที่ควรเฝ้าระวัง"
    )

    for item in risk:

        st.write(
            "• " + item
        )


st.divider()


# ============================================================
# MAP
# ============================================================

st.subheader(
    "🗺️ จุดตรวจวัดแม่น้ำบางปะกง"
)

st.caption(
    "แสดงเพียง 1 จุด"
)

st.map(
    bangpakong_map,
    latitude="lat",
    longitude="lon",
    size=300,
    zoom=10
)


st.divider()


# ============================================================
# GRAPH
# ============================================================

st.subheader(
    "📈 กราฟค่าจากเซนเซอร์"
)


if len(st.session_state.history) > 0:

    graph_df = pd.DataFrame(
        st.session_state.history
    )

    graph_df = graph_df.set_index(
        "เวลา"
    )


    selected = st.selectbox(
        "เลือกค่าที่ต้องการดู",
        [
            "TDS",
            "Turbidity",
            "DO"
        ]
    )


    st.line_chart(
        graph_df[[selected]],
        use_container_width=True
    )

else:

    st.info(
        "⏳ รอข้อมูลจากเซนเซอร์..."
    )


st.divider()


# ============================================================
# FIREBASE DATA
# ============================================================

with st.expander(
    "🔧 ดูข้อมูล Firebase"
):

    st.write(
        "Firebase URL"
    )

    st.code(
        FIREBASE_URL
    )

    st.write(
        "ข้อมูลปัจจุบัน"
    )

    if live_data is not None:

        st.json(
            live_data
        )

    else:

        st.error(
            "ไม่สามารถอ่าน Firebase ได้"
        )


# ============================================================
# LAST UPDATE
# ============================================================

st.caption(
    "🕒 อ่านข้อมูลล่าสุด : "
    + datetime.now(
        TH_TZ
    ).strftime(
        "%d/%m/%Y %H:%M:%S"
    )
)


# ============================================================
# AUTO REFRESH
# ============================================================

time.sleep(
    REFRESH_SECONDS
)

st.rerun()
