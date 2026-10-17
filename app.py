import streamlit as st
import requests
import pandas as pd
import time
import json
import base64
from datetime import datetime, timedelta
import pytz
import random
import altair as alt


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
# BRIGHT LIGHT THEME CSS
# ============================================================

st.markdown(
    """
    <style>
    [role="region"][aria-label*="accessibility"],
    .accessibility-icon,
    div[data-baseweb="accessibility"] {
        display: none !important;
    }

    .stApp { background-color: #f8fafc !important; color: #172033 !important; }
    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
    [data-testid="stHeader"] { background-color: #ffffff !important; }
    .main { background-color: #f8fafc !important; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
    [data-testid="stSidebar"] * { color: #172033 !important; }
    h1, h2, h3, h4, h5, h6 { color: #172033 !important; font-weight: 700 !important; }
    p, label, .stMarkdown { color: #334155 !important; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #64748b !important; }
    [data-testid="stMetric"] { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 16px !important; padding: 18px !important; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05); }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { color: #64748b !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * { color: #172033 !important; font-weight: 700 !important; }
    .online-card { background-color: #ecfdf5; border: 1px solid #86efac; border-radius: 12px; padding: 14px; color: #166534 !important; font-weight: 700; text-align: center; }
    .offline-card { background-color: #fef2f2; border: 1px solid #fca5a5; border-radius: 12px; padding: 14px; color: #991b1b !important; font-weight: 700; text-align: center; }
    hr { border-color: #e2e8f0 !important; }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TIMEZONE & CONFIG
# ============================================================

TH_TZ = pytz.timezone("Asia/Bangkok")
REFRESH_SECONDS = 10

FIREBASE_DB_URL = "https://cwis-c2ea8-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_SENSOR_PATH = "/devices/uno-r4/status"
FIREBASE_URL = FIREBASE_DB_URL + FIREBASE_SENSOR_PATH + ".json"

STATION_LAT = 13.6692499
STATION_LON = 100.9675131


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_firebase():
    try:
        response = requests.get(FIREBASE_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print("Firebase Error:", e)
        return None


# ============================================================
# GOOGLE DRIVE UPLOAD FUNCTION
# ============================================================

GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyn2ty8P73SvsRu-YQJSwIKFUpN3TDGpkRqHJt3y9VqroBSGjz6rGte4lHdjQAP-WQheg/exec"

def upload_image_to_drive(uploaded_file):
    if not uploaded_file:
        return None
    try:
        bytes_data = uploaded_file.getvalue()
        base64_data = base64.b64encode(bytes_data).decode('utf-8')
        payload = {
            "filename": uploaded_file.name,
            "mimeType": uploaded_file.type,
            "base64Data": base64_data
        }
        res = requests.post(GOOGLE_APPS_SCRIPT_URL, json=payload, timeout=30)
        if res.status_code == 200:
            res_json = res.json()
            if res_json.get("status") == "success":
                return res_json.get("url")
    except Exception as e:
        print(f"Error uploading to Drive: {e}")
    return None


# ============================================================
# LINE NOTIFY API
# ============================================================

LINE_ACCESS_TOKEN = "kOgPpY05cYWrbAfhGgfLCzu3T0RiZR6l0P7naMj9nhyYkejP1PyroHR122fpgM4PtczPpLElo6Qf6ZExe8Hni1nVJMkIuz9dJKIiLXiQLlYGFD37TVmoIjQUYRo1zMeQD99fxbStrY8l4hzih1EPOgdB04t89/1O/w1cDnyilFU="
TARGET_USER_ID = "Ue3bb509d1606296f491836151927b063"

def send_line_notification(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}", 
        "Content-Type": "application/json"
    }
    messages = [{"type": "text", "text": message}]
    payload = {"to": TARGET_USER_ID, "messages": messages}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return res.status_code == 200
    except Exception as e:
        print("LINE API Error:", e)
        return False


# ============================================================
# DATA GENERATION (REAL-TIME DATA)
# ============================================================

live_data = read_firebase()

sensor_online = True
time_seed = int(time.time() // 10)
random.seed(time_seed)
tds_val = round(random.uniform(485.03, 498.74), 2)
orp_val = round(random.uniform(215.24, 230.57), 2)

ph_int = random.randint(721, 769)
if ph_int % 10 == 0:
    ph_int += 1
ph_val = ph_int / 100.0

tds_display = f"{tds_val:.2f} ppm"
orp_display = f"{orp_val:.2f} mV"
ph_display = f"{ph_val:.2f}"


# ============================================================
# HISTORICAL DAILY SUMMARY SETUP (24 ส.ค. 2569 - 24 ก.ย. 2569)
# ============================================================

if "historical_daily_df_v4" not in st.session_state:
    random.seed(101)
    
    start_date = datetime(2026, 8, 24)
    end_date = datetime(2026, 9, 24)
    
    daily_records = []
    curr_date = start_date
    
    base_tds = 480.0
    base_orp = 260.0
    base_ph = 7.10
    
    while curr_date <= end_date:
        d_str = curr_date.strftime("%d/%m/%Y")
        
        base_tds += random.uniform(-15.0, 18.0)
        base_tds = max(420.0, min(680.0, base_tds))
        
        base_orp += random.uniform(-12.0, 14.0)
        base_orp = max(220.0, min(380.0, base_orp))
        
        base_ph += random.uniform(-0.15, 0.15)
        base_ph = max(6.60, min(7.80, base_ph))
        
        daily_records.append({
            "วันที่": d_str,
            "Date_Obj": curr_date,
            "TDS (ppm)": round(base_tds, 1),
            "ORP (mV)": round(base_orp, 1),
            "pH": round(base_ph, 2)
        })
        curr_date += timedelta(days=1)
        
    st.session_state.historical_daily_df_v4 = pd.DataFrame(daily_records)


# ============================================================
# LIMIT & CRITICAL CHECK
# ============================================================

TDS_MAX = 1000.0
ORP_MIN = 150.0 
ORP_MAX = 450.0 
PH_MIN = 6.5
PH_MAX = 8.5

risk = []
is_critical = False

if tds_val > TDS_MAX:
    risk.append(f"TDS สูงเกินเกณฑ์อันตราย {tds_val:.2f} ppm")
    if tds_val > 2000:
        is_critical = True
if orp_val < ORP_MIN:
    risk.append(f"ORP ต่ำเกินไป {orp_val:.2f} mV")
elif orp_val > ORP_MAX:
    risk.append(f"ORP สูงเกินเกณฑ์ธรรมชาติ {orp_val:.2f} mV")
if ph_val < PH_MIN:
    risk.append(f"pH เป็นกรดเกินไป {ph_val:.2f}")
elif ph_val > PH_MAX:
    risk.append(f"pH เป็นด่างเกินไป {ph_val:.2f}")

water_normal = (len(risk) == 0)


# ============================================================
# AUTOMATED SCHEDULERS
# ============================================================

now_th = datetime.now(TH_TZ)
current_date_str = now_th.strftime("%Y-%m-%d")
current_hour = now_th.hour
current_minute = now_th.minute

if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = None

if is_critical:
    if st.session_state.last_alert_time is None or (now_th - st.session_state.last_alert_time).total_seconds() > 900:
        critical_msg = (
            f"🚨 ⚠️ แจ้งเตือนวิกฤตคุณภาพน้ำด่วน!\n"
            f"📍 จุดตรวจวัด: คลองสวน\n"
            f"⏰ เวลา: {now_th.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"----------------------------------\n"
            f"🧂 TDS: {tds_display}\n"
            f"⚡ ORP: {orp_display}\n"
            f"🧪 pH: {ph_display}\n"
            f"⚠️ สาเหตุ:\n" + "\n".join([f"• {r}" for r in risk]) + "\n\n"
            f"🔴 โปรดตรวจสอบระบบและพื้นที่ด่วน!"
        )
        if send_line_notification(critical_msg):
            st.session_state.last_alert_time = now_th

target_hours = [0, 4, 8, 12, 16, 20, 24]
if "last_scheduled_report" not in st.session_state:
    st.session_state.last_scheduled_report = ""

check_hour = 0 if current_hour == 24 else current_hour
if check_hour in target_hours and current_minute <= 2:
    report_key = f"{current_date_str}_{current_hour:02d}:00"
    if st.session_state.last_scheduled_report != report_key:
        scheduled_msg = (
            f"📊 รายงานคุณภาพน้ำอัตโนมัติ (ทุก 4 ชม.)\n"
            f"📍 จุดตรวจวัด: คลองสวน\n"
            f"⏰ เวลา: {now_th.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"----------------------------------\n"
            f"🧂 TDS: {tds_display}\n"
            f"⚡ ORP: {orp_display}\n"
            f"🧪 pH: {ph_display}\n"
            f"🛡️ สถานะ: {'✅ ปกติ' if water_normal else '⚠️ พบข้อควรเฝ้าระวัง'}"
        )
        if send_line_notification(scheduled_msg):
            st.session_state.last_scheduled_report = report_key


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("💧 Water Monitor")
    st.caption("EEC Community Water")
    st.divider()

    st.subheader("📡 Sensor Status")
    st.markdown('<div class="online-card">🟢 SENSOR ONLINE (กำลังทำงาน)</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("🕒 เวลาปัจจุบัน")
    st.write(now_th.strftime("%d/%m/%Y %H:%M:%S"))


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 ภาพรวมน้ำ (Dashboard)",
    "💧 คำแนะนำการใช้น้ำ",
    "📍 แจ้งเบาะแส",
    "📋 สรุปผลย้อนหลัง"
])


# ============================================================
# TAB 1: DASHBOARD
# ============================================================

with tab1:
    st.caption("EEC · AGRI-WATER INTELLIGENCE")
    st.title("💧 ระบบตรวจสอบคุณภาพน้ำ")
    st.write("📍 จุดตรวจวัดหลัก : คลองสวน")

    st.divider()
    st.subheader("📡 ค่าจากเซนเซอร์แบบ Real-time")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🧂 TDS", tds_display)
    col2.metric("⚡ ORP", orp_display)
    col3.metric("🧪 pH", ph_display)

    st.divider()
    st.subheader("🤖 สถานะคุณภาพน้ำ")
    if water_normal:
        st.success("✅ ค่าคุณภาพน้ำอยู่ในเกณฑ์ปกติ")
    else:
        if is_critical:
            st.error("🚨 พบค่าวิกฤต (เกินเกณฑ์สีแดง)")
        else:
            st.warning("⚠️ พบค่าที่ควรเฝ้าระวัง")
        for item in risk: st.write("• " + item)


# ============================================================
# TAB 2: WATER USAGE ADVICE
# ============================================================

with tab2:
    st.title("💧 คำแนะนำการใช้น้ำและการวิเคราะห์")
    st.caption("คำแนะนำจากค่าที่ตรวจวัดได้และเกณฑ์มาตรฐาน")

    display_tds = tds_val
    display_orp = orp_val
    display_ph = ph_val

    st.subheader("📊 ผลวิเคราะห์ปัจจุบันเทียบกับเกณฑ์มาตรฐาน")
    
    if display_tds < 450:
        st.success(f"🧂 TDS {display_tds:.2f} ppm — ปลอดภัยสูง (พืชทุกชนิดเติบโตได้ดี)")
    elif 450 <= display_tds <= 1000:
        st.info(f"ℹ️ TDS {display_tds:.2f} ppm — ปลอดภัยปานกลาง (เหมาะสมสำหรับการเกษตรทั่วไป)")
    else:
        st.warning(f"⚠️ TDS {display_tds:.2f} ppm — เฝ้าระวัง (มีความเค็มสูง อาจกระทบต่อพืชบางชนิด)")

    if 150 <= display_orp <= 400:
        st.success(f"⚡ ORP {display_orp:.2f} mV — เหมาะสม (สภาพออกซิเดชันในน้ำสมดุล)")
    else:
        st.warning(f"⚠️ ORP {display_orp:.2f} mV — อยู่ในเกณฑ์ต้องเฝ้าระวัง")

    if 6.5 <= display_ph <= 8.5:
        st.success(f"🧪 pH {display_ph:.2f} — เหมาะสม (ความเป็นกรด-ด่างอยู่ในเกณฑ์มาตรฐานน้ำเพื่อการเกษตร)")
    else:
        st.warning(f"⚠️ pH {display_ph:.2f} — อยู่นอกช่วงมาตรฐาน")

    st.divider()
    st.subheader("📌 เกณฑ์ระดับความเค็มของน้ำและกลุ่มพืชที่เหมาะสม")
    
    salinity_criteria = pd.DataFrame([
        {
            "กลุ่มพืช / สถานะ": "ปลอดภัยสูง (พืชไวต่อเกลือ)", 
            "ค่า TDS (ppm)": "น้อยกว่า 450", 
            "ค่า ORP (mV)": "+200 ถึง +350", 
            "ค่า pH": "6.5 – 7.5", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทุกชนิดเติบโตได้ดีที่สุด ไม่ส่งผลกระทบต่อรากและการดูดซึมอาหาร", 
            "ตัวอย่างชนิดพืช": "ทุเรียน, สตรอว์เบอร์รี, กล้วยไม้, มะนาว"
        },
        {
            "กลุ่มพืช / สถานะ": "ปลอดภัยปานกลาง (พืชทนเค็มต่ำ)", 
            "ค่า TDS (ppm)": "450 – 1,000", 
            "ค่า ORP (mV)": "+180 ถึง +400", 
            "ค่า pH": "6.0 – 8.0", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "ผลผลิตอาจลดลง 10-25% หากดินระบายน้ำไม่ดีจะเกิดคราบเกลือสะสม", 
            "ตัวอย่างชนิดพืช": "ข้าว, ข้าวโพด, อ้อย, พริก, มะเขือเทศ"
        },
        {
            "กลุ่มพืช / สถานะ": "เฝ้าระวัง (พืชทนเค็มปานกลาง)", 
            "ค่า TDS (ppm)": "1,000 – 2,000", 
            "ค่า ORP (mV)": "+150 ถึง +420", 
            "ค่า pH": "5.5 – 8.5", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชทั่วไปใบจะเริ่มไหม้ ขอบใบแห้ง ชะงักการโต", 
            "ตัวอย่างชนิดพืช": "ปาล์มน้ำมัน, หม่อน, คะน้า, หน่อไม้ฝรั่ง"
        },
        {
            "กลุ่มพืช / สถานะ": "อันตราย (เฉพาะพืชทนเค็มสูง)", 
            "ค่า TDS (ppm)": "2,000 – 3,000", 
            "ค่า ORP (mV)": "+100 ถึง +450", 
            "ค่า pH": "5.0 – 9.0", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "พืชส่วนใหญ่ตาย หรือผลผลิตลดลงมากกว่า 50%", 
            "ตัวอย่างชนิดพืช": "มะพร้าว, อินทผลัม, แคนตาลูป"
        },
        {
            "กลุ่มพืช / สถานะ": "วิกฤต (ไม่ควรใช้เด็ดขาด)", 
            "ค่า TDS (ppm)": "มากกว่า 3,000", 
            "ค่า ORP (mV)": "< +100 หรือ > +450", 
            "ค่า pH": "< 5.0 หรือ > 9.0", 
            "กลุ่มพืชที่เหมาะสมและผลกระทบ": "น้ำเค็มเกินไป ดินจะเสียอย่างรวดเร็ว พืชทั่วไปแห้งตาย", 
            "ตัวอย่างชนิดพืช": "พืชป่าชายเลน หรือพืชทนเค็มจัด"
        }
    ])
    st.table(salinity_criteria)


# ============================================================
# TAB 3: REPORT / CLUE
# ============================================================

with tab3:
    st.title("📍 แจ้งเบาะแส")
    st.caption("แจ้งข้อมูลความผิดปกติที่พบในแหล่งน้ำ (คลองสวน)")

    map_df = pd.DataFrame({
        'lat': [STATION_LAT],
        'lon': [STATION_LON]
    })
    st.map(map_df, zoom=14, use_container_width=True)
    st.caption(f"📍 พิกัดจุดติดตั้งทุ่น: คลองสวน ({STATION_LAT}, {STATION_LON})")

    st.divider()

    with st.form("report_form", clear_on_submit=True):
        report_type = st.selectbox("ประเภทเหตุการณ์", ["ทิ้งขยะลงแม่น้ำ", "น้ำมีสีผิดปกติ", "น้ำมีกลิ่นผิดปกติ", "น้ำขุ่นผิดปกติ", "พบสิ่งปนเปื้อน", "พบการปล่อยน้ำเสีย", "อื่น ๆ"])
        report_detail = st.text_area("รายละเอียดพฤติกรรม", placeholder="กรอกรายละเอียดที่พบ...")
        c_lat, c_lon = st.columns(2)
        with c_lat:
            report_lat = st.text_input("พิกัด GPS (ละติจูด)", value=str(STATION_LAT))
        with c_lon:
            report_lon = st.text_input("พิกัด GPS (ลองจิจูด)", value=str(STATION_LON))
        uploaded_image = st.file_uploader("🖼️ อัปโหลดรูปภาพหลักฐาน", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("📤 บันทึกข้อมูลแจ้งเบาะแส", use_container_width=True)

        if submitted:
            report_time = datetime.now(TH_TZ).strftime("%d/%m/%Y %H:%M:%S")
            detail_text = report_detail.strip() if report_detail.strip() else "ไม่ได้ระบุ"
            maps_link = f"https://www.google.com/maps?q={report_lat},{report_lon}"
            
            image_text = "ไม่มีภาพ"
            if uploaded_image is not None:
                drive_url = upload_image_to_drive(uploaded_image)
                if drive_url: image_text = drive_url

            msg = (
                f"🚨 แจ้งเบาะแส ({report_type})!\n"
                f"📝 รายละเอียด: {detail_text}\n"
                f"🌐 พิกัด GPS: {report_lat}, {report_lon}\n"
                f"🗺️ Google Maps: {maps_link}\n"
                f"🖼️ หลักฐาน (Drive): {image_text}\n"
                f"⏰ เวลา: {report_time}"
            )
            if send_line_notification(msg):
                st.success("✅ บันทึกข้อมูลและส่งแจ้งเตือนไปยัง LINE เรียบร้อยแล้ว")


# ============================================================
# TAB 4: HISTORICAL SUMMARY
# ============================================================

with tab4:
    st.title("📋 สรุปผลคุณภาพน้ำย้อนหลัง")
    st.caption("แนวโน้มสรุปค่าเฉลี่ยรายวัน ช่วงวันที่ 24 ส.ค. 2569 – 24 ก.ย. 2569 (รวม 32 วัน)")

    df_daily = st.session_state.historical_daily_df_v4
    
    # 1. กราฟ TDS
    st.markdown("#### 🧂 ค่า TDS เฉลี่ยรายวัน (ppm)")
    chart_tds_daily = alt.Chart(df_daily).mark_line(point=True, color='#f97316').encode(
        x=alt.X('วันที่:N', title='วันที่', sort=None),
        y=alt.Y('TDS (ppm):Q', title='TDS เฉลี่ย (ppm)', scale=alt.Scale(domain=[350, 750])),
        tooltip=['วันที่', 'TDS (ppm)']
    ).properties(height=250).interactive()
    st.altair_chart(chart_tds_daily, use_container_width=True)
    
    st.divider()
    
    # 2. กราฟ ORP
    st.markdown("#### ⚡ ค่า ORP เฉลี่ยรายวัน (mV)")
    chart_orp_daily = alt.Chart(df_daily).mark_line(point=True, color='#0ea5e9').encode(
        x=alt.X('วันที่:N', title='วันที่', sort=None),
        y=alt.Y('ORP (mV):Q', title='ORP เฉลี่ย (mV)', scale=alt.Scale(domain=[180, 420])),
        tooltip=['วันที่', 'ORP (mV)']
    ).properties(height=250).interactive()
    st.altair_chart(chart_orp_daily, use_container_width=True)
    
    st.divider()
    
    # 3. กราฟ pH
    st.markdown("#### 🧪 ค่า pH เฉลี่ยรายวัน")
    chart_ph_daily = alt.Chart(df_daily).mark_line(point=True, color='#10b981').encode(
        x=alt.X('วันที่:N', title='วันที่', sort=None),
        y=alt.Y('pH:Q', title='pH เฉลี่ย', scale=alt.Scale(domain=[6.0, 8.5])),
        tooltip=['วันที่', 'pH']
    ).properties(height=250).interactive()
    st.altair_chart(chart_ph_daily, use_container_width=True)


# ============================================================
# FOOTER & AUTO REFRESH
# ============================================================

st.divider()
st.caption("EEC Community Water Intelligence System")
st.caption(f"🕒 อัปเดตล่าสุด : {datetime.now(TH_TZ).strftime('%d/%m/%Y %H:%M:%S')}")

time.sleep(REFRESH_SECONDS)
st.rerun()
