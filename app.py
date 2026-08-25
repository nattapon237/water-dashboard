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

    .stApp {
        background-color: #f8fafc;
        color: #172033;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc;
    }

    .main {
        background-color: #f8fafc;
    }

    [data-testid="stHeader"] {
        background-color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    [data-testid="stSidebar"] * {
        color: #172033 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #172033 !important;
    }

    p, span, label {
        color: #334155;
    }

    [data-testid="stCaptionContainer"] {
        color: #64748b !important;
    }

    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #172033 !important;
        font-weight: 700;
    }

    input,
    textarea {
        background-color: #ffffff !important;
        color: #172033 !important;
        border: 1px solid #cbd5e1 !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #94a3b8 !important;
    }

    [data-baseweb="select"] {
        background-color: #ffffff !important;
    }

    [data-baseweb="select"] * {
        color: #172033 !important;
    }

    .stButton > button {
        background-color: #ffffff;
        color: #172033 !important;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #f1f5f9;
        border-color: #94a3b8;
    }

    button[data-baseweb="tab"] {
        color: #64748b !important;
        font-weight: 600;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0284c7 !important;
    }

    [data-testid="stExpander"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }

    [data-testid="stFileUploader"] {
        background-color: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 8px;
    }

    hr {
        border-color: #e2e8f0;
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
# LINE
# ============================================================

LINE_ACCESS_TOKEN = (
    "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLyLGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
)

TARGET_USER_ID = (
    "Ue3bb509d1606296f491836151927b063"
)


# ============================================================
# GOOGLE APPS SCRIPT
# ============================================================

GOOGLE_APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyn2ty8P73SvsRu-YQJSwIKFUpN3TDGpkRqHJt3y9VqroBSGjz6rGte4lHdjQAP-WQheg/"
    "exec"
)


# ============================================================
# FIREBASE TOKEN
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
# WRITE TEST DATA
# ============================================================

def write_mock_sensor_data(
    id_token,
    tds_value,
    turbidity_value,
    do_value
):

    if not id_token:
        return False

    url = (
        f"{FIREBASE_DB_URL}"
        f"{FIREBASE_SENSOR_PATH}.json"
        f"?auth={id_token}"
    )

    payload = {

        "tds": float(tds_value),

        "turbidity": float(
            turbidity_value
        ),

        "do": float(do_value),

        "updatedAt": int(
            time.time()
        )

    }

    try:

        response = requests.patch(
            url,
            json=payload,
            timeout=5
        )

        return response.status_code == 200

    except Exception as e:

        print(
            "Firebase Write Error:",
            e
        )

        return False


# ============================================================
# LINE
# ============================================================

def send_line_notification(message):

    url = (
        "https://api.line.me/v2/bot/message/push"
    )

    headers = {

        "Authorization":
            f"Bearer {LINE_ACCESS_TOKEN}",

        "Content-Type":
            "application/json"

    }

    payload = {

        "to":
            TARGET_USER_ID,

        "messages": [

            {
                "type": "text",
                "text": message
            }

        ]

    }

    try:

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )

        return response.status_code == 200

    except Exception as e:

        print(
            "LINE Error:",
            e
        )

        return False


# ============================================================
# GOOGLE DRIVE
# ============================================================

def upload_image_to_drive(
    uploaded_file
):

    if not uploaded_file:
        return None

    try:

        import base64

        bytes_data = (
            uploaded_file.getvalue()
        )

        base64_data = (
            base64
            .b64encode(bytes_data)
            .decode("utf-8")
        )

        payload = {

            "filename":
                uploaded_file.name,

            "mimeType":
                uploaded_file.type,

            "base64Data":
                base64_data

        }

        response = requests.post(
            GOOGLE_APPS_SCRIPT_URL,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:

            result = response.json()

            if (
                result.get("status")
                == "success"
            ):

                return result.get(
                    "url"
                )

    except Exception as e:

        print(
            "Google Drive Error:",
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

        return (
            False,
            "ควรเฝ้าระวัง",
            reasons
        )

    return (
        True,
        "ปกติ",
        []
    )


# ============================================================
# MAP
# ============================================================

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

    point = {

        "เวลา": now,

        "TDS": float(tds),

        "Turbidity": float(
            turbidity
        ),

        "DO": float(
            do_value
        )

    }

    st.session_state.water_history.append(
        point
    )

    st.session_state.water_history = (
        st.session_state.water_history[-30:]
    )


# ============================================================
# FIREBASE
# ============================================================

id_token = get_firebase_token()

live_data = read_sensor_data(
    id_token
)


# ============================================================
# DEFAULT
# ============================================================

test_tds = 250.0
test_turbidity = 15.0
test_do = 6.5

tds = test_tds
turbidity = test_turbidity
do_value = test_do

sensor_connected = False
last_update = None
seconds_since_update = None


# ============================================================
# PROCESS DATA
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
                0 <= seconds_since_update
                <= SENSOR_OFFLINE_TIMEOUT
            )

    except Exception as e:

        print(
            "Sensor Error:",
            e
        )


# ============================================================
# HISTORY
# ============================================================

add_history(
    tds,
    turbidity,
    do_value
)


# ============================================================
# QUALITY
# ============================================================

(
    water_safe,
    water_status,
    risk_reasons
) = calculate_water_quality(
    tds,
    do_value,
    turbidity
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

    st.info(
        "🕒 เวลาไทย\n\n"
        + datetime.now(
            TH_TZ
        ).strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )

    st.divider()

    st.subheader(
        "🧪 ทดสอบเซนเซอร์"
    )

    test_tds = st.number_input(
        "TDS (ppm)",
        min_value=0.0,
        max_value=2000.0,
        value=250.0,
        step=1.0
    )

    test_turbidity = st.number_input(
        "Turbidity (NTU)",
        min_value=0.0,
        max_value=2000.0,
        value=15.0,
        step=1.0
    )

    test_do = st.number_input(
        "DO (mg/L)",
        min_value=0.0,
        max_value=14.0,
        value=6.5,
        step=0.1
    )

    if st.button(
        "📤 ส่งค่าทดสอบ",
        use_container_width=True
    ):

        if write_mock_sensor_data(
            id_token,
            test_tds,
            test_turbidity,
            test_do
        ):

            st.success(
                "✅ ส่งข้อมูลสำเร็จ"
            )

            st.rerun()

        else:

            st.error(
                "❌ ส่งข้อมูลไม่สำเร็จ"
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
    # OTHER
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
            "ยังไม่มีข้อมูล pH"
        )

    with col2:

        st.metric(
            "🌡️ Temperature",
            "--"
        )

        st.caption(
            "ยังไม่มีข้อมูลอุณหภูมิ"
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

    chart_df = pd.DataFrame(
        st.session_state.water_history
    )

    if not chart_df.empty:

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
            "Database"
        )

        st.code(
            FIREBASE_DB_URL
        )

        st.write(
            "Path"
        )

        st.code(
            FIREBASE_SENSOR_PATH
        )

        st.write(
            "ข้อมูลที่ได้รับ"
        )

        if live_data:

            st.json(
                live_data
            )

        else:

            st.warning(
                "ไม่มีข้อมูล"
            )

    if st.button(
        "🔄 รีเฟรชข้อมูล",
        use_container_width=True
    ):

        st.rerun()


# ============================================================
# ADVICE
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
            "สามารถใช้ข้อมูลเพื่อประกอบ "
            "การเฝ้าระวังและจัดการแหล่งน้ำได้"
        )

    else:

        st.warning(
            "⚠️ ควรเฝ้าระวังคุณภาพน้ำ"
        )

        st.write(
            "ควรตรวจสอบแหล่งกำเนิดมลพิษ "
            "และตรวจวัดซ้ำ"
        )

    st.divider()

    st.subheader(
        "📋 เกณฑ์เบื้องต้น"
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
        "สามารถส่งภาพและรายละเอียดได้"
    )

    uploaded_file = st.file_uploader(
        "📷 อัปโหลดรูปภาพ",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
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

    if uploaded_file:

        st.image(
            uploaded_file,
            caption="รูปภาพที่เลือก",
            use_container_width=True
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

            image_url = None

            if uploaded_file:

                with st.spinner(
                    "กำลังอัปโหลดรูปภาพ..."
                ):

                    image_url = (
                        upload_image_to_drive(
                            uploaded_file
                        )
                    )

            message = (
                "📍 แจ้งเบาะแสแหล่งน้ำ\n\n"
                "รายละเอียด:\n"
                f"{report_detail}\n\n"
                "เวลา: "
                f"{datetime.now(TH_TZ).strftime('%d/%m/%Y %H:%M:%S')}"
            )

            if image_url:

                message += (
                    "\n\nรูปภาพ:\n"
                    f"{image_url}"
                )

            if send_line_notification(
                message
            ):

                st.success(
                    "✅ ส่งข้อมูลสำเร็จ"
                )

            else:

                st.error(
                    "❌ ไม่สามารถส่งข้อมูลได้"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "💧 EEC Community Water Intelligence System"
)
