import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta
import urllib.parse
from PIL import Image
import time
from io import BytesIO

# ================== KONFIGURASI DASAR ==================
st.set_page_config(page_title="SEHATKAN PLN UP3 SITUBONDO", page_icon="🏥", layout="wide")

DB_FILE = "database_kesehatan.csv"
PHOTO_DIR = "pemeriksaan_foto"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo_pln.png")

if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

def load_data():
    columns = [
        "Tanggal_Input", "Nama", "Tempat_Lahir", "Tgl_Lahir", "NIK", "Bagian", 
        "Unit_Kerja", "No_WA", "BB", "TB", "Suhu", "Status_Suhu", "Tensi", "Oximeter", 
        "Status_Oximeter", "Alkohol", "Status_Alkohol", "BMI", "Status_BMI", 
        "Status_Tensi", "Pemeriksa", "Nama_Foto"
    ]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Tanggal_Input_DT'] = pd.to_datetime(df['Tanggal_Input'], format="%d/%m/%Y %H:%M")
            for col in columns:
                if col not in df.columns: df[col] = None
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_all_data(df):
    if 'Tanggal_Input_DT' in df.columns:
        df = df.drop(columns=['Tanggal_Input_DT'])
    df.to_csv(DB_FILE, index=False)

def to_excel(df):
    output = BytesIO()
    if 'Tanggal_Input_DT' in df.columns:
        df = df.drop(columns=['Tanggal_Input_DT'])
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Rekap_Kesehatan')
    writer.close()
    return output.getvalue()

def interpretasi_medis(bb, tb, suhu, tensi, oxi, alko):
    tb_m = tb / 100
    bmi = round(bb / (tb_m ** 2), 2)
    st_bmi = "Kurus" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obesitas"
    st_suhu = "Hipotermia" if suhu < 35.0 else "Normal" if 35.0 <= suhu <= 37.5 else "Demam"
    try:
        s, d = map(int, tensi.split("/"))
        if s > 180 or d > 120: st_tensi = "Hipertensi Tingkat 2"
        elif s > 140 or d > 90: st_tensi = "Hipertensi Tingkat 1"
        elif (130 <= s <= 139) or (85 <= d <= 89): st_tensi = "Pra Hipertensi"
        elif 90 <= s <= 129 and 60 <= d <= 84: st_tensi = "Normal"
        elif s < 90 or d < 60: st_tensi = "Hipotensi"
        else: st_tensi = "Normal (Variasi)"
    except: st_tensi = "Format Salah"
    st_oxi = "Normal" if oxi >= 95 else "Waspada" if oxi >= 90 else "Hipoksemia (Darurat)"
    st_alko = "Aman" if alko <= 0.02 else "Mabuk/Gangguan" if alko <= 0.15 else "BAHAYA"
    return bmi, st_bmi, st_suhu, st_tensi, st_oxi, st_alko

def link_wa(row):
    no_hp = str(row['No_WA']).strip()
    if no_hp.startswith("0"): no_hp = "62" + no_hp[1:]
    tgl_f = str(row['Tanggal_Input']).split(" ")[0]
    pesan = (
        f"HASIL MONITORING KESEHATAN TANGGAL {tgl_f}\n"
        f"--------------------------------------------\n"
        f"Nama: {row['Nama']}\nNIK: {row['NIK']}\n\n"
        f"Hasil Pemeriksaan:\n"
        f"* Tensi: {row['Tensi']} ({row['Status_Tensi']})\n"
        f"* Status BMI: {row['Status_BMI']} ({row['BMI']})\n"
        f"* Suhu: {row['Suhu']}°C\n"
        f"* Oximeter: {row['Oximeter']}% ({row['Status_Oximeter']})\n"
        f"--------------------------------------------\n"
        f"SEHATKAN - PLN"
    )
    return f"https://wa.me/{no_hp}?text={urllib.parse.quote(pesan)}"

# ================== UI LOGIN ==================
if "login" not in st.session_state: st.session_state.login = False
if not st.session_state.login:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.write("<br><br>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=120)
        st.title("🔐 Login SEHATKAN")
        u, p = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            if u == "admin" and p == "admin123":
                st.session_state.login = True
                st.rerun()
            else: st.error("Akses Ditolak!")
    st.stop()

with st.sidebar:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=100)
    st.title("Menu Navigasi")
    st.divider()
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.login = False
        st.rerun()

st.title("🏥 SEHATKAN PLN SITUBONDO V1.2 (Updated Jan 26)")
tab1, tab2, tab3 = st.tabs(["📝 Input Data", "📊 Database & Filter", "⚙️ Kelola"])

# --- TAB 1: INPUT DATA ---
with tab1:
    with st.form("input_form", clear_on_submit=True):
        st.subheader("📌 Identitas & Foto")
        c1, c2 = st.columns(2)
        with c1:
            nama, nik = st.text_input("Nama"), st.text_input("NIK")
            tmp_lhr = st.text_input("Tempat Lahir")
            tgl_lhr = st.date_input("Tanggal Lahir", value=date(1995, 1, 1))
            bagian = st.selectbox("Bagian", ["Yantek", "Billman", "CS", "Security", "Yanbung", "P2TL", "DIJ", "Driver"])
            unit_kerja = st.selectbox("Unit Kerja", ["ULP Asembagus", "ULP Panarukan", "ULP Besuki", "ULP Wonosari", "ULP Bondowoso"])
            wa, pem = st.text_input("No. WhatsApp (62...)"), st.text_input("Pemeriksa")
        with c2: foto_input = st.camera_input("Foto Pemeriksaan")
        
        st.divider()
        st.subheader("🩺 Hasil Pemeriksaan")
        c3, c4 = st.columns(2)
        with c3:
            bb, tb = st.number_input("BB (kg)", value=60.0), st.number_input("TB (cm)", value=165.0)
            suhu = st.number_input("Suhu (°C)", value=36.5)
        with c4:
            tns = st.text_input("Tensi", placeholder="120/80")
            oxi = st.number_input("Oximeter (%)", value=98)
            alk = st.number_input("Alkohol (%)", value=0.0)

        if st.form_submit_button("💾 SIMPAN DATA", use_container_width=True):
            if not nama or not nik or foto_input is None: st.error("Data tidak lengkap!")
            else:
                bmi, s_bmi, s_suhu, s_tns, s_oxi, s_alk = interpretasi_medis(bb, tb, suhu, tns, oxi, alk)
                img_name = f"{nik}_{datetime.now().strftime('%H%M%S')}.png"
                Image.open(foto_input).save(os.path.join(PHOTO_DIR, img_name))
                new_row = pd.DataFrame([{"Tanggal_Input": datetime.now().strftime("%d/%m/%Y %H:%M"), "Nama": nama, "NIK": nik, "Tempat_Lahir": tmp_lhr, "Tgl_Lahir": tgl_lhr.strftime('%d-%m-%Y'), "Bagian": bagian, "Unit_Kerja": unit_kerja, "No_WA": wa, "BB": bb, "TB": tb, "BMI": bmi, "Status_BMI": s_bmi, "Suhu": suhu, "Status_Suhu": s_suhu, "Tensi": tns, "Status_Tensi": s_tns, "Oximeter": oxi, "Status_Oximeter": s_oxi, "Alkohol": alk, "Status_Alcohol": s_alk, "Pemeriksa": pem, "Nama_Foto": img_name}])
                save_all_data(pd.concat([load_data(), new_row], ignore_index=True))
                st.success("✅ Berhasil disimpan!")
                st.markdown(f'<a href="{link_wa(new_row.iloc[0])}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold;">📲 KIRIM WA</button></a>', unsafe_allow_html=True)
                time.sleep(1); st.rerun()

# --- TAB 2: DATABASE & FILTER (GRAFIK DI BAWAH) ---
with tab2:
    df_mon = load_data()
    if not df_mon.empty:
        st.subheader("🔍 Filter Data")
        cf1, cf2, cf3 = st.columns([2, 2, 1])
        with cf1: start_date = st.date_input("Dari Tanggal", value=date.today() - timedelta(days=7))
        with cf2: end_date = st.date_input("Sampai Tanggal", value=date.today())
        with cf3:
            st.write("<br>", unsafe_allow_html=True)
            filter_btn = st.button("🔄 Refresh Data", use_container_width=True)

        mask = (df_mon['Tanggal_Input_DT'].dt.date >= start_date) & (df_mon['Tanggal_Input_DT'].dt.date <= end_date)
        df_filtered = df_mon.loc[mask]

        if not df_filtered.empty:
            # 1. Tabel & Download Berada di Atas
            col_t, col_e = st.columns([3, 1])
            with col_t: st.write(f"Menampilkan **{len(df_filtered)}** data pemeriksaan.")
            with col_e:
                df_xlsx = to_excel(df_filtered)
                st.download_button(label="📥 Download Excel Filtered", data=df_xlsx, file_name=f'Rekap_{start_date}_to_{end_date}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
            
            st.dataframe(df_filtered.drop(columns=["Nama_Foto", "Tanggal_Input_DT"]), use_container_width=True, hide_index=True)
            
            # 2. Grafik Berada di Bawah Tabel
            st.divider()
            st.subheader("📊 Ringkasan Statistik (Filter Terpilih)")
            ch1, ch2, ch3 = st.columns(3)
            with ch1:
                st.write("**Status BMI**")
                st.bar_chart(df_filtered['Status_BMI'].value_counts(), color="#29b5e8")
            with ch2:
                st.write("**Status Tensi**")
                st.bar_chart(df_filtered['Status_Tensi'].value_counts(), color="#ff4b4b")
            with ch3:
                st.write("**Kondisi Suhu**")
                st.bar_chart(df_filtered['Status_Suhu'].value_counts(), color="#ffaa00")
        else:
            st.warning("Data tidak ditemukan untuk rentang tanggal tersebut.")
    else:
        st.info("Database masih kosong.")

# --- TAB 3: KELOLA (TETAP SAMA) ---
with tab3:
    df_manage = load_data()
    if not df_manage.empty:
        st.subheader("⚙️ Kelola Database")
        st.info("💡 **Tips Hapus:** Sorot baris lalu tekan tombol **Delete** pada keyboard Anda.")
        edited = st.data_editor(df_manage.drop(columns=["Tanggal_Input_DT"]), use_container_width=True, hide_index=True, num_rows="dynamic")
        if st.button("💾 Simpan Perubahan"):
            save_all_data(edited)
            st.success("Tersimpan!"); st.rerun()
        if st.button("🔥 RESET TOTAL DATABASE"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()
