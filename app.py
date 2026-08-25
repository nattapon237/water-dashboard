from pathlib import Path
import base64

# Read the previously generated Base64 image file.
b64_file = Path("/mnt/data/water_sensor_image_base64.txt")
image_data_uri = b64_file.read_text(encoding="utf-8").strip()

# Build a complete Streamlit application.
app_code = r'''import streamlit as st
import pandas as pd
import requests
import json
import time
import math
import base64
from datetime import datetime
import pytz
import altair as alt
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="ระบบตรวจวัดคุณภาพแหล่งน้ำอัจฉริยะ",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

TH_TZ = pytz.timezone("Asia/Bangkok")

# =========================================================
# FIREBASE CONFIG
# ใส่ค่าจริงใน .streamlit/secrets.toml
# =========================================================
FIREBASE_WEB_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY", "")
FIREBASE_DB_URL = st.secrets.get(
    "FIREBASE_DB_URL",
    "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app",
)

# LINE ใช้เฉพาะฟังก์ชันแจ้งเบาะแส
LINE_ACCESS_TOKEN = st.secrets.get("LINE_ACCESS_TOKEN", "")
TARGET_USER_ID = st.secrets.get("TARGET_USER_ID", "")

# Google Apps Script สำหรับอัปโหลดรูป
GOOGLE_APPS_SCRIPT_URL = st.secrets.get("GOOGLE_APPS_SCRIPT_URL", "")

# =========================================================
# WATER SENSOR LOCATION
# จากพิกัดในภาพที่ผู้ใช้ส่งมา
# =========================================================
SENSOR_LAT = 13.689108
SENSOR_LON = 101.079153
SENSOR_NAME = "จุดตรวจวัดคุณภาพน้ำ 01"

# =========================================================
# SENSOR THRESHOLDS
# เป็นค่าเกณฑ์สำหรับต้นแบบระบบ
# ไม่ใช้เพื่อยืนยันความปลอดภัยสำหรับการบริโภค
# =========================================================
PH_MIN = 6.5
PH_MAX = 8.5

TDS_MAX = 1000.0

ORP_MIN = 200.0

# =========================================================
# EMBEDDED HERO IMAGE
# รูปทุ่นตรวจวัดคุณภาพน้ำถูกฝังเป็น Base64
# =========================================================
WATER_SENSOR_IMAGE = r"""__WATER_SENSOR_IMAGE_DATA_URI__"""


# =========================================================
# LOAD CUSTOM CSS
# =========================================================
try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass


# =========================================================
# FIREBASE AUTH
# =========================================================
@st.cache_data(ttl=3000)
def get_firebase_token():
    if not FIREBASE_WEB_API_KEY:
        return None

    auth_url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
        f"?key={FIREBASE_WEB_API_KEY}"
    )

    try:
        res = requests.post(
            auth_url,
            json={"returnSecureToken": True},
            timeout=8,
        )
        if res.status_code == 200:
            return res.json().get("idToken")
    except Exception:
        pass

    return None


# =========================================================
# FIREBASE CURRENT SENSOR DATA
# =========================================================
@st.cache_data(ttl=15)
def read_sensor_data(id_token):
    if not id_token:
        return None

    url = (
        f"{FIREBASE_DB_URL}/devices/uno-r4/status.json"
        f"?auth={id_token}"
    )

    try:
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            return data if isinstance(data, dict) else None
    except Exception:
        pass

    return None


# =========================================================
# FIREBASE SENSOR HISTORY
# =========================================================
@st.cache_data(ttl=20)
def read_sensor_history(id_token):
    if not id_token:
        return []

    url = (
        f"{FIREBASE_DB_URL}/devices/uno-r4/history.json"
        f"?auth={id_token}"
    )

    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return []

        data = res.json()

        if not isinstance(data, dict):
            return []

        rows = []

        for key, item in data.items():
            if not isinstance(item, dict):
                continue

            try:
                timestamp = item.get("timestamp", key)
                timestamp = float(timestamp)
            except Exception:
                continue

            ph_value = item.get("ph")
            tds_value = item.get("tds")
            orp_value = item.get("orp")

            if ph_value is None or tds_value is None or orp_value is None:
                continue

            try:
                rows.append(
                    {
                        "timestamp": timestamp,
                        "ph": float(ph_value),
                        "tds": float(tds_value),
                        "orp": float(orp_value),
                    }
                )
            except (TypeError, ValueError):
                continue

        rows.sort(key=lambda x: x["timestamp"])
        return rows

    except Exception:
        return []


# =========================================================
# UPLOAD IMAGE TO GOOGLE DRIVE
# =========================================================
def upload_image_to_drive(uploaded_file):
    if not uploaded_file or not GOOGLE_APPS_SCRIPT_URL:
        return None

    try:
        bytes_data = uploaded_file.getvalue()
        base64_data = base64.b64encode(bytes_data).decode("utf-8")

        payload = {
            "filename": uploaded_file.name,
            "mimeType": uploaded_file.type,
            "base64Data": base64_data,
        }

        res = requests.post(
            GOOGLE_APPS_SCRIPT_URL,
            json=payload,
            timeout=30,
        )

        if res.status_code == 200:
            result = res.json()
            if result.get("status") == "success":
                return result.get("url")

    except Exception:
        pass

    return None


# =========================================================
# LINE NOTIFICATION
# =========================================================
def send_line_notification(message):
    if not LINE_ACCESS_TOKEN or not TARGET_USER_ID:
        return False

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "to": TARGET_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message,
            }
        ],
    }

    try:
        res = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )
        return res.status_code == 200
    except Exception:
        return False


# =========================================================
# WATER QUALITY EVALUATION
# =========================================================
def calculate_water_quality(ph, tds, orp):
    reasons = []
    warnings = []

    if ph is None:
        reasons.append("ไม่พบค่า pH")
    elif not (PH_MIN <= ph <= PH_MAX):
        reasons.append(
            f"pH ({ph:.2f}) อยู่นอกช่วงตัวอย่าง {PH_MIN:.1f}-{PH_MAX:.1f}"
        )

    if tds is None:
        reasons.append("ไม่พบค่า TDS")
    elif tds > TDS_MAX:
        reasons.append(
            f"TDS ({tds:.1f} ppm) สูงกว่าเกณฑ์ตัวอย่าง {TDS_MAX:.0f} ppm"
        )

    if orp is None:
        reasons.append("ไม่พบค่า ORP")
    elif orp < ORP_MIN:
        warnings.append(
            f"ORP ({orp:.0f} mV) ต่ำกว่าเกณฑ์เฝ้าระวัง {ORP_MIN:.0f} mV"
        )

    total_issues = len(reasons) + len(warnings)

    if ph is None or tds is None or orp is None:
        return (
            0,
            "รอข้อมูล Sensor",
            "#64748b",
            reasons,
            warnings,
            "กำลังรอข้อมูลจาก Sensor",
        )

    if reasons:
        return (
            35,
            "ผิดปกติ",
            "#dc2626",
            reasons,
            warnings,
            "ควรตรวจสอบจุดติดตั้งและคุณภาพน้ำเพิ่มเติม",
        )

    if warnings:
        return (
            70,
            "เฝ้าระวัง",
            "#eab308",
            reasons,
            warnings,
            "ควรติดตามค่า Sensor อย่างต่อเนื่อง",
        )

    return (
        100,
        "ปกติ",
        "#16a34a",
        [],
        [],
        "ค่าที่ตรวจวัดอยู่ในช่วงตัวอย่างที่ระบบกำหนด",
    )


# =========================================================
# HELPERS
# =========================================================
def sensor_status(updated_at):
    if not updated_at:
        return False, "Offline"

    try:
        ts = float(updated_at)
        now = time.time()
        age = now - ts

        # Offline if no update for more than 5 minutes
        if age <= 300:
            return True, "Online"

    except Exception:
        pass

    return False, "Offline"


def format_update_time(updated_at):
    if not updated_at:
        return "--"

    try:
        dt = datetime.fromtimestamp(float(updated_at), TH_TZ)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "--"


def safe_float(data, key):
    if not isinstance(data, dict):
        return None

    value = data.get(key)

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def display_value(value, digits=2):
    if value is None:
        return "--"
    return f"{value:.{digits}f}"


def status_for_ph(value):
    if value is None:
        return "รอข้อมูล"
    if PH_MIN <= value <= PH_MAX:
        return "ปกติ"
    return "ผิดปกติ"


def status_for_tds(value):
    if value is None:
        return "รอข้อมูล"
    if value <= TDS_MAX:
        return "ปกติ"
    return "ผิดปกติ"


def status_for_orp(value):
    if value is None:
        return "รอข้อมูล"
    if value >= ORP_MIN:
        return "ปกติ"
    return "เฝ้าระวัง"


def filter_history(rows, hours):
    if not rows:
        return []

    cutoff = time.time() - (hours * 3600)

    filtered = [
        row for row in rows
        if row.get("timestamp", 0) >= cutoff
    ]

    # If the requested period has no records, keep the newest records.
    if not filtered:
        return rows[-100:]

    return filtered[-500:]


def history_dataframe(rows):
    if not rows:
        return pd.DataFrame(
            columns=["เวลา", "pH", "TDS (ppm)", "ORP (mV)", "สถานะ"]
        )

    records = []

    for row in rows:
        try:
            dt = datetime.fromtimestamp(
                float(row["timestamp"]),
                TH_TZ,
            )

            ph_value = float(row["ph"])
            tds_value = float(row["tds"])
            orp_value = float(row["orp"])

            _, status, _, _, _, _ = calculate_water_quality(
                ph_value,
                tds_value,
                orp_value,
            )

            records.append(
                {
                    "เวลา": dt.strftime("%d/%m/%Y %H:%M:%S"),
                    "pH": round(ph_value, 2),
                    "TDS (ppm)": round(tds_value, 1),
                    "ORP (mV)": round(orp_value, 1),
                    "สถานะ": status,
                }
            )
        except Exception:
            continue

    return pd.DataFrame(records)


# =========================================================
# GET DATA
# =========================================================
id_token = get_firebase_token()
live_data = read_sensor_data(id_token)
history_rows = read_sensor_history(id_token)

now_th = datetime.now(TH_TZ)

ph = safe_float(live_data, "ph")
tds = safe_float(live_data, "tds")
orp = safe_float(live_data, "orp")
updated_at = live_data.get("updatedAt") if live_data else None

sensor_online, sensor_state = sensor_status(updated_at)

water_score, status_label, status_color, risk_reasons, warnings, action_advice = (
    calculate_water_quality(ph, tds, orp)
)


# =========================================================
# AUTO REFRESH
# =========================================================
# 30 วินาที
st_autorefresh(
    interval=30 * 1000,
    key="water_dashboard_refresh",
)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div style="
            font-size:1.35rem;
            font-weight:850;
            color:#0f172a;
            margin-bottom:4px;">
            💧 WATER MONITOR
        </div>
        <div style="
            color:#64748b;
            font-size:.78rem;
            margin-bottom:18px;">
            Smart Water Quality System
        </div>
        """,
        unsafe_allow_html=True,
    )

    if id_token:
        st.success("🟢 Firebase Connected")
    else:
        st.error("🔴 Firebase Disconnected")

    if sensor_online:
        st.success("🟢 Sensor Online")
    else:
        st.error("🔴 Sensor Offline")

    st.info(
        f"🕒 เวลาไทย\n\n"
        f"{now_th.strftime('%d/%m/%Y %H:%M:%S')}"
    )

    st.markdown("---")

    st.markdown(
        """
        <div style="
            color:#0f172a;
            font-weight:800;
            font-size:.9rem;
            margin-bottom:8px;">
            📡 สถานีตรวจวัด
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(SENSOR_NAME)
    st.caption(f"Lat: {SENSOR_LAT:.6f}")
    st.caption(f"Lon: {SENSOR_LON:.6f}")

    st.markdown("---")

    if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("ระบบรีเฟรชอัตโนมัติทุก 30 วินาที")


# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(
    [
        "📊 Dashboard",
        "📈 ประวัติข้อมูล",
        "📍 จุดติดตั้ง Sensor",
    ]
)


# =========================================================
# TAB 1 — DASHBOARD
# =========================================================
with tab1:

    st.markdown(
        '<div class="hdr-eyebrow">SMART WATER QUALITY MONITORING</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hdr-title">💧 ระบบตรวจวัดคุณภาพแหล่งน้ำอัจฉริยะ</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="hdr-sub">'
        f'จุดตรวจวัด: {SENSOR_NAME} · '
        f'อัปเดตล่าสุด: {format_update_time(updated_at)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Hero image
    st.markdown(
        f"""
        <div class="water-hero">
            <img src="{WATER_SENSOR_IMAGE}" />
            <div class="water-hero-overlay">
                <div class="water-hero-title">
                    ทุ่นตรวจวัดคุณภาพแหล่งน้ำอัจฉริยะ
                </div>
                <div class="water-hero-sub">
                    ตรวจวัด pH · TDS · ORP และส่งข้อมูลเข้าสู่ Dashboard
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status
    st.markdown(
        f"""
        <div style="margin-bottom:14px;">
            <span class="status-pill" style="--pill-color:{status_color}">
                <span class="status-dot"></span>
                คุณภาพน้ำ: {status_label}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # SENSOR CARDS
    # =====================================================
    c1, c2, c3 = st.columns(3, gap="medium")

    sensor_cards = [
        (
            c1,
            "⚗️",
            "pH",
            display_value(ph, 2),
            "pH",
            status_for_ph(ph),
        ),
        (
            c2,
            "🧂",
            "TDS",
            display_value(tds, 1),
            "ppm",
            status_for_tds(tds),
        ),
        (
            c3,
            "🔬",
            "ORP",
            display_value(orp, 0),
            "mV",
            status_for_orp(orp),
        ),
    ]

    for col, icon, label, value, unit, sensor_status_text in sensor_cards:
        with col:
            if sensor_status_text == "ปกติ":
                color = "#16a34a"
                soft = "#dcfce7"
            elif sensor_status_text == "เฝ้าระวัง":
                color = "#eab308"
                soft = "#fef9c3"
            elif sensor_status_text == "ผิดปกติ":
                color = "#dc2626"
                soft = "#fee2e2"
            else:
                color = "#64748b"
                soft = "#f1f5f9"

            st.markdown(
                f"""
                <div style="
                    background:#ffffff;
                    border:1px solid #dbe7ef;
                    border-radius:18px;
                    padding:20px;
                    box-shadow:0 8px 28px rgba(15,23,42,.07);
                    min-height:170px;">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;">
                        <div style="
                            color:#64748b;
                            font-size:.78rem;
                            font-weight:800;
                            letter-spacing:.08em;">
                            {label.upper()} SENSOR
                        </div>
                        <div style="
                            width:40px;
                            height:40px;
                            display:grid;
                            place-items:center;
                            background:#e0f2fe;
                            border-radius:12px;
                            font-size:1.15rem;">
                            {icon}
                        </div>
                    </div>

                    <div style="
                        margin-top:16px;
                        font-size:2.15rem;
                        font-weight:850;
                        letter-spacing:-.04em;
                        color:#0284c7;">
                        {value}
                        <span style="
                            font-size:.85rem;
                            color:#64748b;
                            font-weight:650;">
                            {unit}
                        </span>
                    </div>

                    <div style="
                        display:inline-block;
                        margin-top:12px;
                        padding:5px 10px;
                        border-radius:999px;
                        background:{soft};
                        color:{color};
                        font-size:.75rem;
                        font-weight:800;">
                        ● {sensor_status_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # =====================================================
    # WATER QUALITY EVALUATION
    # =====================================================
    reasons_html = ""

    if risk_reasons:
        reasons_html += "".join(
            f'<div style="color:#dc2626;margin-top:4px;">• {reason}</div>'
            for reason in risk_reasons
        )

    if warnings:
        reasons_html += "".join(
            f'<div style="color:#a16207;margin-top:4px;">• {warning}</div>'
            for warning in warnings
        )

    if not reasons_html:
        reasons_html = (
            '<div style="color:#16a34a;margin-top:6px;">'
            "• ยังไม่พบค่าที่ผิดปกติจากเกณฑ์ตัวอย่าง"
            "</div>"
        )

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">
                🌊 ผลประเมินคุณภาพน้ำ
                <span class="tag">REAL SENSOR</span>
            </div>

            <div style="
                display:flex;
                align-items:center;
                gap:20px;
                margin-top:16px;">

                <div style="
                    width:110px;
                    height:110px;
                    border-radius:50%;
                    background:conic-gradient(
                        {status_color} {water_score}%,
                        #e2e8f0 {water_score}% 100%
                    );
                    display:grid;
                    place-items:center;
                    flex-shrink:0;">

                    <div style="
                        width:88px;
                        height:88px;
                        border-radius:50%;
                        background:#ffffff;
                        display:grid;
                        place-items:center;
                        text-align:center;">

                        <div>
                            <div style="
                                color:{status_color};
                                font-size:1.15rem;
                                font-weight:850;">
                                {water_score}
                            </div>
                            <div style="
                                color:#64748b;
                                font-size:.65rem;">
                                / 100
                            </div>
                        </div>
                    </div>
                </div>

                <div>
                    <div style="
                        color:{status_color};
                        font-size:1.2rem;
                        font-weight:850;">
                        {status_label}
                    </div>

                    <div style="
                        color:#64748b;
                        font-size:.84rem;
                        margin-top:4px;">
                        การประเมินจากค่า pH, TDS และ ORP
                    </div>

                    {reasons_html}
                </div>
            </div>

            <div style="
                margin-top:18px;
                padding:12px 14px;
                border-radius:12px;
                background:#f0f9ff;
                border:1px solid #bae6fd;
                color:#0369a1;
                font-size:.84rem;">
                💡 {action_advice}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # =====================================================
    # MINI GRAPH
    # =====================================================
    st.markdown("### 📈 แนวโน้มคุณภาพน้ำ")

    graph_hours = st.selectbox(
        "ช่วงเวลาที่ต้องการดู",
        options=[1, 6, 24, 168],
        format_func=lambda x: (
            "1 ชั่วโมง" if x == 1
            else "6 ชั่วโมง" if x == 6
            else "24 ชั่วโมง" if x == 24
            else "7 วัน"
        ),
        key="dashboard_graph_hours",
    )

    filtered_rows = filter_history(history_rows, graph_hours)

    if filtered_rows:
        chart_df = pd.DataFrame(filtered_rows)

        chart_df["เวลา"] = pd.to_datetime(
            chart_df["timestamp"],
            unit="s",
            utc=True,
        ).dt.tz_convert("Asia/Bangkok")

        chart_df["เวลา"] = chart_df["เวลา"].dt.strftime(
            "%d/%m %H:%M"
        )

        left, right = st.columns(2, gap="medium")

        with left:
            ph_chart = (
                alt.Chart(chart_df)
                .mark_line(
                    point=True,
                    strokeWidth=3,
                    color="#0284c7",
                )
                .encode(
                    x=alt.X(
                        "เวลา:N",
                        title="เวลา",
                        axis=alt.Axis(
                            labelAngle=-35,
                            labelColor="#64748b",
                            titleColor="#64748b",
                        ),
                    ),
                    y=alt.Y(
                        "ph:Q",
                        title="pH",
                        scale=alt.Scale(domain=[0, 14]),
                    ),
                    tooltip=[
                        alt.Tooltip("เวลา:N", title="เวลา"),
                        alt.Tooltip("ph:Q", title="pH", format=".2f"),
                    ],
                )
                .properties(
                    height=300,
                    title="pH",
                )
                .configure_view(
                    stroke="#dbe7ef",
                )
                .configure_title(
                    color="#0f172a",
                    anchor="start",
                )
            )

            st.altair_chart(ph_chart, use_container_width=True)

        with right:
            tds_chart = (
                alt.Chart(chart_df)
                .mark_line(
                    point=True,
                    strokeWidth=3,
                    color="#16a34a",
                )
                .encode(
                    x=alt.X(
                        "เวลา:N",
                        title="เวลา",
                        axis=alt.Axis(
                            labelAngle=-35,
                            labelColor="#64748b",
                            titleColor="#64748b",
                        ),
                    ),
                    y=alt.Y(
                        "tds:Q",
                        title="TDS (ppm)",
                    ),
                    tooltip=[
                        alt.Tooltip("เวลา:N", title="เวลา"),
                        alt.Tooltip("tds:Q", title="TDS", format=".1f"),
                    ],
                )
                .properties(
                    height=300,
                    title="TDS",
                )
                .configure_view(
                    stroke="#dbe7ef",
                )
                .configure_title(
                    color="#0f172a",
                    anchor="start",
                )
            )

            st.altair_chart(tds_chart, use_container_width=True)

        orp_chart = (
            alt.Chart(chart_df)
            .mark_line(
                point=True,
                strokeWidth=3,
                color="#7c3aed",
            )
            .encode(
                x=alt.X(
                    "เวลา:N",
                    title="เวลา",
                    axis=alt.Axis(
                        labelAngle=-35,
                        labelColor="#64748b",
                        titleColor="#64748b",
                    ),
                ),
                y=alt.Y(
                    "orp:Q",
                    title="ORP (mV)",
                ),
                tooltip=[
                    alt.Tooltip("เวลา:N", title="เวลา"),
                    alt.Tooltip("orp:Q", title="ORP", format=".0f"),
                ],
            )
            .properties(
                height=300,
                title="ORP",
            )
            .configure_view(
                stroke="#dbe7ef",
            )
            .configure_title(
                color="#0f172a",
                anchor="start",
            )
        )

        st.altair_chart(orp_chart, use_container_width=True)

    else:
        st.info(
            "📭 ยังไม่มีข้อมูล History จาก Sensor "
            "จึงยังไม่สามารถแสดงกราฟย้อนหลังได้"
        )

    # =====================================================
    # MAP
    # =====================================================
    st.markdown("### 📍 จุดติดตั้ง Sensor")

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <link rel="stylesheet"
              href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
        </script>

        <style>
            html, body {{
                margin:0;
                padding:0;
                width:100%;
                height:100%;
            }}

            #map {{
                width:100%;
                height:470px;
                border-radius:18px;
            }}

            .leaflet-popup-content-wrapper {{
                border-radius:12px;
            }}

            .popup-title {{
                font-weight:800;
                color:#0f172a;
                margin-bottom:7px;
            }}

            .popup-row {{
                color:#475569;
                font-size:13px;
                margin:3px 0;
            }}
        </style>
    </head>

    <body>
        <div id="map"></div>

        <script>
            const lat = {SENSOR_LAT};
            const lon = {SENSOR_LON};

            const map = L.map('map').setView([lat, lon], 15);

            L.tileLayer(
                'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
                {{
                    maxZoom: 19,
                    attribution: '&copy; OpenStreetMap contributors'
                }}
            ).addTo(map);

            const marker = L.marker([lat, lon]).addTo(map);

            marker.bindPopup(`
                <div class="popup-title">
                    📍 {SENSOR_NAME}
                </div>

                <div class="popup-row">
                    ⚗️ pH: {display_value(ph, 2)}
                </div>

                <div class="popup-row">
                    🧂 TDS: {display_value(tds, 1)} ppm
                </div>

                <div class="popup-row">
                    🔬 ORP: {display_value(orp, 0)} mV
                </div>

                <div class="popup-row">
                    📡 สถานะ: {sensor_state}
                </div>

                <div class="popup-row">
                    📌 {SENSOR_LAT:.6f}, {SENSOR_LON:.6f}
                </div>
            `).openPopup();
        </script>
    </body>
    </html>
    """

    components.html(
        map_html,
        height=490,
        scrolling=False,
    )

    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric("Latitude", f"{SENSOR_LAT:.6f}")

    with m2:
        st.metric("Longitude", f"{SENSOR_LON:.6f}")

    with m3:
        st.metric("Sensor Status", sensor_state)


# =========================================================
# TAB 2 — HISTORY
# =========================================================
with tab2:

    st.markdown("### 📈 ประวัติข้อมูลคุณภาพน้ำ")

    history_hours = st.selectbox(
        "ช่วงข้อมูล",
        options=[1, 6, 24, 168],
        format_func=lambda x: (
            "1 ชั่วโมง" if x == 1
            else "6 ชั่วโมง" if x == 6
            else "24 ชั่วโมง" if x == 24
            else "7 วัน"
        ),
        key="history_hours",
    )

    selected_rows = filter_history(
        history_rows,
        history_hours,
    )

    history_df = history_dataframe(selected_rows)

    if history_df.empty:
        st.info(
            "📭 ยังไม่มีข้อมูลประวัติจาก Sensor ใน Firebase"
        )
    else:
        st.dataframe(
            history_df.iloc[::-1],
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"แสดงข้อมูล {len(history_df):,} รายการ"
        )


# =========================================================
# TAB 3 — SENSOR LOCATION
# =========================================================
with tab3:

    st.markdown("### 📍 รายละเอียดจุดติดตั้ง Sensor")

    info1, info2 = st.columns([1.5, 1], gap="medium")

    with info1:
        location_map_html = f"""
        <html>
        <head>
            <link rel="stylesheet"
                  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
            </script>
            <style>
                html, body {{
                    margin:0;
                    padding:0;
                }}
                #map {{
                    height:450px;
                    width:100%;
                    border-radius:18px;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>

            <script>
                const map = L.map('map').setView(
                    [{SENSOR_LAT}, {SENSOR_LON}], 16
                );

                L.tileLayer(
                    'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
                    {{
                        maxZoom: 19,
                        attribution:
                        '&copy; OpenStreetMap contributors'
                    }}
                ).addTo(map);

                L.marker(
                    [{SENSOR_LAT}, {SENSOR_LON}]
                ).addTo(map)
                .bindPopup(
                    '<b>📍 {SENSOR_NAME}</b>'
                )
                .openPopup();
            </script>
        </body>
        </html>
        """

        components.html(
            location_map_html,
            height=470,
        )

    with info2:
        st.markdown(
            f"""
            <div class="panel">
                <div class="panel-title">
                    📡 {SENSOR_NAME}
                </div>

                <div style="
                    color:#64748b;
                    font-size:.85rem;
                    margin-top:12px;">
                    Water Quality Monitoring Station
                </div>

                <hr style="
                    border:0;
                    border-top:1px solid #dbe7ef;
                    margin:16px 0;">

                <div style="margin:10px 0;">
                    <b>⚗️ pH Sensor</b><br>
                    <span style="color:#64748b;">
                        ค่าปัจจุบัน: {display_value(ph, 2)} pH
                    </span>
                </div>

                <div style="margin:10px 0;">
                    <b>🧂 TDS Sensor</b><br>
                    <span style="color:#64748b;">
                        ค่าปัจจุบัน: {display_value(tds, 1)} ppm
                    </span>
                </div>

                <div style="margin:10px 0;">
                    <b>🔬 ORP Sensor</b><br>
                    <span style="color:#64748b;">
                        ค่าปัจจุบัน: {display_value(orp, 0)} mV
                    </span>
                </div>

                <div style="
                    margin-top:18px;
                    padding:12px;
                    border-radius:12px;
                    background:#f0fdf4;
                    border:1px solid #bbf7d0;
                    color:#166534;">
                    ● {sensor_state}
                </div>

                <div style="
                    margin-top:15px;
                    color:#475569;
                    font-size:.82rem;
                    line-height:1.8;">
                    <b>พิกัดจุดติดตั้ง</b><br>
                    Latitude: {SENSOR_LAT:.6f}<br>
                    Longitude: {SENSOR_LON:.6f}<br>
                    อัปเดตล่าสุด: {format_update_time(updated_at)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# FOOTER
# =========================================================
st.markdown(
    """
    <div style="
        margin-top:35px;
        padding-top:16px;
        border-top:1px solid #dbe7ef;
        text-align:center;
        color:#94a3b8;
        font-size:.75rem;">
        💧 Smart Water Quality Monitoring System
        · pH · TDS · ORP
    </div>
    """,
    unsafe_allow_html=True,
)
'''

# Inject the large Base64 data URI into the app.
app_code = app_code.replace(
    "__WATER_SENSOR_IMAGE_DATA_URI__",
    image_data_uri
)

app_path = Path("/mnt/data/app.py")
app_path.write_text(app_code, encoding="utf-8")

requirements = """streamlit
streamlit-autorefresh
pandas
requests
pytz
altair
"""
req_path = Path("/mnt/data/requirements.txt")
req_path.write_text(requirements, encoding="utf-8")

print(f"สร้าง FULL CODE: {app_path}")
print(f"สร้าง requirements: {req_path}")
print(f"Embedded image data URI: {len(image_data_uri):,} characters")
