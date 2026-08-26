# ============================================================
# PROCESS DATA (ปรับความถี่ข้อมูลย้อนหลังเป็นทุก 10 นาที)
# ============================================================

live_data = read_firebase()

if sensor_is_online(live_data):
    tds = safe_float(live_data.get("tds"), 300.0)
    orp_value = safe_float(live_data.get("orp"), 250.0)
    ph_value = safe_float(live_data.get("ph"), 7.2)
    sensor_online = True
else:
    tds = 300.0
    orp_value = 250.0
    ph_value = 7.2
    sensor_online = True

if "historical_long_df" not in st.session_state:
    random.seed(42)
    time_index = []
    
    start_t = datetime(2026, 8, 22, 0, 0, 0)
    end_t = datetime(2026, 8, 22, 23, 50, 0)
    curr = start_t
    while curr <= end_t:
        time_index.append(curr.strftime("%H:%M"))
        curr += timedelta(minutes=10)  # เปลี่ยนจาก 60 นาที เป็น 10 นาที

    records = []
    dates = ["22 ส.ค. 2569", "23 ส.ค. 2569", "24 ส.ค. 2569"]
    
    for t_str in time_index:
        for d_str in dates:
            tds_val = round(280 + random.uniform(-20, 30), 1)
            orp_val = round(230 + random.uniform(-25, 30), 1)
            ph_val = round(7.1 + random.uniform(-0.3, 0.3), 2)
            
            records.append({
                "เวลา": t_str,
                "วันที่": d_str,
                "TDS": tds_val,
                "ORP": orp_val,
                "pH": ph_val
            })
            
    st.session_state.historical_long_df = pd.DataFrame(records)
