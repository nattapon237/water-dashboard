# ============================================================
# EEC COMMUNITY WATER INTELLIGENCE SYSTEM
# ระบบตรวจสอบคุณภาพน้ำอัจฉริยะ
# ============================================================

import streamlit as st
import requests
import json
import time
import math
import base64
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
# FIREBASE CONFIGURATION
# ============================================================

FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA"

FIREBASE_DB_URL = (
    "https://cwis-c2ea8-default-rtdb."
    "asia-southeast1.firebasedatabase.app"
)

# ============================================================
# LINE CONFIGURATION
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
# WHITE THEME CSS
# ============================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

.stApp {
    background: #f7f9fc;
    color: #1e293b;
}

/* =========================
   SIDEBAR
========================= */

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

section[data-testid="stSidebar"] * {
    color: #1e293b !important;
}

/* =========================
   HEADER
========================= */

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

/* =========================
   STATUS
========================= */

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 15px;
    border-radius: 999px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #334155;
    font-size: 13px;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(15,23,42,0.05);
}

.status-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--pill-color);
}

/* =========================
   GAUGE CARD
========================= */

.gauge-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 15px rgba(15,23,42,0.05);
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
}

.gauge-unit {
    font-size: 14px;
    color: #64748b;
    margin-left: 5px;
}

.gauge-track {
    position: relative;
    height: 10px;
    border-radius: 20px;
    overflow: visible;
}

.gauge-marker {
    position: absolute;
    top: -4px;
    width: 4px;
    height: 18px;
    background: #0f172a;
    border-radius: 4px;
    transform: translateX(-50%);
}

.gauge-range {
    display: flex;
    justify-content: space-between;
    color: #94a3b8;
    font-size: 11px;
    margin-top: 7px;
}

/* =========================
   PANEL
========================= */

.panel {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 22px;
    margin-top: 15px;
    box-shadow: 0 4px 15px rgba(15,23,42,0.05);
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

/* =========================
   SAFE / DANGER
========================= */

.advice-safe {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    color: #047857;
    padding: 15px;
    border-radius: 12px;
    font-weight: 700;
}

.advice-danger {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #b91c1c;
    padding: 15px;
    border-radius: 12px;
    font-weight: 700;
}

/* =========================
   INFO BOX
========================= */

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

/* =========================
   DIVIDER
========================= */

.divider {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 20px 0;
}

/* =========================
   FOOTER
========================= */

.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    padding: 25px;
}

/* =========================
   BUTTON
========================= */

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


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

            return response.json().get("idToken")

        return None

    except Exception:

        return None


# ============================================================
# READ FIREBASE SENSOR DATA
# ============================================================

def read_sensor_data(id_token):

    if not id_token:
        return None

    url = (
        f"{FIREBASE_DB_URL}/devices/uno-r4/status.json"
        f"?auth={id_token}"
    )

    try:

        response = requests.get(
            url,
            timeout=5
        )

        if response.status_code == 200:

            data = response.json()

            if isinstance(data, dict):
                return data

    except Exception:
        pass

    return None


# ============================================================
# WRITE TEST SENSOR DATA
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
        f"{FIREBASE_DB_URL}/devices/uno-r4/status.json"
        f"?auth={id_token}"
    )

    payload = {

        "ph": ph_val,

        "tds": tds_val,

        "temp": temp_val,

        "do": do_val,

        "turbidity": turb_val,

        "updatedAt": int(time.time())

    }

    try:

        response = requests.put(
            url,
            json=payload,
            timeout=5
        )

        return response.status_code == 200

    except Exception:

        return False


# ============================================================
# LINE NOTIFICATION
# ============================================================

def send_line_notification(message):

    url = "https://api.line.me/v2/bot/message/push"

    headers = {

        "Authorization":
            f"Bearer {LINE_ACCESS_TOKEN}",

        "Content-Type":
            "application/json"

    }

    payload = {

        "to": TARGET_USER_ID,

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

    except Exception:

        return False


# ============================================================
# GOOGLE DRIVE IMAGE UPLOAD
# ============================================================

def upload_image_to_drive(uploaded_file):

    if not uploaded_file:
        return None

    try:

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

    except Exception:
        pass

    return None


# ============================================================
# GET FIREBASE
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
        "🔴 ไม่สามารถเชื่อมต่อ Firebase"
    )


# ============================================================
# TIME
# ============================================================

now_th = datetime.now(TH_TZ)

st.sidebar.info(
    "🕒 เวลาไทย\n\n"
    + now_th.strftime("%d/%m/%Y %H:%M:%S")
)


# ============================================================
# SIDEBAR SENSOR CONTROL
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
# SEND MOCK DATA
# ============================================================

if st.sidebar.button(
    "📤 ส่งค่าทดสอบเข้า Firebase",
    use_container_width=True
):

    success = write_mock_sensor_data(
        id_token,
        sim_ph,
        sim_tds,
        sim_temp,
        sim_do,
        sim_turb
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
# READ LIVE SENSOR
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


# ============================================================
# APPLY FIREBASE DATA
# ============================================================

if (
    live_data
    and isinstance(live_data, dict)
):

    try:

        if "ph" in live_data:

            ph = float(
                live_data.get(
                    "ph",
                    sim_ph
                )
            )

        if "tds" in live_data:

            tds = float(
                live_data.get(
                    "tds",
                    sim_tds
                )
            )

        if "temp" in live_data:

            temp = float(
                live_data.get(
                    "temp",
                    sim_temp
                )
            )

        if "do" in live_data:

            do_val = float(
                live_data.get(
                    "do",
                    sim_do
                )
            )

        if "turbidity" in live_data:

            turbidity = float(
                live_data.get(
                    "turbidity",
                    sim_turb
                )
            )

        sensor_connected = True

        if "updatedAt" in live_data:

            try:

                timestamp = float(
                    live_data["updatedAt"]
                )

                last_update = datetime.fromtimestamp(
                    timestamp,
                    TH_TZ
                ).strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

            except Exception:

                last_update = None

    except Exception:

        sensor_connected = False


# ============================================================
# WATER QUALITY CALCULATION
# ============================================================

def calculate_water_quality(
    ph,
    tds,
    temp,
    do_val,
    turbidity
):

    reasons = []

    # pH
    if not (
        6.5 <= ph <= 8.5
    ):

        reasons.append(
            f"pH ({ph:.2f}) "
            "อยู่นอกเกณฑ์ 6.5–8.5"
        )

    # TDS
    if tds > 1000:

        reasons.append(
            f"TDS ({tds:.1f} ppm) "
            "สูงเกิน 1,000 ppm"
        )

    # DO
    if do_val < 4.0:

        reasons.append(
            f"DO ({do_val:.1f} mg/L) "
            "ต่ำกว่า 4.0 mg/L"
        )

    # Turbidity
    if turbidity > 100:

        reasons.append(
            f"ความขุ่น ({turbidity:.1f} NTU) "
            "สูงเกิน 100 NTU"
        )

    # Temperature
    if temp > 35:

        reasons.append(
            f"อุณหภูมิ ({temp:.1f} °C) "
            "สูงเกิน 35 °C"
        )

    if reasons:

        return (
            0,
            "น้ำไม่ปลอดภัย",
            "#dc2626",
            reasons,
            "❌ ห้ามนำไปรดพืชผลหรือเติมลงบ่อปลา"
        )

    else:

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
# GAUGE RENDER
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

    clipped = max(
        vmin,
        min(vmax, value)
    )

    pct = (
        (clipped - vmin)
        /
        (vmax - vmin)
        *
        100
    )

    color = "#dc2626"

    for low, high, zone_color in zones:

        if low <= value <= high:

            color = zone_color
            break

    st.markdown(
        f"""
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
                style="color:{color}"
            >

                {value:.1f}

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
                    style="left:{pct:.1f}%"
                ></div>

            </div>

            <div class="gauge-range">

                <span>{vmin}</span>

                <span>{vmax}</span>

            </div>

        </div>
        """,
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

    st.markdown(
        '<div class="hdr-eyebrow">'
        'EEC · AGRI-WATER INTELLIGENCE'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hdr-title">'
        '💧 ระบบตรวจสอบคุณภาพน้ำ'
        '</div>',
        unsafe_allow_html=True
    )

    if last_update:

        update_text = (
            f"ข้อมูลล่าสุด: {last_update}"
        )

    else:

        update_text = (
            "กำลังรอข้อมูลจากเซนเซอร์"
        )

    st.markdown(
        f'''
        <div class="hdr-sub">
            เวลาไทย:
            {now_th.strftime("%d/%m/%Y %H:%M:%S")}
            · {update_text}
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.write("")

    # ================================
    # CONNECTION
    # ================================

    if sensor_connected:

        st.markdown(
            '''
            <span
                class="status-pill"
                style="--pill-color:#16a34a"
            >
                <span class="status-dot"></span>
                🟢 รับข้อมูลจากเซนเซอร์แล้ว
            </span>
            ''',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '''
            <span
                class="status-pill"
                style="--pill-color:#f59e0b"
            >
                <span class="status-dot"></span>
                🟡 กำลังใช้ค่าทดสอบ
            </span>
            ''',
            unsafe_allow_html=True
        )

    st.markdown(
        '<hr class="divider">',
        unsafe_allow_html=True
    )

    # ================================
    # SENSOR GAUGES
    # ================================

    col1, col2 = st.columns(
        2,
        gap="small"
    )

    with col1:

        render_gauge_card(
            "⚗️",
            "pH LEVEL",
            ph,
            "",
            0,
            14,
            [
                (0, 6.49, "#dc2626"),
                (6.5, 8.5, "#16a34a"),
                (8.51, 14, "#dc2626")
            ]
        )

        render_gauge_card(
            "🌡️",
            "TEMPERATURE",
            temp,
            "°C",
            10,
            45,
            [
                (10, 35, "#16a34a"),
                (35.01, 45, "#dc2626")
            ]
        )

        render_gauge_card(
            "🌫️",
            "TURBIDITY",
            turbidity,
            "NTU",
            0,
            300,
            [
                (0, 100, "#16a34a"),
                (100.01, 300, "#dc2626")
            ]
        )

    with col2:

        render_gauge_card(
            "🧂",
            "TDS / EC",
            tds,
            "ppm",
            0,
            1200,
            [
                (0, 1000, "#16a34a"),
                (1000.01, 1200, "#dc2626")
            ]
        )

        render_gauge_card(
            "🫧",
            "DISSOLVED OXYGEN",
            do_val,
            "mg/L",
            0,
            20,
            [
                (0, 3.99, "#dc2626"),
                (4, 20, "#16a34a")
            ]
        )

    # ================================
    # EVALUATION
    # ================================

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True
    )

    st.markdown(
        '''
        <div class="panel-title">
            🤖 ผลประเมินน้ำเพื่อเกษตรกรรม
            <span class="tag">
                EVALUATION
            </span>
        </div>
        ''',
        unsafe_allow_html=True
    )

    if risk_reasons:

        st.markdown(
            f'''
            <div class="advice-danger">
                {action_advice}
            </div>
            ''',
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
            f'''
            <div class="advice-safe">
                {action_advice}
            </div>
            ''',
            unsafe_allow_html=True
        )

        st.write("")

        st.markdown(
            "• ทุกค่าอยู่ในเกณฑ์มาตรฐานปกติ"
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # ================================
    # CURRENT VALUES
    # ================================

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True
    )

    st.markdown(
        '''
        <div class="panel-title">
            📡 ค่าที่ได้รับจาก Firebase
            <span class="tag">
                REAL-TIME DATA
            </span>
        </div>
        ''',
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
            f"{do_val:.1f} mg/L"
        )

    with c5:

        st.metric(
            "Turbidity",
            f"{turbidity:.1f} NTU"
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# TAB 2
# ============================================================

with tab2:

    st.markdown(
        '<div class="hdr-eyebrow">'
        'WATER USAGE RECOMMENDATION'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hdr-title">'
        '💧 คำแนะนำการใช้น้ำ'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    if water_score >= 100:

        st.markdown(
            '''
            <div class="advice-safe">
                ✅ คุณภาพน้ำอยู่ในเกณฑ์ปกติ
            </div>
            ''',
            unsafe_allow_html=True
        )

        st.write("")

        st.markdown("""
        ### 🌱 สามารถใช้น้ำได้

        - ใช้รดน้ำพืชผล
        - ใช้ในระบบเกษตรกรรม
        - สามารถใช้กับแหล่งน้ำสำหรับสัตว์น้ำ
        - ควรตรวจวัดคุณภาพน้ำอย่างสม่ำเสมอ
        """)

    else:

        st.markdown(
            '''
            <div class="advice-danger">
                ⚠️ ควรหลีกเลี่ยงการใช้น้ำ
            </div>
            ''',
            unsafe_allow_html=True
        )

        st.write("")

        st.markdown("""
        ### 🚨 ข้อควรระวัง

        - ไม่ควรนำไปใช้รดพืชผล
        - ไม่ควรนำไปเติมในบ่อปลา
        - ควรตรวจสอบแหล่งกำเนิดมลพิษ
        - ควรตรวจวัดซ้ำหลังจากแก้ไขปัญหา
        """)

    st.markdown("---")

    st.markdown(
        "### 📊 เกณฑ์การประเมิน"
    )

    st.markdown("""
    | Parameter | เกณฑ์ |
    |---|---|
    | pH | 6.5 – 8.5 |
    | TDS | < 1,000 ppm |
    | DO | > 4.0 mg/L |
    | Turbidity | < 100 NTU |
    | Temperature | < 35 °C |
    """)


# ============================================================
# TAB 3
# ============================================================

with tab3:

    st.markdown(
        '<div class="hdr-eyebrow">'
        'COMMUNITY REPORT'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hdr-title">'
        '📍 แจ้งเบาะแสแหล่งน้ำ'
        '</div>',
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

            image_url = upload_image_to_drive(
                uploaded_file
            )

        message = (
            "📍 แจ้งเบาะแสแหล่งน้ำ\n\n"
            f"รายละเอียด:\n{report_detail}\n\n"
        )

        if image_url:

            message += (
                f"รูปภาพ:\n{image_url}"
            )

        if send_line_notification(message):

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
        · Agriculture Water Monitoring
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AUTO REFRESH
# ============================================================

time.sleep(5)

st.rerun()
