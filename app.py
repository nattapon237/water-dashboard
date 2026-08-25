import streamlit as st
import pandas as pd
import requests
import datetime
import pytz
import folium
from streamlit_folium import st_folium

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(page_title="Smart Water Quality Monitoring", page_icon="💧", layout="wide")

# กรุณาเปลี่ยนเป็น URL ของ Firebase ของคุณ (ห้ามเปลี่ยนโครงสร้าง Path ตามข้อกำหนด)
FIREBASE_URL = "https://your-firebase-database-url.firebaseio.com"

# ==========================================
# BASE64 IMAGE
# ==========================================
# นำ Base64 ที่แนบมาใส่ตัวแปร
WATER_SENSOR_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAABagAAAQ+CAYAAAA6bNi7AAAQAElEQVR4AwV5A/V7v2z9e/u18c2/2P/Tz3s9X67X+c/n1+f99n+a/z87v/wL9sD2B0+3/6/v199z/6f/3/7c/b39wAAAABJRU5ErkJggg==" 
WATER_SENSOR_IMAGE = "data:image/png;base64," + WATER_SENSOR_IMAGE_BASE64

# ==========================================
# CSS LIGHT THEME
# ==========================================
st.markdown("""
<style>
/* พื้นหลังหลัก */
.stApp {
    background-color: #F5F7FA;
}

/* Typography */
h1, h2, h3, h4, p, div, span {
    color: #1E293B;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.secondary-text {
    color: #64748B;
    font-size: 14px;
}

/* Card Design */
.light-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
    padding: 24px;
    margin-bottom: 24px;
    text-align: center;
}

/* Header Design */
.header-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
    padding: 24px;
    margin-bottom: 24px;
    text-align: left;
}

/* Hero Image */
.hero-water-image {
    width: 100%;
    border-radius: 20px;
    overflow: hidden;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    box-shadow: 0 6px 20px rgba(15,23,42,0.08);
    margin-bottom: 24px;
}
.hero-water-image img {
    width: 100%;
    height: 360px;
    object-fit: cover;
    display: block;
}

/* Sensor Values */
.sensor-title {
    font-size: 18px;
    font-weight: 600;
    color: #64748B;
}
.sensor-value {
    font-size: 42px;
    font-weight: 700;
    color: #0284C7;
    margin: 10px 0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0;
}

/* Buttons */
.stButton>button {
    background-color: #0284C7 !important;
    color: #FFFFFF !important;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    width: 100%;
}
.stButton>button:hover {
    background-color: #0369A1 !important;
}

hr {
    border-color: #E2E8F0;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_firebase_status():
    try:
        response = requests.get(f"{FIREBASE_URL}/devices/uno-r4/status.json", timeout=5)
        if response.status_code == 200:
            return response.json(), True
    except:
        pass
    return None, False

def get_firebase_history():
    try:
        response = requests.get(f"{FIREBASE_URL}/devices/uno-r4/history.json", timeout=5)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return None

def check_ph(val):
    if val is None: return "--", "รอข้อมูล"
    if 6.5 <= val <= 8.5: return "🟢 ปกติ", "#16A34A"
    elif 6.0 <= val < 6.5 or 8.5 < val <= 9.0: return "🟡 เฝ้าระวัง", "#EAB308"
    else: return "🔴 ผิดปกติ", "#DC2626"

def check_tds(val):
    if val is None: return "--", "รอข้อมูล"
    if val <= 300: return "🟢 ปกติ", "#16A34A"
    elif 300 < val <= 500: return "🟡 เฝ้าระวัง", "#EAB308"
    else: return "🔴 ผิดปกติ", "#DC2626"

def check_orp(val):
    if val is None: return "--", "รอข้อมูล"
    if val >= 200: return "🟢 ปกติ", "#16A34A"
    elif 0 <= val < 200: return "🟡 เฝ้าระวัง", "#EAB308"
    else: return "🔴 ผิดปกติ", "#DC2626"

def get_overall_status(ph_stat, tds_stat, orp_stat):
    statuses = [ph_stat, tds_stat, orp_stat]
    if "🔴 ผิดปกติ" in statuses: return "🔴 ผิดปกติ", "#DC2626"
    if "🟡 เฝ้าระวัง" in statuses: return "🟡 เฝ้าระวัง", "#EAB308"
    if "รอข้อมูล" in statuses: return "รอข้อมูลจาก Sensor", "#64748B"
    return "🟢 ปกติ", "#16A34A"

# ==========================================
# FETCH DATA
# ==========================================
status_data, firebase_connected = get_firebase_status()
history_data = get_firebase_history()

ph_val = status_data.get('pH') if status_data else None
tds_val = status_data.get('TDS') if status_data else None
orp_val = status_data.get('ORP') if status_data else None

ph_label, ph_color = check_ph(ph_val)
tds_label, tds_color = check_tds(tds_val)
orp_label, orp_color = check_orp(orp_val)
overall_label, overall_color = get_overall_status(ph_label, tds_label, orp_label)

sensor_online = status_data is not None

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color: #0F172A; text-align: center;'>💧 WATER QUALITY SYSTEM</h3>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown(f"**สถานะ Firebase:** {'🟢 Connected' if firebase_connected else '🔴 Disconnected'}")
    st.markdown(f"**สถานะ Sensor:** {'🟢 Online' if sensor_online else '🔴 Offline'}")
    
    tz_thai = pytz.timezone('Asia/Bangkok')
    now = datetime.datetime.now(tz_thai).strftime("%d/%m/%Y %H:%M:%S")
    st.markdown(f"<div class='secondary-text'>เวลาไทย: {now}</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 รีเฟรชข้อมูล"):
        st.rerun()

# ==========================================
# MAIN DASHBOARD TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 ประวัติข้อมูล", "📍 จุดติดตั้ง Sensor"])

with tab1:
    # 1. Header
    st.markdown("""
        <div class="header-card">
            <h1 style='color: #0F172A; margin: 0;'>💧 ระบบตรวจวัดคุณภาพแหล่งน้ำอัจฉริยะ</h1>
            <p class="secondary-text" style='margin: 0; font-size: 18px;'>Smart Water Quality Monitoring System</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. รูปทุ่นตรวจวัดคุณภาพน้ำ (Hero Image)
    st.markdown(f"""
        <div class="hero-water-image">
            <img src="{WATER_SENSOR_IMAGE}" alt="ทุ่นตรวจวัดคุณภาพแหล่งน้ำอัจฉริยะ" />
        </div>
    """, unsafe_allow_html=True)

    # 4. Card ค่า pH / TDS / ORP
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="light-card">
            <div class="sensor-title">pH</div>
            <div class="sensor-value">{f"{ph_val:.2f} pH" if ph_val is not None else "--"}</div>
            <div style="color: {ph_color}; font-weight: 600;">สถานะ: {ph_label}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="light-card">
            <div class="sensor-title">TDS</div>
            <div class="sensor-value">{f"{tds_val:.0f} ppm" if tds_val is not None else "--"}</div>
            <div style="color: {tds_color}; font-weight: 600;">สถานะ: {tds_label}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="light-card">
            <div class="sensor-title">ORP</div>
            <div class="sensor-value">{f"{orp_val:.0f} mV" if orp_val is not None else "--"}</div>
            <div style="color: {orp_color}; font-weight: 600;">สถานะ: {orp_label}</div>
        </div>
        """, unsafe_allow_html=True)

    # 5. คุณภาพน้ำโดยรวม (Overall Status)
    st.markdown(f"""
        <div class="light-card">
            <h3 style="color: #0F172A; margin-top:0;">คุณภาพน้ำโดยรวม</h3>
            <h2 style="color: {overall_color}; margin-bottom:0;">{overall_label}</h2>
        </div>
    """, unsafe_allow_html=True)

    # 6. กราฟ pH / TDS / ORP (ใช้ st.line_chart แบบเดิมของ Streamlit)
    st.markdown("<h3 style='color: #0F172A;'>📈 กราฟแนวโน้มคุณภาพน้ำย้อนหลัง</h3>", unsafe_allow_html=True)
    if history_data:
        df = pd.DataFrame.from_dict(history_data, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        if 'pH' in df.columns:
            st.markdown("<h4 style='color: #1E293B;'>📈 ค่า pH ย้อนหลัง</h4>", unsafe_allow_html=True)
            st.line_chart(df[['pH']], color=["#0284C7"])
            
        if 'TDS' in df.columns:
            st.markdown("<h4 style='color: #1E293B;'>📈 ค่า TDS ย้อนหลัง (ppm)</h4>", unsafe_allow_html=True)
            st.line_chart(df[['TDS']], color=["#16A34A"])
            
        if 'ORP' in df.columns:
            st.markdown("<h4 style='color: #1E293B;'>📈 ค่า ORP ย้อนหลัง (mV)</h4>", unsafe_allow_html=True)
            st.line_chart(df[['ORP']], color=["#EAB308"])
            
    else:
        st.markdown("""
        <div class="light-card">
            <p style="color: #64748B; font-weight: bold; font-size: 18px;">ยังไม่มีข้อมูลจาก Sensor</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    # 8. ตารางประวัติข้อมูล
    st.markdown("<h3 style='color: #0F172A;'>📈 ประวัติข้อมูล</h3>", unsafe_allow_html=True)
    if history_data:
        df_hist = pd.DataFrame.from_dict(history_data, orient='index')
        df_hist.index.name = "Timestamp"
        df_hist = df_hist.reset_index()
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
    else:
        st.info("รอข้อมูลจาก Sensor")

with tab3:
    # 7. Map จุดติดตั้ง Sensor
    st.markdown("""
        <h3 style='color: #0F172A;'>📍 จุดติดตั้ง Sensor</h3>
        <p class="secondary-text">ตำแหน่งปัจจุบันของทุ่นตรวจวัดคุณภาพน้ำอัจฉริยะ</p>
    """, unsafe_allow_html=True)
    
    map_lat = 13.689108
    map_lon = 101.079153
    
    m = folium.Map(location=[map_lat, map_lon], zoom_start=15, tiles="OpenStreetMap")
    
    popup_html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1E293B; min-width: 150px;">
        <b>จุดตรวจวัดคุณภาพน้ำ 01</b><br>
        <hr style="margin: 5px 0; border-color: #E2E8F0;">
        pH: {ph_val if ph_val is not None else '--'}<br>
        TDS: {tds_val if tds_val is not None else '--'} ppm<br>
        ORP: {orp_val if orp_val is not None else '--'} mV<br>
        <br>
        สถานะ: <b>{'Online' if sensor_online else 'Offline'}</b>
    </div>
    """
    
    folium.Marker(
        [map_lat, map_lon],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip="📍 Sensor Station 01",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)
    
    st.markdown('<div class="light-card" style="padding: 10px;">', unsafe_allow_html=True)
    st_folium(m, height=400, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
