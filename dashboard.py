import streamlit as st
import pandas as pd
import os
import glob
import base64

st.set_page_config(page_title="Kiosk (CUSS) Dashboard", page_icon="✈️", layout="wide")

# Custom CSS for Modern UI
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #f4f7f6;
    }
    /* Metric styling */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    /* Kiosk Card */
    .kiosk-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        border-top: 5px solid #0052cc;
        transition: transform 0.2s;
    }
    .kiosk-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .kiosk-title {
        color: #172b4d;
        font-weight: 800;
        margin-bottom: 15px;
        font-size: 1.3rem;
        text-align: center;
    }
    .kiosk-stats {
        margin-top: 15px;
        font-size: 0.95rem;
    }
    .kiosk-stats-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px dashed #eaecf0;
        color: #42526e;
    }
    .app-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        padding: 10px;
        background: #f4f5f7;
        border-radius: 10px;
        border: 1px solid #dfe1e6;
    }
    .app-logo {
        width: 35px;
        height: 35px;
        object-fit: contain;
        margin-right: 12px;
    }
    .app-info {
        flex-grow: 1;
    }
    .app-name {
        font-weight: 700;
        color: #172b4d;
        font-size: 0.95rem;
    }
    .app-tx {
        font-size: 0.8rem;
        color: #5e6c84;
    }
</style>
""", unsafe_allow_html=True)

AIRPORT_NAMES = {
    "UBP": "อุบลราชธานี (Ubon Ratchathani)",
    "KKC": "ขอนแก่น (Khon Kaen)",
    "UTH": "อุดรธานี (Udon Thani)",
    "KBV": "กระบี่ (Krabi)",
    "TST": "ตรัง (Trang)",
    "NST": "นครศรีธรรมราช (Nakhon Si Thammarat)",
    "URT": "สุราษฎร์ธานี (Surat Thani)",
    "PHS": "พิษณุโลก (Phitsanulok)"
}

AIRLINE_MAP = {
    "AK_AIRASIACUSSCLIENT": {"icao": "FD", "name": "AirAsia", "logo": "FD.png"},
    "SL_SABREKIOSK": {"icao": "SL", "name": "Thai Lion Air", "logo": "SL.png"},
    "TG_CKC": {"icao": "TG", "name": "Thai Airways", "logo": "TG.png"},
    "VZ_RES2KIOSK_PROD_VZ": {"icao": "VZ", "name": "Thai VietJet Air", "logo": "VZ.png"}
}

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return ""
    
# Pre-load airline logos
IMAGE_DIR = "รูปใช้งานใน dashboard"
LOGO_B64 = {}
for app, info in AIRLINE_MAP.items():
    logo_path = os.path.join(IMAGE_DIR, info["logo"])
    LOGO_B64[app] = get_image_base64(logo_path)

@st.cache_data
def load_data():
    csv_files = list(set(glob.glob("*.csv")))
    df_list = []
    
    for file in csv_files:
        if file.lower() == "requirements.txt":
            continue
            
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                skip_rows = 0
                for i, line in enumerate(lines):
                    if line.startswith("Devices,Applications"):
                        skip_rows = i
                        break
            
            df = pd.read_csv(file, skiprows=skip_rows)
            if 'Devices' in df.columns:
                df = df.dropna(subset=['Devices'])
                df_list.append(df)
        except Exception as e:
            st.warning(f"Could not read {file}: {e}")
            
    if not df_list:
        return pd.DataFrame()
        
    final_df = pd.concat(df_list, ignore_index=True)
    numeric_cols = ['Transactions', 'BP Prints', 'Bag Tag Prints', 'Passport Scans', 'BP Scans']
    for col in numeric_cols:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
            
    return final_df

def parse_device(device_code):
    if not isinstance(device_code, str):
        return device_code, "UNK", "00"
    
    airport_code = device_code[:3].upper()
    import re
    match = re.search(r'\d+$', device_code)
    machine_num = match.group() if match else "00"
    if len(machine_num) == 1:
        machine_num = "0" + machine_num
        
    display_name = f"{airport_code} CUSS {machine_num}"
    return display_name, airport_code, machine_num

def main():
    st.title("✈️ Airport Kiosk (CUSS) Dashboard")
    st.markdown("ระบบแสดงข้อมูลการใช้งานอุปกรณ์ CUSS ของท่าอากาศยานต่างๆ (Modern Dashboard)")
    
    df = load_data()
    
    if df.empty:
        st.warning("⚠️ ไม่พบข้อมูล กรุณาตรวจสอบไฟล์ CSV ในโฟลเดอร์")
        st.stop()

    df[['Display_Name', 'Airport', 'Machine_No']] = df.apply(
        lambda row: pd.Series(parse_device(row['Devices'])), axis=1
    )
    df['Airport_Name'] = df['Airport'].map(lambda x: AIRPORT_NAMES.get(x, x))
    df['Airline_Name'] = df['Applications'].map(lambda x: AIRLINE_MAP.get(x, {"name": x})["name"])
    
    st.sidebar.header("🔍 กรองข้อมูล (Filters)")
    all_airports = sorted(df['Airport_Name'].unique())
    selected_airports = st.sidebar.multiselect(
        "เลือกท่าอากาศยาน (Airports):", 
        all_airports, 
        default=all_airports
    )
    
    all_airlines = sorted(df['Airline_Name'].unique())
    selected_airlines = st.sidebar.multiselect(
        "เลือกสายการบิน (Airlines):",
        all_airlines,
        default=all_airlines
    )
    
    filtered_df = df[
        (df['Airport_Name'].isin(selected_airports)) & 
        (df['Airline_Name'].isin(selected_airlines))
    ]
        
    st.header("📊 ภาพรวมการใช้งาน (Overall Summary)")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Transactions", f"{int(filtered_df['Transactions'].sum()):,}")
    col2.metric("BP Prints", f"{int(filtered_df['BP Prints'].sum()):,}")
    col3.metric("Bag Tag Prints", f"{int(filtered_df['Bag Tag Prints'].sum()):,}")
    col4.metric("Passport Scans", f"{int(filtered_df['Passport Scans'].sum()):,}")
    col5.metric("BP Scans", f"{int(filtered_df['BP Scans'].sum()):,}")
    
    st.divider()
    
    st.header("🏆 เครื่อง Kiosk ที่ใช้งานเยอะที่สุด (Top Kiosks)")
    if not filtered_df.empty:
        # 1. Top Overall Kiosk
        top_overall = filtered_df.groupby('Display_Name')['Transactions'].sum().reset_index().sort_values('Transactions', ascending=False)
        if not top_overall.empty:
            top_1 = top_overall.iloc[0]
            st.markdown(f"**🌟 ยอดใช้งานสูงสุด (รวมทุกแอป):** `{top_1['Display_Name']}` ด้วยยอด **{int(top_1['Transactions']):,}** Transactions")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**✈️ ยอดใช้งานสูงสุด (แยกตามสายการบิน):**")
        
        # 2. Top Kiosk by Airline
        top_by_app = filtered_df.groupby(['Airline_Name', 'Display_Name'])['Transactions'].sum().reset_index()
        airlines = sorted(top_by_app['Airline_Name'].unique())
        
        if airlines:
            # Create columns based on number of airlines
            cols = st.columns(len(airlines))
            for i, app in enumerate(airlines):
                app_data = top_by_app[top_by_app['Airline_Name'] == app].sort_values('Transactions', ascending=False)
                if not app_data.empty:
                    top_app_kiosk = app_data.iloc[0]
                    with cols[i]:
                        st.info(f"**{app}**\n\n🏆 {top_app_kiosk['Display_Name']}\n\n📊 {int(top_app_kiosk['Transactions']):,} Tx")
    st.divider()
    
    st.header("📈 วิเคราะห์สถิติและจัดอันดับ (Analytics & Rankings)")
    if not filtered_df.empty:
        tab1, tab2, tab3 = st.tabs(["🏆 อันดับ Kiosk", "📍 อันดับท่าอากาศยาน", "✈️ อันดับแอปสายการบิน"])
        
        with tab1:
            st.markdown("**ตารางจัดอันดับเครื่อง Kiosk เรียงตามยอด Transactions**")
            kiosk_stats = filtered_df.groupby('Display_Name')[['Transactions', 'BP Prints', 'Bag Tag Prints', 'Passport Scans', 'BP Scans']].sum().reset_index()
            kiosk_stats = kiosk_stats.sort_values('Transactions', ascending=False).reset_index(drop=True)
            kiosk_stats.index += 1
            
            max_tx = int(kiosk_stats['Transactions'].max()) if not kiosk_stats.empty else 100
            max_bp = int(kiosk_stats['BP Prints'].max()) if not kiosk_stats.empty else 100
            max_ps = int(kiosk_stats['Passport Scans'].max()) if not kiosk_stats.empty else 100
            
            st.dataframe(
                kiosk_stats,
                use_container_width=True,
                column_config={
                    "Transactions": st.column_config.ProgressColumn("Transactions", format="%d", min_value=0, max_value=max_tx),
                    "BP Prints": st.column_config.ProgressColumn("BP Prints", format="%d", min_value=0, max_value=max_bp),
                    "Passport Scans": st.column_config.ProgressColumn("Passport Scans", format="%d", min_value=0, max_value=max_ps)
                }
            )
            
        with tab2:
            st.markdown("**ตารางจัดอันดับท่าอากาศยาน เรียงตามยอด Transactions**")
            airport_stats = filtered_df.groupby('Airport_Name')[['Transactions', 'BP Prints', 'Bag Tag Prints', 'Passport Scans', 'BP Scans']].sum().reset_index()
            airport_stats = airport_stats.sort_values('Transactions', ascending=False).reset_index(drop=True)
            airport_stats.index += 1
            
            max_tx2 = int(airport_stats['Transactions'].max()) if not airport_stats.empty else 100
            st.dataframe(
                airport_stats,
                use_container_width=True,
                column_config={
                    "Transactions": st.column_config.ProgressColumn("Transactions", format="%d", min_value=0, max_value=max_tx2)
                }
            )
            
        with tab3:
            st.markdown("**ตารางจัดอันดับแอปสายการบิน เรียงตามยอด Transactions**")
            airline_stats = filtered_df.groupby('Airline_Name')[['Transactions', 'BP Prints', 'Bag Tag Prints', 'Passport Scans', 'BP Scans']].sum().reset_index()
            airline_stats = airline_stats.sort_values('Transactions', ascending=False).reset_index(drop=True)
            airline_stats.index += 1
            
            max_tx3 = int(airline_stats['Transactions'].max()) if not airline_stats.empty else 100
            st.dataframe(
                airline_stats,
                use_container_width=True,
                column_config={
                    "Transactions": st.column_config.ProgressColumn("Transactions", format="%d", min_value=0, max_value=max_tx3)
                }
            )
            
    st.divider()
    kiosk_img_path = os.path.join(IMAGE_DIR, "CUSS.png")
    kiosk_b64 = get_image_base64(kiosk_img_path)
    
    grouped_airport = filtered_df.groupby('Airport_Name')
    
    for airport_name, airport_group in grouped_airport:
        st.subheader(f"📍 {airport_name}")
        
        kiosks = airport_group.groupby(['Display_Name', 'Machine_No']).sum(numeric_only=True).reset_index()
        kiosks = kiosks.sort_values('Machine_No')
        
        cols_per_row = 4
        
        for i in range(0, len(kiosks), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(kiosks):
                    row = kiosks.iloc[i + j]
                    with cols[j]:
                        kiosk_name = row['Display_Name']
                        
                        # Build Apps HTML
                        apps_data = airport_group[airport_group['Display_Name'] == kiosk_name]
                        apps_html = ""
                        for _, app_row in apps_data.iterrows():
                            app_raw = app_row['Applications']
                            tx = int(app_row['Transactions'])
                            app_info = AIRLINE_MAP.get(app_raw, {"name": app_raw})
                            app_name = app_info["name"]
                            logo_b64 = LOGO_B64.get(app_raw, "")
                            
                            img_tag = f'<img src="{logo_b64}" class="app-logo">' if logo_b64 else '<span style="font-size:24px; margin-right:12px;">✈️</span>'
                            
                            apps_html += f'''
<div class="app-row">
    {img_tag}
    <div class="app-info">
        <div class="app-name">{app_name}</div>
        <div class="app-tx">Tx: <strong>{tx:,}</strong></div>
    </div>
</div>
'''
                            
                        img_html = f'<img src="{kiosk_b64}" style="width: 130px; display: block; margin: 0 auto 15px auto;">' if kiosk_b64 else ''
                            
                        card_html = f'''
<div class="kiosk-card">
    <div class="kiosk-title">{kiosk_name}</div>
    {img_html}
    <div class="kiosk-stats">
        <div class="kiosk-stats-row"><span>Transactions:</span> <strong>{int(row['Transactions']):,}</strong></div>
        <div class="kiosk-stats-row"><span>BP Prints:</span> <strong>{int(row['BP Prints']):,}</strong></div>
        <div class="kiosk-stats-row"><span>Bag Tags:</span> <strong>{int(row['Bag Tag Prints']):,}</strong></div>
        <div class="kiosk-stats-row"><span>Passport Scans:</span> <strong>{int(row['Passport Scans']):,}</strong></div>
    </div>
    <div style="font-size: 0.9rem; color: #0052cc; margin: 15px 0 10px 0; font-weight: bold; border-bottom: 2px solid #0052cc; padding-bottom: 4px;">Airlines</div>
    {apps_html}
</div>
'''
                        st.markdown(card_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
