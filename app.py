# ============================================================
# EEC COMMUNITY WATER INTELLIGENCE SYSTEM
# ระบบตรวจสอบคุณภาพน้ำอัจฉริยะ
#
# Streamlit + Firebase Realtime Database
# WHITE THEME
# SENSOR ONLINE / OFFLINE
# ============================================================

import streamlit as st
import requests
import json
import time
import base64
import textwrap

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
#
# ถ้าไม่มีข้อมูลใหม่เกิน 30 วินาที
# ให้ถือว่า SENSOR OFFLINE
#
# ถ้าอยากเปลี่ยนเป็น 60 วินาที
# แก้เป็น 60
#
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
# CSS
# ============================================================

st.markdown(
    """
<style>

/* ============================================================
   GLOBAL
============================================================ */

html, body, [class*="css"] {
    font-family: Arial, "Tahoma", sans-serif;
}

.stApp {
    background: #f7f9fc;
    color: #1e293b;
}


/* ============================================================
   SIDEBAR
============================================================ */

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

section[data-testid="stSidebar"] * {
    color: #1e293b !important;
}


/* ============================================================
   HEADER
============================================================ */

.hdr-eyebrow {
    color: #0284c7;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin-bottom: 5px;
}

.hdr-title {
    color: #0f172a;
    font-size: 34px;
    font-weight: 800;
    line-height: 1.2;
}

.hdr-sub {
    color: #64748b;
    font-size: 14px;
    margin-top: 8px;
}


/* ============================================================
   STATUS
============================================================ */

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;

    padding: 9px 16px;

    border-radius: 999px;

    background: #ffffff;

    border: 1px solid #e2e8f0;

    color: #334155;

    font-size: 13px;

    font-weight: 800;

    box-shadow:
        0 2px 8px rgba(15, 23, 42, 0.05);
}

.status-dot {
    width: 9px;
    height: 9px;

    border-radius: 50%;

    background: var(--pill-color);
}


/* ============================================================
   GAUGE
============================================================ */

.gauge-card {
    background: #ffffff;

    border: 1px solid #e2e8f0;

    border-radius: 18px;

    padding: 20px;

    margin-bottom: 15px;

    box-shadow:
        0 4px 15px rgba(15, 23, 42, 0.05);
}

.gauge-top {
    display: flex;

    justify-content: space-between;

    align-items: center;
}

.gauge-label {
    font-size: 13px;

    font-weight: 800;

    color: #64748b;

    letter-spacing: 0.8px;
}

.gauge-icon {
    font-size: 24px;
}

.gauge-value {
    font-size: 34px;

    font-weight: 800;

    margin: 12px 0;

    line-height: 1.1;
}

.gauge-unit {
    font-size: 14px;

    color: #64748b;

    margin-left: 5px;

    font-weight: 600;
}

.gauge-track {
    position: relative;

    height: 10px;

    border-radius: 20px;

    overflow: visible;

    margin-top: 8px;
}

.gauge-marker {
    position: absolute;

    top: -5px;

    width: 5px;

    height: 20px;

    background: #0f172a;

    border-radius: 5px;

    transform: translateX(-50%);

    box-shadow:
        0 1px 4px rgba(0, 0, 0, 0.25);
}

.gauge-range {
    display: flex;

    justify-content: space-between;

    color: #94a3b8;

    font-size: 11px;

    margin-top: 7px;
}


/* ============================================================
   PANEL
============================================================ */

.panel {
    background: #ffffff;

    border: 1px solid #e2e8f0;

    border-radius: 18px;

    padding: 22px;

    margin-top: 15px;

    box-shadow:
        0 4px 15px rgba(15, 23, 42, 0.05);
}

.panel-title {
    color: #0f172a;

    font-size: 18px;

    font-weight: 800;

    margin-bottom: 15px;
}

.tag {
    display: inline-block;

    background: #e0f2fe;

    color: #0369a1;

    padding: 4px 9px;

    border-radius: 8px;

    font-size: 10px;

    margin-left: 5px;
}


/* ============================================================
   SAFE
============================================================ */

.advice-safe {
    background: #ecfdf5;

    border: 1px solid #a7f3d0;

    color: #047857;

    padding: 15px;

    border-radius: 12px;

    font-weight: 700;
}


/* ============================================================
   DANGER
============================================================ */

.advice-danger {
    background: #fef2f2;

    border: 1px solid #fecaca;

    color: #b91c1c;

    padding: 15px;

    border-radius: 12px;

    font-weight: 700;
}


/* ============================================================
   INFO
============================================================ */

.info-box {
    background: #ffffff;

    border: 1px solid #e2e8f0;

    border-radius: 14px;

    padding: 16px;

    margin-bottom: 12px;
}

.info-title {
    font-size: 12px;

    color: #64748b;

    font-weight: 700;
}

.info-value {
    font-size: 24px;

    font-weight: 800;

    color: #0f172a;

    margin-top: 4px;
}


/* ============================================================
   DIVIDER
============================================================ */

.divider {
    border: none;

    border-top: 1px solid #e2e8f0;

    margin: 20px 0;
}


/* ============================================================
   BUTTON
============================================================ */

.stButton > button {
    border-radius: 10px;

    font-weight: 700;
}


/* ============================================================
   METRIC
============================================================ */

[data-testid="stMetric"] {
    background: #ffffff;

    border: 1px solid #e2e8f0;

    padding: 15px;

    border-radius: 12px;
}


/* ============================================================
   FOOTER
============================================================ */

.footer {
    text-align: center;

    color: #94a3b8;

    font-size: 12px;

    padding: 30px 10px;
}

</style>
""",
    unsafe_allow_html=True
)


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

            data = response.json()

            return data.get("idToken")

        return None

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

        print(
            "Firebase HTTP:",
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
    ph_val,
    tds_val,
    temp_val,
    do_val,
    turb_val
):

    if not id_token:
        return False

    url = (
        f"{FIREBASE_DB_URL}"
        f"{FIREBASE_SENSOR_PATH}.json"
        f"?auth={id_token}"
    )

    payload = {

        "ph": ph_val,

        "tds": tds_val,

        "temp": temp_val,

        "do": do_val,

        "turbidity": turb_val,

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

        bytes_data = (
            uploaded_file
            .getvalue()
        )

        base64_data = (
            base64
            .b64encode(
                bytes_data
            )
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

            if result.get(
                "status"
            ) == "success":

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
# FIREBASE TOKEN
# ============================================================

id_token = get_firebase_token()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔥 Firebase")


if id_token:

    st.sidebar.success(
        "🟢 เชื่อมต่อ Firebase สำเร็จ"
    )

else:

    st.sidebar.error(
        "🔴 Firebase Authentication ล้มเหลว"
    )


# ============================================================
# CURRENT TIME
# ============================================================

now_th = datetime.now(
    TH_TZ
)


st.sidebar.info(
    "🕒 เวลาไทย\n\n"
    +
    now_th.strftime(
        "%d/%m/%Y %H:%M:%S"
    )
)


# ============================================================
# SENSOR TEST
# ============================================================

st.sidebar.markdown("---")

st.sidebar.title(
    "🎛️ Sensor Test"
)


sim_ph = st.sidebar.slider(
    "pH Level",
    0.0,
    14.0,
    7.0,
    0.1
)


sim_tds = st.sidebar.slider(
    "TDS (ppm)",
    0.0,
    1200.0,
    250.0,
    1.0
)


sim_temp = st.sidebar.slider(
    "Temperature (°C)",
    10.0,
    45.0,
    28.0,
    0.5
)


sim_do = st.sidebar.slider(
    "DO (mg/L)",
    0.0,
    20.0,
    6.5,
    0.1
)


sim_turb = st.sidebar.slider(
    "Turbidity (NTU)",
    0.0,
    300.0,
    15.0,
    1.0
)


# ============================================================
# SEND TEST DATA
# ============================================================

if st.sidebar.button(
    "📤 ส่งค่าทดสอบเข้า Firebase",
    use_container_width=True
):

    success = (
        write_mock_sensor_data(
            id_token,
            sim_ph,
            sim_tds,
            sim_temp,
            sim_do,
            sim_turb
        )
    )

    if success:

        st.sidebar.success(
            "✅ ส่งข้อมูลสำเร็จ"
        )

        st.rerun()

    else:

        st.sidebar.error(
            "❌ ส่งข้อมูลไม่สำเร็จ"
        )


# ============================================================
# READ LIVE DATA
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

do_val = sim_do

turbidity = sim_turb

sensor_connected = False

last_update = None

seconds_since_update = None


# ============================================================
# APPLY FIREBASE DATA
# ============================================================

if (
    live_data is not None
    and isinstance(
        live_data,
        dict
    )
):

    # ========================================================
    # อ่านค่าทีละตัว
    #
    # ไม่บังคับว่าต้องมีครบทุกค่า
    # ========================================================

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

            do_val = float(
                live_data["do"]
            )


        if "turbidity" in live_data:

            turbidity = float(
                live_data["turbidity"]
            )


        # ====================================================
        # ตรวจว่ามี Sensor Data หรือไม่
        # ====================================================

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
        # ตรวจ updatedAt
        # ====================================================

        if "updatedAt" in live_data:

            try:

                timestamp = float(
                    live_data[
                        "updatedAt"
                    ]
                )


                # ------------------------------------------------
                # รองรับ milliseconds
                # ------------------------------------------------

                if timestamp > 100000000000:

                    timestamp = (
                        timestamp / 1000
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


                # ------------------------------------------------
                # คำนวณอายุข้อมูล
                # ------------------------------------------------

                seconds_since_update = (
                    time.time()
                    -
                    timestamp
                )


            except Exception:

                last_update = None

                seconds_since_update = None


        # ====================================================
        # SENSOR ONLINE LOGIC
        # ====================================================
        #
        # กรณี 1:
        # มี Sensor Data แต่ไม่มี updatedAt
        # => ONLINE
        #
        # กรณี 2:
        # มี Sensor Data + updatedAt
        # และข้อมูลไม่เกิน 30 วินาที
        # => ONLINE
        #
        # กรณี 3:
        # ข้อมูลเกิน 30 วินาที
        # => OFFLINE
        #
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
            "Sensor Data Error:",
            e
        )

        # ถ้า Firebase ส่ง object มา
        # แต่แปลงบางค่าผิด
        # ยังไม่ถือว่า Firebase offline
        sensor_connected = (
            live_data is not None
        )


# ============================================================
# WATER QUALITY
# ============================================================

def calculate_water_quality(
    ph,
    tds,
    temp,
    do_val,
    turbidity
):

    reasons = []


    # ========================================================
    # pH
    # ========================================================

    if not (
        6.5
        <= ph
        <= 8.5
    ):

        reasons.append(
            f"pH ({ph:.2f}) "
            "อยู่นอกเกณฑ์ 6.5–8.5"
        )


    # ========================================================
    # TDS
    # ========================================================

    if tds > 1000:

        reasons.append(
            f"TDS ({tds:.1f} ppm) "
            "สูงเกิน 1,000 ppm"
        )


    # ========================================================
    # DO
    # ========================================================

    if do_val < 4.0:

        reasons.append(
            f"DO ({do_val:.1f} mg/L) "
            "ต่ำกว่า 4.0 mg/L"
        )


    # ========================================================
    # TURBIDITY
    # ========================================================

    if turbidity > 100:

        reasons.append(
            f"ความขุ่น ({turbidity:.1f} NTU) "
            "สูงเกิน 100 NTU"
        )


    # ========================================================
    # TEMPERATURE
    # ========================================================

    if temp > 35:

        reasons.append(
            f"อุณหภูมิ ({temp:.1f} °C) "
            "สูงเกิน 35 °C"
        )


    # ========================================================
    # RESULT
    # ========================================================

    if reasons:

        return (

            0,

            "น้ำไม่ปลอดภัย",

            "#dc2626",

            reasons,

            "❌ ห้ามนำไปรดพืชผลหรือเติมลงบ่อปลา"

        )


    return (

        100,

        "ปกติ (ปลอดภัย)",

        "#16a34a",

        [],

        "✅ น้ำปลอดภัย สามารถใช้รดน้ำพืชผลและให้สัตว์น้ำได้"

    )


# ============================================================
# CALCULATE
# ============================================================

(
    water_score,
    status_label,
    status_color,
    risk_reasons,
    action_advice
) = calculate_water_quality(
    ph,
    tds,
    temp,
    do_val,
    turbidity
)


# ============================================================
# GAUGE FUNCTION
# ============================================================

def render_gauge_card(
    icon,
    label,
    value,
    unit,
    vmin,
    vmax,
    zones
):

    # ========================================================
    # CLIP
    # ========================================================

    clipped = max(
        vmin,
        min(
            vmax,
            value
        )
    )


    # ========================================================
    # PERCENT
    # ========================================================

    pct = (

        (
            clipped
            -
            vmin
        )
        /
        (
            vmax
            -
            vmin
        )
        *
        100

    )


    # ========================================================
    # COLOR
    # ========================================================

    color = "#dc2626"


    for low, high, zone_color in zones:

        if (
            low
            <= value
            <= high
        ):

            color = zone_color

            break


    # ========================================================
    # HTML
    # ========================================================

    html = f"""
<div class="gauge-card">

    <div class="gauge-top">

        <span class="gauge-label">
            {label}
        </span>

        <span class="gauge-icon">
            {icon}
        </span>

    </div>


    <div
        class="gauge-value"
        style="color:{color};"
    >

        {value:.2f}

        <span class="gauge-unit">
            {unit}
        </span>

    </div>


    <div
        class="gauge-track"
        style="
            background:
            linear-gradient(
                90deg,
                #dcfce7 0%,
                #bbf7d0 100%
            );
        "
    >

        <div
            class="gauge-marker"
            style="
                left:{pct:.1f}%;
            "
        ></div>

    </div>


    <div class="gauge-range">

        <span>
            {vmin}
        </span>

        <span>
            {vmax}
        </span>

    </div>

</div>
"""


    # ========================================================
    # IMPORTANT
    # ป้องกัน Streamlit แสดง HTML เป็น Code Block
    # ========================================================

    html = (
        textwrap
        .dedent(html)
        .strip()
    )


    st.markdown(
        html,
        unsafe_allow_html=True
    )


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "📊 ภาพรวมน้ำ",
        "💧 คำแนะนำการใช้น้ำ",
        "📍 แจ้งเบาะแส"
    ]
)


# ============================================================
# TAB 1
# ============================================================

with tab1:

    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(
        """
        <div class="hdr-eyebrow">
            EEC · AGRI-WATER INTELLIGENCE
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="hdr-title">
            💧 ระบบตรวจสอบคุณภาพน้ำ
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # LAST UPDATE
    # ========================================================

    if last_update:

        update_text = (
            f"ข้อมูลล่าสุด: {last_update}"
        )

    else:

        update_text = (
            "ยังไม่มีเวลาข้อมูลล่าสุด"
        )


    st.markdown(
        f"""
        <div class="hdr-sub">

            เวลาไทย:
            {now_th.strftime("%d/%m/%Y %H:%M:%S")}

            ·

            {update_text}

        </div>
        """,
        unsafe_allow_html=True
    )


    st.write("")


    # ========================================================
    # SENSOR STATUS
    # ========================================================

    if sensor_connected:

        if seconds_since_update is not None:

            age_text = (
                f"อัปเดตเมื่อ "
                f"{int(max(0, seconds_since_update))} "
                f"วินาทีที่แล้ว"
            )

        else:

            age_text = (
                "รับข้อมูลจาก Firebase แล้ว"
            )


        st.markdown(
            f"""
            <div
                class="status-pill"
                style="--pill-color:#16a34a"
            >

                <span class="status-dot"></span>

                🟢 SENSOR ONLINE

                <span style="
                    color:#64748b;
                    font-weight:600;
                ">

                    · {age_text}

                </span>

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            """
            <div
                class="status-pill"
                style="--pill-color:#dc2626"
            >

                <span class="status-dot"></span>

                🔴 SENSOR OFFLINE

                <span style="
                    color:#64748b;
                    font-weight:600;
                ">

                    · ไม่มีข้อมูลใหม่เกิน
                    30 วินาที

                </span>

            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # DEBUG FIREBASE
    # ========================================================

    with st.expander(
        "🔧 Firebase Debug"
    ):

        st.write(
            "Firebase Path:",
            FIREBASE_SENSOR_PATH
        )

        st.write(
            "Firebase Response:"
        )

        st.json(
            live_data
            if live_data is not None
            else {}
        )


    st.markdown(
        '<hr class="divider">',
        unsafe_allow_html=True
    )


    # ========================================================
    # GAUGES
    # ========================================================

    col1, col2 = st.columns(
        2,
        gap="small"
    )


    # ========================================================
    # LEFT
    # ========================================================

    with col1:

        # ----------------------------------------------------
        # pH
        # ----------------------------------------------------

        render_gauge_card(
            "⚗️",
            "pH LEVEL",
            ph,
            "",
            0,
            14,
            [

                (
                    0,
                    6.49,
                    "#dc2626"
                ),

                (
                    6.5,
                    8.5,
                    "#16a34a"
                ),

                (
                    8.51,
                    14,
                    "#dc2626"
                )

            ]
        )


        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        render_gauge_card(
            "🌡️",
            "TEMPERATURE",
            temp,
            "°C",
            10,
            45,
            [

                (
                    10,
                    35,
                    "#16a34a"
                ),

                (
                    35.01,
                    45,
                    "#dc2626"
                )

            ]
        )


        # ----------------------------------------------------
        # Turbidity
        # ----------------------------------------------------

        render_gauge_card(
            "🌫️",
            "TURBIDITY",
            turbidity,
            "NTU",
            0,
            300,
            [

                (
                    0,
                    100,
                    "#16a34a"
                ),

                (
                    100.01,
                    300,
                    "#dc2626"
                )

            ]
        )


    # ========================================================
    # RIGHT
    # ========================================================

    with col2:

        # ----------------------------------------------------
        # TDS
        # ----------------------------------------------------

        render_gauge_card(
            "🧂",
            "TDS / EC",
            tds,
            "ppm",
            0,
            1200,
            [

                (
                    0,
                    1000,
                    "#16a34a"
                ),

                (
                    1000.01,
                    1200,
                    "#dc2626"
                )

            ]
        )


        # ----------------------------------------------------
        # DO
        # ----------------------------------------------------

        render_gauge_card(
            "🫧",
            "DISSOLVED OXYGEN",
            do_val,
            "mg/L",
            0,
            20,
            [

                (
                    0,
                    3.99,
                    "#dc2626"
                ),

                (
                    4,
                    20,
                    "#16a34a"
                )

            ]
        )


    # ========================================================
    # WATER EVALUATION
    # ========================================================

    st.markdown(
        """
        <div class="panel">
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="panel-title">

            🤖 ผลประเมินน้ำเพื่อเกษตรกรรม

            <span class="tag">
                EVALUATION
            </span>

        </div>
        """,
        unsafe_allow_html=True
    )


    if risk_reasons:

        st.markdown(
            f"""
            <div class="advice-danger">

                {action_advice}

            </div>
            """,
            unsafe_allow_html=True
        )


        st.write("")


        st.markdown(
            "**⚠️ สาเหตุที่ตรวจพบ**"
        )


        for reason in risk_reasons:

            st.markdown(
                f"• {reason}"
            )

    else:

        st.markdown(
            f"""
            <div class="advice-safe">

                {action_advice}

            </div>
            """,
            unsafe_allow_html=True
        )


        st.write("")


        st.markdown(
            "• ทุกค่าอยู่ในเกณฑ์ปกติ"
        )


    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # FIREBASE DATA
    # ========================================================

    st.markdown(
        """
        <div class="panel">
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="panel-title">

            📡 ค่าที่ได้รับจาก Firebase

            <span class="tag">
                REAL-TIME DATA
            </span>

        </div>
        """,
        unsafe_allow_html=True
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
            f"{do_val:.2f} mg/L"
        )


    with c5:

        st.metric(
            "Turbidity",
            f"{turbidity:.1f} NTU"
        )


    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# TAB 2
# ============================================================

with tab2:

    st.markdown(
        """
        <div class="hdr-eyebrow">
            WATER USAGE RECOMMENDATION
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="hdr-title">
            💧 คำแนะนำการใช้น้ำ
        </div>
        """,
        unsafe_allow_html=True
    )


    st.write("")


    if water_score >= 100:

        st.markdown(
            """
            <div class="advice-safe">

                ✅ คุณภาพน้ำอยู่ในเกณฑ์ปกติ

            </div>
            """,
            unsafe_allow_html=True
        )


        st.write("")


        st.markdown(
            """
### 🌱 สามารถใช้น้ำได้

- ใช้รดน้ำพืชผล
- ใช้ในระบบเกษตรกรรม
- สามารถใช้กับแหล่งน้ำสำหรับสัตว์น้ำ
- ควรตรวจวัดคุณภาพน้ำอย่างสม่ำเสมอ
"""
        )

    else:

        st.markdown(
            """
            <div class="advice-danger">

                ⚠️ ควรหลีกเลี่ยงการใช้น้ำ

            </div>
            """,
            unsafe_allow_html=True
        )


        st.write("")


        st.markdown(
            """
### 🚨 ข้อควรระวัง

- ไม่ควรนำไปใช้รดพืชผล
- ไม่ควรนำไปเติมในบ่อปลา
- ควรตรวจสอบแหล่งกำเนิดมลพิษ
- ควรตรวจวัดซ้ำหลังจากแก้ไขปัญหา
"""
        )


    st.markdown("---")


    st.markdown(
        "### 📊 เกณฑ์การประเมิน"
    )


    st.markdown(
        """
| Parameter | เกณฑ์ |
|---|---|
| pH | 6.5 – 8.5 |
| TDS | < 1,000 ppm |
| DO | > 4.0 mg/L |
| Turbidity | < 100 NTU |
| Temperature | < 35 °C |
"""
    )


# ============================================================
# TAB 3
# ============================================================

with tab3:

    st.markdown(
        """
        <div class="hdr-eyebrow">
            COMMUNITY REPORT
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown(
        """
        <div class="hdr-title">
            📍 แจ้งเบาะแสแหล่งน้ำ
        </div>
        """,
        unsafe_allow_html=True
    )


    st.write("")


    st.info(
        "หากพบแหล่งน้ำที่มีสี กลิ่น "
        "หรือสภาพผิดปกติ สามารถอัปโหลดภาพ "
        "เพื่อใช้เป็นข้อมูลประกอบการตรวจสอบได้"
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
            "ระบุรายละเอียดของแหล่งน้ำ "
            "เช่น สี กลิ่น หรือสิ่งผิดปกติ"
        )
    )


    if st.button(
        "📤 ส่งข้อมูลแจ้งเบาะแส",
        use_container_width=True
    ):

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
        )


        if image_url:

            message += (
                "รูปภาพ:\n"
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

st.markdown(
    """
    <div class="footer">

        EEC Community Water Intelligence System

        <br>

        Agriculture Water Monitoring

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR REFRESH
# ============================================================

st.sidebar.markdown("---")


if st.sidebar.button(
    "🔄 รีเฟรชข้อมูล",
    use_container_width=True
):

    st.rerun()
