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
# TIMEZONE
# ============================================================

TH_TZ = pytz.timezone("Asia/Bangkok")


# ============================================================
# FIREBASE CONFIG
# ============================================================

FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"

FIREBASE_DB_URL = (
    "https://cwis-c2ea8-default-rtdb."
    "asia-southeast1.firebasedatabase.app"
)


# ============================================================
# FIREBASE SENSOR PATH
# ============================================================

FIREBASE_SENSOR_PATH = "/devices/uno-r4/status"


# ============================================================
# SENSOR OFFLINE TIMEOUT
# ============================================================

SENSOR_OFFLINE_TIMEOUT = 30


# ============================================================
# LINE CONFIG
# ============================================================

LINE_ACCESS_TOKEN = (
    "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLyLGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
)

TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"


# ============================================================
# GOOGLE APPS SCRIPT
# ============================================================

GOOGLE_APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyn2ty8P73SvsRu-YQJSwIKFUpN3TDGpkRqHJt3y9VqroBSGjz6rGte4lHdjQAP-WQheg/"
    "exec"
)


# ============================================================
# FIREBASE AUTHENTICATION
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

            data = response.json()

            return data.get("idToken")

        return None

    except Exception as e:

        print("Firebase Auth Error:", e)

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

        print(
            "Firebase HTTP Error:",
            response.status_code
        )

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
    ph_value,
    tds_value,
    temp_value,
    do_value,
    turbidity_value
):

    if not id_token:
        return False

    url = (
        f"{FIREBASE_DB_URL}"
        f"{FIREBASE_SENSOR_PATH}.json"
        f"?auth={id_token}"
    )

    payload = {

        "ph": ph_value,

        "tds": tds_value,

        "temp": temp_value,

        "do": do_value,

        "turbidity": turbidity_value,

        "updatedAt": int(
            time.time()
        )

    }

    try:

        response = requests.put(
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
# LINE NOTIFICATION
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
# GOOGLE DRIVE UPLOAD
# ============================================================

def upload_image_to_drive(uploaded_file):

    if not uploaded_file:
        return None

    try:

        import base64

        bytes_data = uploaded_file.getvalue()

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

            if result.get("status") == "success":

                return result.get("url")

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
    ph,
    tds,
    temp,
    do_value,
    turbidity
):

    reasons = []


    if not 6.5 <= ph <= 8.5:

        reasons.append(
            f"pH ({ph:.2f}) อยู่นอกเกณฑ์ 6.5–8.5"
        )


    if tds > 1000:

        reasons.append(
            f"TDS ({tds:.1f} ppm) สูงเกิน 1,000 ppm"
        )


    if do_value < 4:

        reasons.append(
            f"DO ({do_value:.2f} mg/L) ต่ำกว่า 4.0 mg/L"
        )


    if turbidity > 100:

        reasons.append(
            f"ความขุ่น ({turbidity:.1f} NTU) สูงเกิน 100 NTU"
        )


    if temp > 35:

        reasons.append(
            f"อุณหภูมิ ({temp:.1f} °C) สูงเกิน 35 °C"
        )


    if reasons:

        return (
            False,
            "น้ำไม่ปลอดภัย",
            reasons
        )


    return (
        True,
        "ปกติ (ปลอดภัย)",
        []
    )


# ============================================================
# GAUGE
# ============================================================

def sensor_gauge(
    label,
    value,
    minimum,
    maximum,
    unit
):

    col1, col2 = st.columns(
        [3, 1]
    )

    with col1:

        st.write(
            f"**{label}**"
        )

        percentage = (
            (value - minimum)
            /
            (maximum - minimum)
        )

        percentage = max(
            0,
            min(
                1,
                percentage
            )
        )

        st.progress(
            percentage
        )

    with col2:

        st.metric(
            label="ค่า",
            value=f"{value:.2f} {unit}"
        )


# ============================================================
# MAP: RIVER BANG PAKONG
# ============================================================

BANG_PAKONG_POINTS = pd.DataFrame(
    [
        {"lat": 13.690, "lon": 101.071},
        {"lat": 13.690, "lon": 101.120},
        {"lat": 13.690, "lon": 101.170},
        {"lat": 13.690, "lon": 101.220},
        {"lat": 13.680, "lon": 101.270},
    ]
)


# ============================================================
# SENSOR HISTORY FOR CHART
# ============================================================

if "water_history" not in st.session_state:

    st.session_state.water_history = []


def add_history_point(
    ph,
    tds,
    temp,
    do_value,
    turbidity
):

    now_label = datetime.now(
        TH_TZ
    ).strftime("%H:%M:%S")

    point = {

        "เวลา":
            now_label,

        "pH":
            float(ph),

        "TDS":
            float(tds),

        "Temperature":
            float(temp),

        "DO":
            float(do_value),

        "Turbidity":
            float(turbidity)

    }

    history = (
        st.session_state.water_history
    )

    if (
        not history
        or history[-1]["เวลา"] != now_label
    ):

        history.append(point)


    st.session_state.water_history = (
        history[-30:]
    )


# ============================================================
# RENDER CHART
# ============================================================

def render_water_charts():

    if not st.session_state.water_history:

        st.info(
            "ยังไม่มีข้อมูลสำหรับกราฟ "
            "กรุณารอข้อมูลจากเซนเซอร์ "
            "หรือส่งค่าทดสอบ"
        )

        return


    chart_df = pd.DataFrame(
        st.session_state.water_history
    )


    chart_df = chart_df.set_index(
        "เวลา"
    )


    st.subheader(
        "📈 กราฟคุณภาพน้ำแบบเรียลไทม์"
    )


    metric = st.selectbox(

        "เลือกค่าที่ต้องการแสดงกราฟ",

        [
            "pH",
            "TDS",
            "Temperature",
            "DO",
            "Turbidity"
        ],

        key="chart_metric"

    )


    st.line_chart(
        chart_df[[metric]],
        use_container_width=True
    )


# ============================================================
# RENDER BANG PAKONG MAP
# ============================================================

def render_bang_pakong_map():

    st.subheader(
        "🗺️ แผนที่แม่น้ำบางปะกง"
    )


    st.caption(
        "พื้นที่อ้างอิงสำหรับระบบตรวจวัดคุณภาพน้ำ"
    )


    st.map(

        BANG_PAKONG_POINTS,

        latitude="lat",

        longitude="lon",

        size=180,

        zoom=10

    )


# ============================================================
# GET FIREBASE TOKEN
# ============================================================

id_token = get_firebase_token()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🔥 Firebase"
    )


    if id_token:

        st.success(
            "🟢 เชื่อมต่อ Firebase สำเร็จ"
        )

    else:

        st.error(
            "🔴 Firebase Authentication ล้มเหลว"
        )


    st.divider()


    now_th = datetime.now(
        TH_TZ
    )


    st.info(

        "🕒 เวลาไทย\n\n"

        + now_th.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

    )


    st.divider()


    st.title(
        "🎛️ Sensor Test"
    )


    sim_ph = st.slider(

        "pH Level",

        0.0,

        14.0,

        7.0,

        0.1

    )


    sim_tds = st.slider(

        "TDS (ppm)",

        0.0,

        1200.0,

        250.0,

        1.0

    )


    sim_temp = st.slider(

        "Temperature (°C)",

        10.0,

        45.0,

        28.0,

        0.5

    )


    sim_do = st.slider(

        "DO (mg/L)",

        0.0,

        20.0,

        6.5,

        0.1

    )


    sim_turbidity = st.slider(

        "Turbidity (NTU)",

        0.0,

        300.0,

        15.0,

        1.0

    )


    if st.button(

        "📤 ส่งค่าทดสอบเข้า Firebase",

        use_container_width=True

    ):


        success = write_mock_sensor_data(

            id_token,

            sim_ph,

            sim_tds,

            sim_temp,

            sim_do,

            sim_turbidity

        )


        if success:

            st.success(
                "✅ ส่งข้อมูลสำเร็จ"
            )

            st.rerun()

        else:

            st.error(
                "❌ ส่งข้อมูลไม่สำเร็จ"
            )


# ============================================================
# READ LIVE FIREBASE
# ============================================================

live_data = read_sensor_data(
    id_token
)


# ============================================================
# DEFAULT VALUES
# ============================================================

ph = sim_ph

tds = sim_tds

temp = sim_temp

do_value = sim_do

turbidity = sim_turbidity

sensor_connected = False

last_update = None

seconds_since_update = None


# ============================================================
# PROCESS FIREBASE DATA
# ============================================================

if (

    live_data is not None

    and isinstance(
        live_data,
        dict
    )

):

    try:

        if "ph" in live_data:

            ph = float(
                live_data["ph"]
            )


        if "tds" in live_data:

            tds = float(
                live_data["tds"]
            )


        if "temp" in live_data:

            temp = float(
                live_data["temp"]
            )


        if "do" in live_data:

            do_value = float(
                live_data["do"]
            )


        if "turbidity" in live_data:

            turbidity = float(
                live_data["turbidity"]
            )


        sensor_keys = [

            "ph",

            "tds",

            "temp",

            "do",

            "turbidity"

        ]


        has_sensor_data = any(

            key in live_data

            for key in sensor_keys

        )


        # ====================================================
        # UPDATED AT
        # ====================================================

        if "updatedAt" in live_data:

            try:

                timestamp = float(
                    live_data["updatedAt"]
                )


                if timestamp > 100000000000:

                    timestamp = (
                        timestamp / 1000
                    )


                last_update = (

                    datetime.fromtimestamp(

                        timestamp,

                        TH_TZ

                    ).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )

                )


                seconds_since_update = (

                    time.time()

                    - timestamp

                )


            except Exception:

                last_update = None

                seconds_since_update = None


        # ====================================================
        # ONLINE / OFFLINE
        # ====================================================

        if has_sensor_data:

            if seconds_since_update is None:

                sensor_connected = True

            else:

                sensor_connected = (

                    seconds_since_update

                    <= SENSOR_OFFLINE_TIMEOUT

                )


    except Exception as e:

        print(
            "Sensor Processing Error:",
            e
        )


# ============================================================
# WATER QUALITY RESULT
# ============================================================

(
    water_safe,
    water_status,
    risk_reasons
) = calculate_water_quality(

    ph,

    tds,

    temp,

    do_value,

    turbidity

)


# ============================================================
# SAVE HISTORY
# ============================================================

add_history_point(

    ph,

    tds,

    temp,

    do_value,

    turbidity

)


# ============================================================
# MAIN TABS
# ============================================================

tab_dashboard, tab_advice, tab_report = st.tabs(

    [

        "📊 ภาพรวมน้ำ",

        "💧 คำแนะนำการใช้น้ำ",

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


    # ========================================================
    # SENSOR STATUS
    # ========================================================

    if sensor_connected:

        if seconds_since_update is not None:

            age = int(

                max(

                    0,

                    seconds_since_update

                )

            )


            st.success(

                f"🟢 SENSOR ONLINE · "

                f"อัปเดตเมื่อ {age} วินาทีที่แล้ว"

            )

        else:

            st.success(

                "🟢 SENSOR ONLINE · "

                "รับข้อมูลจาก Firebase แล้ว"

            )

    else:

        st.error(

            "🔴 SENSOR OFFLINE · "

            "ไม่มีข้อมูลใหม่เกิน 30 วินาที"

        )


    # ========================================================
    # TIME
    # ========================================================

    if last_update:

        st.caption(

            f"ข้อมูลล่าสุด: {last_update}"

        )

    else:

        st.caption(
            "ยังไม่มีเวลาข้อมูลล่าสุด"
        )


    st.divider()


    # ========================================================
    # SENSOR VALUES
    # ========================================================

    st.subheader(
        "📡 ค่าคุณภาพน้ำ"
    )


    col1, col2 = st.columns(2)


    with col1:

        with st.container(border=True):

            sensor_gauge(

                "⚗️ pH LEVEL",

                ph,

                0,

                14,

                ""

            )


        with st.container(border=True):

            sensor_gauge(

                "🌡️ TEMPERATURE",

                temp,

                10,

                45,

                "°C"

            )


        with st.container(border=True):

            sensor_gauge(

                "🌫️ TURBIDITY",

                turbidity,

                0,

                300,

                "NTU"

            )


    with col2:

        with st.container(border=True):

            sensor_gauge(

                "🧂 TDS / EC",

                tds,

                0,

                1200,

                "ppm"

            )


        with st.container(border=True):

            sensor_gauge(

                "🫧 DISSOLVED OXYGEN",

                do_value,

                0,

                20,

                "mg/L"

            )


    # ========================================================
    # WATER EVALUATION
    # ========================================================

    st.divider()


    st.subheader(
        "🤖 ผลประเมินน้ำเพื่อเกษตรกรรม"
    )


    if water_safe:

        st.success(

            "✅ น้ำปลอดภัย "

            "สามารถใช้รดน้ำพืชผลและให้สัตว์น้ำได้"

        )

    else:

        st.error(

            "❌ น้ำไม่ปลอดภัย "

            "ควรหลีกเลี่ยงการนำไปใช้งาน"

        )


        st.warning(

            "⚠️ ควรตรวจสอบแหล่งกำเนิดมลพิษ "

            "และตรวจวัดซ้ำ"

        )


        if risk_reasons:

            st.write(
                "**สาเหตุที่ตรวจพบ:**"
            )


            for reason in risk_reasons:

                st.write(

                    f"• {reason}"

                )


    # ========================================================
    # SUMMARY
    # ========================================================

    st.divider()


    st.subheader(
        "📊 สรุปค่าปัจจุบัน"
    )


    c1, c2, c3, c4, c5 = st.columns(5)


    with c1:

        st.metric(

            "pH",

            f"{ph:.2f}"

        )


    with c2:

        st.metric(

            "TDS",

            f"{tds:.1f} ppm"

        )


    with c3:

        st.metric(

            "Temperature",

            f"{temp:.1f} °C"

        )


    with c4:

        st.metric(

            "DO",

            f"{do_value:.2f} mg/L"

        )


    with c5:

        st.metric(

            "Turbidity",

            f"{turbidity:.1f} NTU"

        )


    # ========================================================
    # MAP + CHART
    # ========================================================

    st.divider()


    map_col, chart_col = st.columns(
        [1, 1]
    )


    with map_col:

        render_bang_pakong_map()


    with chart_col:

        render_water_charts()


    # ========================================================
    # FIREBASE DEBUG
    # ========================================================

    with st.expander(
        "🔧 Firebase Debug"
    ):

        st.write(
            "Firebase Database:"
        )


        st.code(

            FIREBASE_DB_URL,

            language=None

        )


        st.write(
            "Firebase Path:"
        )


        st.code(

            FIREBASE_SENSOR_PATH,

            language=None

        )


        st.write(
            "ข้อมูลที่ได้รับ:"
        )


        if live_data:

            st.json(
                live_data
            )

        else:

            st.warning(
                "ไม่มีข้อมูลจาก Firebase"
            )


    # ========================================================
    # REFRESH
    # ========================================================

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

    st.caption(
        "WATER USAGE RECOMMENDATION"
    )


    st.title(
        "💧 คำแนะนำการใช้น้ำ"
    )


    if water_safe:

        st.success(
            "✅ คุณภาพน้ำอยู่ในเกณฑ์ปกติ"
        )


        st.markdown(

            """
สามารถนำไปใช้สำหรับ

- 🌱 รดน้ำพืชผล
- 🌾 ระบบเกษตรกรรม
- 🐟 แหล่งน้ำสำหรับสัตว์น้ำ
- 💧 ระบบจัดการน้ำในชุมชน

ควรตรวจวัดคุณภาพน้ำอย่างสม่ำเสมอ
"""

        )

    else:

        st.error(
            "⚠️ คุณภาพน้ำมีค่าบางตัวอยู่นอกเกณฑ์"
        )


        st.markdown(

            """
### 🚨 ข้อควรระวัง

- ❌ ไม่ควรนำไปใช้รดพืชผลโดยตรง
- ❌ ไม่ควรนำไปเติมในบ่อปลา
- ⚠️ ควรตรวจสอบแหล่งกำเนิดมลพิษ
- 🔄 ควรตรวจวัดซ้ำหลังแก้ไขปัญหา
"""

        )


    st.divider()


    st.subheader(
        "📋 เกณฑ์การประเมิน"
    )


    st.dataframe(

        {

            "Parameter": [

                "pH",

                "TDS",

                "DO",

                "Turbidity",

                "Temperature"

            ],


            "เกณฑ์": [

                "6.5 – 8.5",

                "< 1,000 ppm",

                "> 4.0 mg/L",

                "< 100 NTU",

                "< 35 °C"

            ]

        },

        use_container_width=True,

        hide_index=True

    )


# ============================================================
# REPORT
# ============================================================

with tab_report:

    st.caption(
        "COMMUNITY REPORT"
    )


    st.title(
        "📍 แจ้งเบาะแสแหล่งน้ำ"
    )


    st.info(

        "หากพบแหล่งน้ำที่มีสี กลิ่น "

        "หรือสภาพผิดปกติ สามารถแจ้งข้อมูล "

        "เพื่อใช้ประกอบการตรวจสอบได้"

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

                f"เวลา: "

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

                    "✅ ส่งข้อมูลแจ้งเบาะแสสำเร็จ"

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
