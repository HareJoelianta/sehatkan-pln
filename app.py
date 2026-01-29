import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import urllib.parse
from PIL import Image
import time

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
        "Unit_Kerja", "No_WA", "BB", "TB", "Suhu", "Tensi", "Oximeter", "Status_Oximeter",
        "Alkohol", "Status_Alkohol", "BMI", "Status_BMI", "Status_Tensi", "Pemeriksa", "Nama_Foto"
    ]
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            for col in columns:
                if col not in df.columns: df[col] = None
            return df[columns]
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_all_data(df):
    df.to_csv(DB_FILE, index=False)

# ================== LOGIKA MEDIS DETAIL ==================
def interpretasi_medis(bb, tb, tensi, oxi, alko):
    # Logika BMI
    tb_m = tb / 100
    bmi = round(bb / (tb_m ** 2), 2)
    if bmi < 18.5: st_bmi = "Kurus"
    elif bmi < 25: st_bmi = "Normal"
    elif bmi < 30: st_bmi = "Overweight"
    else: st_bmi = "Obesitas"
    
    # Logika Tensi Sesuai Rincian Dewasa
    try:
        s, d = map(int, tensi.split("/"))
        if s < 90 or d < 60: 
            st_tensi = "Hipotensi"
        elif 90 <= s <= 120 and 60 <= d <= 80: 
            st_tensi = "Normal"
        elif 120 <= s <= 139 or 80 <= d <= 89: 
            st_tensi = "Pre-Hipertensi (Normal Tinggi)"
        elif 140 <= s <= 159 or 90 <= d <= 99: 
            st_tensi = "Hipertensi Derajat 1"
        elif s >= 160 or d >= 100: 
            st_tensi = "Hipertensi Derajat 2"
        else:
            st_tensi = "Normal (Variasi)"
    except: 
        st_tensi = "Format Salah"
    
    # Oximeter & Alkohol
    st_oxi = "Normal" if oxi >= 95 else "Waspada" if oxi >= 90 else "Hipoksemia (Darurat)"
    st_alko = "Aman" if alko <= 0.02 else "Mabuk/Gangguan" if alko <= 0.15 else "BAHAYA"
    
    return bmi, st_bmi, st_tensi, st_oxi, st_alko

# ================== WHATSAPP FORMAT ==================
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
        f"* Suhu: {row['Suhu']}°C\n"
        f"* Oximeter: {row['Oximeter']}% ({row['Status_Oximeter']})\n"
        f"* Alkohol: {row['Alkohol']}% ({row['Status_Alkohol']})\n\n"
        f"Patuhi K3 dan Tetap Jaga Kesehatan\n"
        f"--------------------------------------------\n"
        f"SEHATKAN - PLN"
    )
    return f"https://wa.me/{no_hp}?text={urllib.parse.quote(pesan)}"

# ================== LOGIN SYSTEM ==================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.write("<br><br>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=120)
        st.title("🔐 Login SEHATKAN")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            if u == "admin" and p == "admin123":
                st.session_state.login = True
                st.rerun()
            else: st.error("Akses Ditolak!")
    st.stop()

# ================== SIDEBAR ==================
with st.sidebar:
    if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=100)
    st.title("Menu Navigasi")
    st.divider()
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.login = False
        st.rerun()

# ================== UI UTAMA ==================
st.title("🏥 SEHATKAN PLN UP3 SITUBONDO V1.2")
tab1, tab2, tab3 = st.tabs(["📝 Input Data", "📊 Database", "⚙️ Kelola"])

with tab1:
    with st.form("input_form", clear_on_submit=True):
        st.subheader("📌 Identitas & Foto")
        c1, c2 = st.columns(2)
        with c1:
            nama = st.text_input("Nama")
            nik = st.text_input("NIK")
            tmp_lhr = st.text_input("Tempat Lahir")
            tgl_lhr = st.date_input("Tanggal Lahir", value=date(1995, 1, 1))
            bagian = st.selectbox("Bagian", ["Yantek", "Billman", "CS", "Security", "Yanbung", "P2TL", "DIJ", "Driver"])
            unit_kerja = st.selectbox("Unit Kerja", ["ULP Asembagus", "ULP Panarukan", "ULP Besuki", "ULP Wonosari", "ULP Bondowoso"])
            wa = st.text_input("No. WhatsApp (62...)")
            pemeriksa = st.text_input("Pemeriksa")
        with c2:
            foto_input = st.camera_input("Foto Pemeriksaan")
        
        st.divider()
        st.subheader("🩺 Hasil Pemeriksaan")
        st.info("📢 **Isikan dengan format benar dan tepat !**")
        c3, c4 = st.columns(2)
        with c3:
            bb = st.number_input("BB (kg)", min_value=1.0, value=60.0, step=0.1)
            tb = st.number_input("TB (cm)", min_value=1.0, value=165.0, step=0.1)
            suhu = st.number_input("Suhu (°C)", min_value=30.0, value=36.5, step=0.1)
        with c4:
            tns = st.text_input("Tensi", placeholder="Contoh: 145/95")
            oxi = st.number_input("Oximeter (%)", value=98)
            alk = st.number_input("Alkohol (%)", value=0.0, format="%.2f")

        if st.form_submit_button("💾 SIMPAN DATA", use_container_width=True):
            if not nama or not nik or foto_input is None: 
                st.error("Lengkapi Nama, NIK, dan Foto!")
            else:
                bmi, s_bmi, s_tns, s_oxi, s_alk = interpretasi_medis(bb, tb, tns, oxi, alk)
                img_name = f"{nik}_{datetime.now().strftime('%H%M%S')}.png"
                Image.open(foto_input).save(os.path.join(PHOTO_DIR, img_name))
                
                new_row = pd.DataFrame([{
                    "Tanggal_Input": datetime.now().strftime("%d/%m/%Y %H:%M"), "Nama": nama, "NIK": nik, 
                    "Tempat_Lahir": tmp_lhr, "Tgl_Lahir": tgl_lhr.strftime('%d-%m-%Y'), "Bagian": bagian,
                    "Unit_Kerja": unit_kerja, "No_WA": wa, "BB": bb, "TB": tb, "BMI": bmi, "Status_BMI": s_bmi, 
                    "Suhu": suhu, "Tensi": tns, "Status_Tensi": s_tns, "Oximeter": oxi, "Status_Oximeter": s_oxi,
                    "Alkohol": alk, "Status_Alkohol": s_alk, "Pemeriksa": pemeriksa, "Nama_Foto": img_name
                }])
                save_all_data(pd.concat([load_data(), new_row], ignore_index=True))
                st.success(f"✅ Data Tersimpan! Status Tensi: {s_tns}")
                st.markdown(f'<a href="{link_wa(new_row.iloc[0])}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold;">📲 KIRIM WHATSAPP</button></a>', unsafe_allow_html=True)
                time.sleep(2); st.rerun()

with tab2:
    df_mon = load_data()
    if not df_mon.empty:
        st.subheader("📊 Monitoring Statistik")
        cg1, cg2 = st.columns(2)
        with cg1:
            st.write("**Status Tensi**")
            st.bar_chart(df_mon['Status_Tensi'].value_counts())
        with cg2:
            st.write("**Status Oksigen**")
            st.bar_chart(df_mon['Status_Oximeter'].value_counts())
        
        st.divider()
        st.dataframe(df_mon.drop(columns=["Nama_Foto"]), use_container_width=True, hide_index=True)
    else:
        st.info("Database kosong.")

with tab3:
    df_manage = load_data()
    if not df_manage.empty:
        st.subheader("⚙️ Kelola Database")
        df_manage["Hapus"] = False
        edited = st.data_editor(df_manage, use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Perubahan"):
            save_all_data(edited.drop(columns=["Hapus"]))
            st.success("Tersimpan!"); st.rerun()
        st.divider()
        if st.button("🔥 RESET TOTAL DATABASE"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.rerun()
