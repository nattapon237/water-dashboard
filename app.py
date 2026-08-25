import streamlit as st
import pandas as pd
import requests
import json
import time
import math
from datetime import datetime, timedelta
import pytz
import altair as alt

# ==========================================
# 0. CONFIGURATION & THRESHOLDS (ตั้งค่าเกณฑ์ต่างๆ)
# ==========================================
st.set_page_config(page_title="Smart Water Quality Monitoring", page_icon="💧", layout="wide")

TH_TZ = pytz.timezone('Asia/Bangkok')
FIREBASE_WEB_API_KEY = "AIzaSyAK_swKTrfzsH-_BKHLU40ilTWfyNBqNHA" # ใส่ API Key ของคุณ
FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"

# พิกัดจุดติดตั้งเซนเซอร์ (Latitude, Longitude)
SENSOR_LAT = 13.689108
SENSOR_LON = 101.079153

# ค่าเกณฑ์สำหรับประเมินคุณภาพน้ำ (สามารถปรับแก้ได้)
PH_MIN = 6.5
PH_MAX = 8.5
TDS_MAX = 1000  # ppm
ORP_MIN = 200   # mV
ORP_MAX = 800   # mV

# เวลา Timeout ของ Sensor (ถ้าไม่อัปเดตเกิน 5 นาที = Offline)
SENSOR_TIMEOUT_SECONDS = 300 

# ==========================================
# 1. CSS STYLING (Dark Theme & Glass Effect)
# ==========================================
st.markdown("""
<style>
    /* Dark Theme Background */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Glass Effect Card */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Titles and Headers */
    h1, h2, h3 { color: #38bdf8 !important; }
    .card-title { font-size: 1.2rem; font-weight: 600; color: #94a3b8; margin-bottom: 10px; }
    .card-value { font-size: 2.2rem; font-weight: 700; color: #f8fafc; }
    .card-unit { font-size: 1rem; color: #94a3b8; margin-left: 5px; }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .status-normal { background: rgba(52, 211, 153, 0.2); color: #34d399; border: 1px solid #34d399; }
    .status-warning { background: rgba(251, 191, 36, 0.2); color: #fbbf24; border: 1px solid #fbbf24; }
    .status-danger { background: rgba(248, 113, 113, 0.2); color: #f87171; border: 1px solid #f87171; }
    .status-offline { background: rgba(156, 163, 175, 0.2); color: #9ca3af; border: 1px solid #9ca3af; }

    hr { border-color: rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. FIREBASE FUNCTIONS
# ==========================================
@st.cache_data(ttl=3000)
def get_firebase_token():
    auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    try:
        res = requests.post(auth_url, json={"returnSecureToken": True}, timeout=5)
        if res.status_code == 200:
            return res.json().get("idToken")
    except Exception:
        pass
    return None

def read_current_status(id_token):
    """ อ่านค่าปัจจุบันจาก /status """
    if not id_token: return None
    url = f"{FIREBASE_DB_URL}/devices/uno-r4/status.json?auth={id_token}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def read_history_data(id_token):
    """ อ่านประวัติจาก /history """
    if not id_token: return None
    url = f"{FIREBASE_DB_URL}/devices/uno-r4/history.json?auth={id_token}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data:
                return data
    except Exception:
        pass
    return None


# ==========================================
# 3. WATER QUALITY EVALUATION
# ==========================================
def calculate_water_quality(ph, tds, orp):
    """ ประเมินสถานะน้ำแบบ Rule-based """
    if ph is None or tds is None or orp is None:
        return 0, "ไม่มีข้อมูล", "status-offline", ["รอข้อมูลจาก Sensor"], "กรุณารอระบบเชื่อมต่อกับ Sensor"

    reasons = []
    is_danger = False
    is_warning = False

    # ตรวจสอบ pH
    if ph < PH_MIN or ph > PH_MAX:
        reasons.append(f"ค่า pH ({ph:.2f}) อยู่นอกเกณฑ์ ({PH_MIN} - {PH_MAX})")
        is_danger = True

    # ตรวจสอบ TDS
    if tds > TDS_MAX:
        reasons.append(f"ค่า TDS ({tds:.0f} ppm) สูงเกินเกณฑ์มาตรฐาน (< {TDS_MAX} ppm)")
        is_warning = True
        if tds > TDS_MAX + 500: is_danger = True # ถ้าสูงกว่ามากให้เป็นอันตราย

    # ตรวจสอบ ORP
    if orp < ORP_MIN:
        reasons.append(f"ค่า ORP ({orp:.0f} mV) ต่ำกว่าเกณฑ์ (< {ORP_MIN} mV อาจมีแบคทีเรีย/สารอินทรีย์สูง)")
        is_warning = True

    # สรุปผล
    if is_danger:
        return 20, "🔴 ผิดปกติ", "status-danger", reasons, "งดการนำน้ำไปใช้ และตรวจสอบแหล่งกำเนิดมลพิษทันที"
    elif is_warning:
        return 60, "🟡 เฝ้าระวัง", "status-warning", reasons, "ควรติดตามคุณภาพน้ำอย่างใกล้ชิด อาจต้องกรองก่อนใช้งาน"
    else:
        return 100, "🟢 ปกติ", "status-normal", ["ทุกค่าพารามิเตอร์อยู่ในเกณฑ์ปกติ"], "คุณภาพน้ำดี สามารถนำไปใช้ในระบบได้"


# ==========================================
# 4. FETCH SENSOR DATA
# ==========================================
id_token = get_firebase_token()
current_data = read_current_status(id_token)
now_th = datetime.now(TH_TZ)
current_time_ts = int(time.time())

# ดึงค่าตัวแปร
ph_val, tds_val, orp_val, updated_at = None, None, None, None
sensor_online = False
last_update_str = "--"

if current_data:
    ph_val = current_data.get("ph")
    tds_val = current_data.get("tds")
    orp_val = current_data.get("orp")
    updated_at = current_data.get("updatedAt")
    
    if updated_at:
        # คำนวณเวลาเพื่อเช็ค Online / Offline
        dt_update = datetime.fromtimestamp(updated_at, TH_TZ)
        last_update_str = dt_update.strftime('%d/%m/%Y %H:%M:%S')
        if (current_time_ts - updated_at) <= SENSOR_TIMEOUT_SECONDS:
            sensor_online = True


# ==========================================
# 5. SIDEBAR (เมนูและสถานะ)
# ==========================================
st.sidebar.markdown("## 💧 WATER QUALITY SYSTEM")
st.sidebar.markdown("---")

st.sidebar.markdown("### สถานะระบบ")
if id_token:
    st.sidebar.markdown("🟢 Firebase: **Connected**")
else:
    st.sidebar.markdown("🔴 Firebase: **Disconnected**")

if sensor_online:
    st.sidebar.markdown("🟢 Sensor: **Online**")
    st.sidebar.markdown(f"🕒 อัปเดต: {last_update_str}")
else:
    st.sidebar.markdown("🔴 Sensor: **Offline**")
    st.sidebar.markdown(f"🕒 อัปเดตล่าสุด: {last_update_str}")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
    st.rerun()

# 6. ประเมินคุณภาพน้ำ (คำนวณ)
score, q_status, q_class, q_reasons, q_recommend = calculate_water_quality(ph_val, tds_val, orp_val)


# ==========================================
# 7. PAGE TABS 
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 ประวัติข้อมูล (History)", "📍 จุดติดตั้ง Sensor"])

# ---------------------------------------------------------
# TAB 1: DASHBOARD
# ---------------------------------------------------------
with tab1:
    st.markdown("<h1>💧 ระบบตรวจวัดคุณภาพแหล่งน้ำอัจฉริยะ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>ระบบตรวจวัดและติดตามคุณภาพน้ำด้วย pH, TDS และ ORP Sensor (Real-time)</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ก้อนแสดงผลสรุป (Overall Status)
    st.markdown(f"""
    <div class="glass-card">
        <div class="card-title">คุณภาพน้ำโดยรวม (Overall Water Quality)</div>
        <div style="font-size: 1.5rem; font-weight: bold; margin-bottom:10px;">
            <span class="status-badge {q_class}">{q_status}</span>
        </div>
        <div><b>สาเหตุ/ข้อสังเกต:</b> {', '.join(q_reasons)}</div>
        <div style="margin-top: 10px; color:#cbd5e1;"><b>คำแนะนำ:</b> {q_recommend}</div>
    </div>
    """, unsafe_allow_html=True)

    # 3 Cards สำหรับ pH, TDS, ORP
    col1, col2, col3 = st.columns(3)
    
    def render_sensor_card(icon, title, val, unit, min_val, max_val, format_str="{:.2f}"):
        if val is None:
            display_val = "--"
            s_class = "status-offline"
            s_text = "Offline"
        else:
            display_val = format_str.format(val)
            if min_val <= val <= max_val:
                s_class = "status-normal"
                s_text = "ปกติ"
            else:
                s_class = "status-danger"
                s_text = "ผิดปกติ"
                
        return f"""
        <div class="glass-card" style="text-align:center;">
            <div class="card-title">{icon} {title}</div>
            <div class="card-value">{display_val} <span class="card-unit">{unit}</span></div>
            <div style="margin-top:15px;"><span class="status-badge {s_class}">{s_text}</span></div>
        </div>
        """

    with col1:
        st.markdown(render_sensor_card("⚗️", "pH", ph_val, "pH", PH_MIN, PH_MAX, "{:.2f}"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_sensor_card("🧂", "TDS", tds_val, "ppm", 0, TDS_MAX, "{:.0f}"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_sensor_card("🔬", "ORP", orp_val, "mV", ORP_MIN, 1000, "{:.0f}"), unsafe_allow_html=True)

    # Map المصغرة في Dashboard
    st.markdown("### 📍 ตำแหน่งตรวจวัดปัจจุบัน")
    map_df = pd.DataFrame({'lat': [SENSOR_LAT], 'lon': [SENSOR_LON]})
    st.map(map_df, zoom=12, use_container_width=True)


# ---------------------------------------------------------
# TAB 2: HISTORY (ประวัติย้อนหลัง และ กราฟของจริง)
# ---------------------------------------------------------
with tab2:
    st.markdown("<h2>📈 ประวัติข้อมูลคุณภาพน้ำย้อนหลัง</h2>", unsafe_allow_html=True)
    
    history_data = read_history_data(id_token)
    
    if history_data:
        # แปลง Data จาก Firebase dict ให้เป็น Pandas DataFrame
        records = []
        for key, val in history_data.items():
            if isinstance(val, dict):
                row = val.copy()
                # ถ้า key คือ timestamp หรือใช้ใน row 
                ts = row.get("timestamp") or int(key) if key.isdigit() else None
                if ts:
                    dt = datetime.fromtimestamp(ts, TH_TZ)
                    row['datetime'] = dt
                    records.append(row)
        
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.sort_values('datetime').reset_index(drop=True)
            
            # ตัวกรองเวลา
            time_filter = st.selectbox("⏳ เลือกช่วงเวลาดูประวัติ", ["1 ชั่วโมงที่ผ่านมา", "6 ชั่วโมงที่ผ่านมา", "24 ชั่วโมงที่ผ่านมา", "7 วันที่ผ่านมา"])
            
            now = datetime.now(TH_TZ)
            if time_filter == "1 ชั่วโมงที่ผ่านมา":
                df_filtered = df[df['datetime'] >= now - timedelta(hours=1)]
            elif time_filter == "6 ชั่วโมงที่ผ่านมา":
                df_filtered = df[df['datetime'] >= now - timedelta(hours=6)]
            elif time_filter == "24 ชั่วโมงที่ผ่านมา":
                df_filtered = df[df['datetime'] >= now - timedelta(hours=24)]
            else:
                df_filtered = df[df['datetime'] >= now - timedelta(days=7)]

            if not df_filtered.empty:
                # ----------------- กราฟ pH -----------------
                st.markdown('<div class="glass-card"><div class="card-title">📈 กราฟค่า pH ย้อนหลัง</div>', unsafe_allow_html=True)
                chart_ph = alt.Chart(df_filtered).mark_line(point=True, color="#38bdf8", strokeWidth=2).encode(
                    x=alt.X('datetime:T', title='เวลา (Time)'),
                    y=alt.Y('ph:Q', title='pH', scale=alt.Scale(domain=[0, 14])),
                    tooltip=['datetime:T', 'ph:Q']
                ).interactive().properties(height=250)
                st.altair_chart(chart_ph, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # ----------------- กราฟ TDS -----------------
                st.markdown('<div class="glass-card"><div class="card-title">📈 กราฟค่า TDS ย้อนหลัง (ppm)</div>', unsafe_allow_html=True)
                chart_tds = alt.Chart(df_filtered).mark_line(point=True, color="#34d399", strokeWidth=2).encode(
                    x=alt.X('datetime:T', title='เวลา (Time)'),
                    y=alt.Y('tds:Q', title='TDS (ppm)'),
                    tooltip=['datetime:T', 'tds:Q']
                ).interactive().properties(height=250)
                st.altair_chart(chart_tds, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # ----------------- กราฟ ORP -----------------
                st.markdown('<div class="glass-card"><div class="card-title">📈 กราฟค่า ORP ย้อนหลัง (mV)</div>', unsafe_allow_html=True)
                chart_orp = alt.Chart(df_filtered).mark_line(point=True, color="#fbbf24", strokeWidth=2).encode(
                    x=alt.X('datetime:T', title='เวลา (Time)'),
                    y=alt.Y('orp:Q', title='ORP (mV)'),
                    tooltip=['datetime:T', 'orp:Q']
                ).interactive().properties(height=250)
                st.altair_chart(chart_orp, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # ----------------- ตาราง -----------------
                st.markdown("### 📋 ตารางประวัติข้อมูล")
                df_show = df_filtered[['datetime', 'ph', 'tds', 'orp']].copy()
                df_show['datetime'] = df_show['datetime'].dt.strftime('%d/%m/%Y %H:%M:%S')
                df_show.columns = ['เวลา', 'pH', 'TDS (ppm)', 'ORP (mV)']
                st.dataframe(df_show, use_container_width=True)

            else:
                st.info("ℹ️ ยังไม่มีข้อมูลประวัติจาก Sensor ในช่วงเวลาที่เลือก")
        else:
            st.info("ℹ️ รูปแบบข้อมูลประวัติใน Firebase ไม่ถูกต้อง หรือว่างเปล่า")
    else:
        st.info("ℹ️ ยังไม่มีข้อมูลประวัติจาก Sensor (ไม่พบ path: /devices/uno-r4/history/ ใน Firebase)")


# ---------------------------------------------------------
# TAB 3: SENSOR LOCATION 
# ---------------------------------------------------------
with tab3:
    st.markdown("<h2>📍 จุดติดตั้ง Sensor</h2>", unsafe_allow_html=True)
    
    col_info, col_map = st.columns([1, 2])
    
    with col_info:
        st.markdown(f"""
        <div class="glass-card">
            <h3>สถานี: Sensor Station 01</h3>
            <p style="color:#94a3b8;">ประเภท: Water Quality Monitoring Station</p>
            <hr>
            <p><b>เซนเซอร์ที่ติดตั้ง:</b><br>
            ⚗️ pH Sensor<br>
            🧂 TDS Sensor<br>
            🔬 ORP Sensor</p>
            <hr>
            <p><b>พิกัด (Lat, Lon):</b><br>
            {SENSOR_LAT}, {SENSOR_LON}</p>
            <hr>
            <p><b>สถานะปัจจุบัน:</b><br>
            {'<span class="status-badge status-normal">🟢 Online</span>' if sensor_online else '<span class="status-badge status-offline">🔴 Offline</span>'}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_map:
        st.map(map_df, zoom=14, use_container_width=True)


# ==========================================
# 8. AUTO REFRESH LOGIC (ทุกๆ 30 วินาที)
# ==========================================
# ใช้ st_autorefresh ได้ถ้าลง library เพิ่ม แต่แบบไม่ต้องลงเพิ่มคือการสั่ง time.sleep แล้ว rerun
# คำเตือน: loop นี้ทำงานที่ท้ายสุดของ script
time.sleep(30)
st.rerun()
