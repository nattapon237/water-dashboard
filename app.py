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

    /* ========================================================
       MAIN
       ======================================================== */

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

    .main {
        background-color: #f8fafc !important;
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
       TEXT
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

    p,
    label,
    .stMarkdown {
        color: #334155 !important;
    }

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {
        color: #64748b !important;
    }


    /* ========================================================
       METRIC
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


    /* ========================================================
       SELECTBOX
       ======================================================== */

    [data-baseweb="select"] {
        background-color: #ffffff !important;
    }

    [data-baseweb="select"] * {
        color: #172033 !important;
    }


    /* ========================================================
       INPUT
       ======================================================== */

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


    /* ========================================================
       BUTTON
       ======================================================== */

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


    /* ========================================================
       TABS
       ======================================================== */

    button[data-baseweb="tab"] {
        color: #475569 !important;
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
       DATAFRAME
       ======================================================== */

    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
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
       CUSTOM CARDS
       ======================================================== */

    .water-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    .online-card {
        background-color: #ecfdf5;
        border: 1px solid #86efac;
        border-radius: 12px;
        padding: 14px;
        color: #166534 !important;
        font-weight: 700;
    }

    .offline-card {
        background-color: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: 12px;
        padding: 14px;
        color: #991b1b !important;
        font-weight: 700;
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    hr {
        border-color: #e2e8f0 !important;
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

FIREBASE_DB_URL = (
    "https://cwis-c2ea8-default-rtdb."
    "asia-southeast1.firebasedatabase.app"
)

FIREBASE_SENSOR_PATH = (
    "/devices/uno-r4/status"
)

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
# BANG PAKONG MAP
# ใช้จุดคงที่ ไม่ใช้ GPS จาก ESP32
# ============================================================

BANGPAKONG_LAT = 13.6900
BANGPAKONG_LON = 101.1700

bangpakong_map = pd.DataFrame(
    {
        "lat": [BANGPAKONG_LAT],
        "lon": [BANGPAKONG_LON]
    }
)


# ============================================================
# FIREBASE FUNCTION
# ============================================================

def read_firebase():

    try:

        response = requests.get(
            FIREBASE_URL,
            timeout=5
        )

        if response.status_code == 200:

            return response.json()

        return None

    except Exception as e:

        print(
            "Firebase Error:",
            e
        )

        return None


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):

    try:

        if value is None:
            return default

        return float(value)

    except:

        return default


# ============================================================
# SENSOR ONLINE
#
# ESP32 ส่ง:
# tds
# turbidity
# do
# ============================================================

def sensor_is_online(data):

    if not isinstance(data, dict):

        return False

    sensor_keys = [
        "tds",
        "turbidity",
        "do"
    ]

    for key in sensor_keys:

        if key in data:

            value = data.get(key)

            if value is not None:

                try:

                    float(value)

                    return True

                except:

                    pass

    return False


# ============================================================
# READ FIREBASE
# ============================================================

live_data = read_firebase()


# ============================================================
# DEFAULT VALUES
# ============================================================

tds = 0.0
turbidity = 0.0
do_value = 0.0


# ============================================================
# PARSE FIREBASE
# ============================================================

if isinstance(
    live_data,
    dict
):

    tds = safe_float(
        live_data.get("tds")
    )

    turbidity = safe_float(
        live_data.get("turbidity")
    )

    do_value = safe_float(
        live_data.get("do")
    )


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
            "เวลา": now.strftime(
                "%H:%M:%S"
            ),
            "TDS": tds,
            "Turbidity": turbidity,
            "DO": do_value
        }
    )

    st.session_state.history = (
        st.session_state.history[-60:]
    )


# ============================================================
# WATER QUALITY LIMIT
# ============================================================

TDS_MAX = 1000.0
TURBIDITY_MAX = 100.0
DO_MIN = 4.0


# ============================================================
# WATER QUALITY ANALYSIS
# ============================================================

risk = []


if sensor_online:

    if tds > TDS_MAX:

        risk.append(
            f"TDS สูง {tds:.1f} ppm"
        )


    if turbidity > TURBIDITY_MAX:

        risk.append(
            f"ความขุ่นสูง {turbidity:.1f} NTU"
        )


    if do_value < DO_MIN:

        risk.append(
            f"DO ต่ำ {do_value:.2f} mg/L"
        )


water_normal = (
    sensor_online
    and
    len(risk) == 0
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


    # --------------------------------------------------------
    # SENSOR STATUS
    # --------------------------------------------------------

    st.subheader(
        "📡 Sensor Status"
    )


    if sensor_online:

        st.markdown(
            """
            <div class="online-card">
            🟢 SENSOR ONLINE
            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            "กำลังรับค่าจาก ESP32 ผ่าน Firebase"
        )

    else:

        st.markdown(
            """
            <div class="offline-card">
            🔴 SENSOR OFFLINE
            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            "ไม่พบค่าจาก ESP32"
        )


    st.divider()


    # --------------------------------------------------------
    # PARAMETERS
    # --------------------------------------------------------

    st.subheader(
        "📊 Parameters"
    )

    st.write(
        "🧂 TDS"
    )

    st.write(
        "🌫️ Turbidity"
    )

    st.write(
        "🫧 DO"
    )


    st.divider()


    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    st.write(
        "🔄 Auto Refresh"
    )

    st.info(
        f"อัปเดตทุก {REFRESH_SECONDS} วินาที"
    )


    st.divider()


    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

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
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "📊 ภาพรวมน้ำ (Dashboard)",
        "💧 คำแนะนำการใช้น้ำ",
        "📍 แจ้งเบาะแส"
    ]
)


# ============================================================
# TAB 1
# DASHBOARD
# ============================================================

with tab1:

    st.caption(
        "EEC · AGRI-WATER INTELLIGENCE"
    )

    st.title(
        "💧 ระบบตรวจสอบคุณภาพน้ำ"
    )

    st.write(
        "📍 จุดตรวจวัด : แม่น้ำบางปะกง"
    )

    st.caption(
        "ESP32 → Firebase → Dashboard"
    )


    # --------------------------------------------------------
    # ONLINE STATUS
    # --------------------------------------------------------

    if sensor_online:

        st.success(
            "🟢 SENSOR ONLINE · รับค่าจาก ESP32 แล้ว"
        )

    else:

        st.error(
            "🔴 SENSOR OFFLINE · ไม่พบข้อมูลจากเซนเซอร์"
        )


    st.divider()


    # --------------------------------------------------------
    # CURRENT VALUES
    # --------------------------------------------------------

    st.subheader(
        "📡 ค่าจากเซนเซอร์แบบ Real-time"
    )


    col1, col2, col3 = st.columns(
        3
    )


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


    # --------------------------------------------------------
    # WATER STATUS
    # --------------------------------------------------------

    st.subheader(
        "🤖 สถานะคุณภาพน้ำ"
    )


    if not sensor_online:

        st.info(
            "⏳ กำลังรอข้อมูลจากเซนเซอร์..."
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


    # --------------------------------------------------------
    # PARAMETER TABLE
    # --------------------------------------------------------

    st.subheader(
        "📋 สรุป Parameter"
    )


    parameter_data = pd.DataFrame(
        [
            {
                "Parameter": "TDS",
                "ค่า": f"{tds:.1f} ppm",
                "เกณฑ์": "≤ 1000 ppm",
                "สถานะ":
                    "ปกติ"
                    if tds <= TDS_MAX
                    else "เฝ้าระวัง"
            },
            {
                "Parameter": "Turbidity",
                "ค่า": f"{turbidity:.1f} NTU",
                "เกณฑ์": "≤ 100 NTU",
                "สถานะ":
                    "ปกติ"
                    if turbidity <= TURBIDITY_MAX
                    else "เฝ้าระวัง"
            },
            {
                "Parameter": "DO",
                "ค่า": f"{do_value:.2f} mg/L",
                "เกณฑ์": "≥ 4 mg/L",
                "สถานะ":
                    "ปกติ"
                    if do_value >= DO_MIN
                    else "เฝ้าระวัง"
            }
        ]
    )


    st.dataframe(
        parameter_data,
        use_container_width=True,
        hide_index=True
    )


    st.divider()


    # --------------------------------------------------------
    # MAP
    # --------------------------------------------------------

    st.subheader(
        "🗺️ จุดตรวจวัดแม่น้ำบางปะกง"
    )

    st.caption(
        "แสดงจุดตรวจวัดเพียง 1 จุด • ไม่ใช้ GPS จาก ESP32"
    )


    st.map(
        bangpakong_map,
        latitude="lat",
        longitude="lon",
        size=350,
        zoom=10
    )


    st.divider()


    # --------------------------------------------------------
    # GRAPH
    # --------------------------------------------------------

    st.subheader(
        "📈 กราฟค่าจากเซนเซอร์"
    )


    if len(
        st.session_state.history
    ) > 0:

        graph_df = pd.DataFrame(
            st.session_state.history
        )

        graph_df = graph_df.set_index(
            "เวลา"
        )


        selected_parameter = st.selectbox(
            "เลือกค่าที่ต้องการดู",
            [
                "TDS",
                "Turbidity",
                "DO"
            ],
            key="graph_parameter"
        )


        st.line_chart(
            graph_df[
                [selected_parameter]
            ],
            use_container_width=True
        )


    else:

        st.info(
            "⏳ รอข้อมูลจากเซนเซอร์..."
        )


    st.divider()


    # --------------------------------------------------------
    # FIREBASE DEBUG
    # --------------------------------------------------------

    with st.expander(
        "🔧 ดูข้อมูล Firebase"
    ):

        st.write(
            "Firebase Path"
        )

        st.code(
            "/devices/uno-r4/status"
        )


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
                "ไม่สามารถอ่านข้อมูลจาก Firebase ได้"
            )


# ============================================================
# TAB 2
# WATER USAGE ADVICE
# ============================================================

with tab2:

    st.title(
        "💧 คำแนะนำการใช้น้ำ"
    )

    st.caption(
        "คำแนะนำจากค่าที่ตรวจวัดได้จาก ESP32"
    )


    if not sensor_online:

        st.warning(
            "🔴 ยังไม่มีข้อมูลจากเซนเซอร์"
        )

        st.info(
            "เมื่อ ESP32 ส่ง TDS / Turbidity / DO "
            "เข้ามา ระบบจะแสดงผลที่นี่"
        )


    else:

        st.subheader(
            "📊 ผลวิเคราะห์ปัจจุบัน"
        )


        # ----------------------------------------------------
        # TDS
        # ----------------------------------------------------

        if tds <= TDS_MAX:

            st.success(
                f"🧂 TDS {tds:.1f} ppm — อยู่ในเกณฑ์"
            )

        else:

            st.warning(
                f"⚠️ TDS {tds:.1f} ppm — ควรเฝ้าระวัง"
            )


        # ----------------------------------------------------
        # TURBIDITY
        # ----------------------------------------------------

        if turbidity <= TURBIDITY_MAX:

            st.success(
                f"🌫️ Turbidity {turbidity:.1f} NTU — อยู่ในเกณฑ์"
            )

        else:

            st.warning(
                f"⚠️ Turbidity {turbidity:.1f} NTU — ความขุ่นสูง"
            )


        # ----------------------------------------------------
        # DO
        # ----------------------------------------------------

        if do_value >= DO_MIN:

            st.success(
                f"🫧 DO {do_value:.2f} mg/L — อยู่ในเกณฑ์"
            )

        else:

            st.warning(
                f"⚠️ DO {do_value:.2f} mg/L — ออกซิเจนละลายต่ำ"
            )


        st.divider()


        st.subheader(
            "🌱 แนวทางการใช้น้ำ"
        )


        if len(risk) == 0:

            st.success(
                "✅ จากค่าที่ตรวจวัดได้ "
                "สามารถนำข้อมูลไปประกอบการวางแผน "
                "ใช้น้ำเพื่อการเกษตรได้"
            )

            st.write(
                "• ควรติดตามค่าคุณภาพน้ำอย่างต่อเนื่อง"
            )

            st.write(
                "• ควรเปรียบเทียบค่าในแต่ละช่วงเวลา"
            )

            st.write(
                "• หากค่าผิดปกติควรตรวจสอบแหล่งน้ำเพิ่มเติม"
            )

        else:

            st.warning(
                "⚠️ พบค่าที่ควรเฝ้าระวัง"
            )

            st.write(
                "• ควรตรวจสอบคุณภาพน้ำเพิ่มเติม"
            )

            st.write(
                "• ไม่ควรตัดสินใจจากค่าการวัดเพียงครั้งเดียว"
            )

            st.write(
                "• หากค่าผิดปกติต่อเนื่อง "
                "ควรเก็บตัวอย่างน้ำตรวจสอบเพิ่มเติม"
            )


        st.divider()


        st.subheader(
            "📌 Parameter ที่ใช้"
        )


        st.info(
            "ESP32 เวอร์ชันล่าสุดส่ง 3 ค่า: "
            "TDS / Turbidity / DO"
        )


# ============================================================
# TAB 3
# REPORT / CLUE
# ============================================================

with tab3:

    st.title(
        "📍 แจ้งเบาะแส"
    )

    st.caption(
        "แจ้งข้อมูลความผิดปกติที่พบในแหล่งน้ำ"
    )


    st.markdown(
        """
        <div class="water-card">

        <h3>📢 แจ้งปัญหาคุณภาพน้ำ</h3>

        ใช้สำหรับบันทึกข้อมูลเมื่อพบความผิดปกติ
        ของแม่น้ำบางปะกง เช่น น้ำมีสีผิดปกติ
        มีกลิ่นผิดปกติ น้ำขุ่นมาก
        หรือพบสิ่งปนเปื้อน

        </div>
        """,
        unsafe_allow_html=True
    )


    report_type = st.selectbox(
        "ประเภทเหตุการณ์",
        [
            "น้ำมีสีผิดปกติ",
            "น้ำมีกลิ่นผิดปกติ",
            "น้ำขุ่นผิดปกติ",
            "พบสิ่งปนเปื้อน",
            "พบการปล่อยน้ำเสีย",
            "อื่น ๆ"
        ]
    )


    report_detail = st.text_area(
        "รายละเอียด",
        placeholder="กรอกรายละเอียดที่พบ..."
    )


    report_location = st.text_input(
        "สถานที่ / จุดที่พบ",
        placeholder="เช่น ริมแม่น้ำบางปะกง"
    )


    if st.button(
        "📤 บันทึกข้อมูลแจ้งเบาะแส",
        use_container_width=True
    ):

        if (
            report_detail.strip()
            or report_location.strip()
        ):

            report_time = datetime.now(
                TH_TZ
            ).strftime(
                "%d/%m/%Y %H:%M:%S"
            )


            report_data = {
                "เวลา": report_time,
                "ประเภท": report_type,
                "รายละเอียด": report_detail,
                "สถานที่": report_location
            }


            st.session_state[
                "last_report"
            ] = report_data


            st.success(
                "✅ บันทึกข้อมูลแจ้งเบาะแสแล้ว"
            )

        else:

            st.warning(
                "กรุณากรอกรายละเอียดหรือสถานที่"
            )


    if "last_report" in st.session_state:

        st.divider()

        st.subheader(
            "📋 รายการล่าสุด"
        )

        st.json(
            st.session_state[
                "last_report"
            ]
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EEC Community Water Intelligence System"
)

st.caption(
    "ESP32 → Firebase → Streamlit"
)

st.caption(
    "🕒 อัปเดตล่าสุด : "
    +
    datetime.now(
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
