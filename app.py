import streamlit as st
from groq import Groq
import pypdf
import pandas as pd
import os
import requests
from datetime import datetime

# --- KONFIGURASI HALAMAN & TEMA ---
st.set_page_config(
    page_title="Portal Evaluasi Bisnis Wirausaha - UNKARTUR",
    page_icon="💼",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 24px;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #38bdf8;
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .main-header p {
        color: #cbd5e1;
        font-size: 14px;
        margin: 0;
    }
    .footer-box {
        text-align: center;
        color: #64748b;
        font-size: 13px;
        padding: 18px;
        background-color: #f8fafc;
        border-top: 2px solid #e2e8f0;
        border-radius: 8px;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- AMBIL SECRETS ---
client = None
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=groq_api_key)
    api_ready = True
except Exception:
    api_ready = False

gsheet_url = st.secrets.get("GOOGLE_SHEET_WEBAPP_URL", "")

# --- HEADER UTAMA ---
st.markdown("""
    <div class="main-header">
        <h1>💼 Portal Evaluasi Laporan Wirausaha Mahasiswa</h1>
        <p>Sistem Evaluasi Kinerja Bisnis & Business Model Canvas (BMC) Berbasis Artificial Intelligence</p>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR DOSEN ---
st.sidebar.markdown("### 🔒 Panel Dosen / Evaluator")
pin_input = st.sidebar.text_input("Masukkan PIN Dosen untuk Rekap Local:", type="password")

CSV_FILE = "rekap_nilai_wirausaha.csv"
dosen_pin = st.secrets.get("DOSEN_PIN", "1234")

if pin_input == dosen_pin:
    st.sidebar.success("🔓 Akses Dosen Diterima")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Rekapitulasi Nilai")
    
    if os.path.exists(CSV_FILE):
        df_rekap = pd.read_csv(CSV_FILE)
        st.sidebar.metric(label="Total Laporan Masuk (Lokal)", value=f"{len(df_rekap)} Laporan")
        st.sidebar.download_button(
            label="📥 Download Rekap Local (CSV)",
            data=df_rekap.to_csv(index=False).encode('utf-8'),
            file_name=f"rekap_wirausaha_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            use_container_width=True
        )
    else:
        st.sidebar.info("Belum ada data lokal.")
else:
    if pin_input:
        st.sidebar.error("❌ PIN Salah!")
    else:
        st.sidebar.info("📌 Panel ini khusus Dosen Pengampu.")

# --- FORM INPUT MAHASISWA ---
with st.form("form_wirausaha", clear_on_submit=False):
    st.markdown('### 👤 1. Identitas Kelompok')
    col1, col2 = st.columns(2)
    with col1:
        nim = st.text_input("NIM Ketua / Perwakilan:")
        nama = st.text_input("Nama Ketua / Perwakilan:")
    with col2:
        kelompok = st.text_input("Nama Kelompok / Produk Bisnis:")

    st.markdown("---")

    st.markdown('### 📈 2. Data Finansial & Operasional (Penjualan)')
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        hpp = st.number_input("HPP per Unit (Rp):", min_value=0, step=1000)
        harga_jual = st.number_input("Harga Jual per Unit (Rp):", min_value=0, step=1000)
    with col_b:
        target_unit = st.number_input("Target Penjualan (Unit):", min_value=0, step=1)
        realisasi_unit = st.number_input("Realisasi Penjualan (Unit):", min_value=0, step=1)
    with col_c:
        deskripsi = st.text_area("Deskripsi Singkat Produk & Target Pasar:", height=110, placeholder="Jelaskan produk, manfaat, serta keunggulan target pasar...")

    st.markdown("---")

    st.markdown('### 📄 3. Dokumen Business Model Canvas (BMC)')
    file_pdf = st.file_uploader("Upload PDF / Diagram BMC (Maksimal 2 MB):", type=["pdf"])

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        submit_button = st.form_submit_button("🚀 Kirim & Evaluasi Laporan", use_container_width=True, type="primary")
    with col_btn2:
        reset_button = st.form_submit_button("🔄 Reset Form", use_container_width=True)

if reset_button:
    st.rerun()

# --- LOGIKA PEMROSESAN EVALUASI & KIRIM KE GOOGLE SHEETS ---
if submit_button:
    if not api_ready or client is None:
        st.error("⚠️ Sistem belum siap: `GROQ_API_KEY` belum dimasukkan di Streamlit Secrets.")
    elif not nim or not nama or not kelompok or not file_pdf:
        st.warning("⚠️ Mohon lengkapi seluruh data identitas dan unggah file PDF BMC!")
    elif hpp <= 0 or harga_jual <= 0:
        st.warning("⚠️ HPP dan Harga Jual harus lebih dari 0!")
    else:
        if file_pdf.size > 2 * 1024 * 1024:
            st.error("❌ Ukuran file melebihi 2 MB! Mohon kompres file PDF BMC Anda terlebih dahulu.")
            st.stop()

        with st.spinner("⏳ Menghitung rasio finansial, menganalisis BMC, & menyinkronkan data ke Google Sheets..."):
            try:
                # 1. Perhitungan Otomatis
                margin_rp = harga_jual - hpp
                margin_persen = (margin_rp / harga_jual) * 100 if harga_jual > 0 else 0
                persen_capaian_target = (realisasi_unit / target_unit) * 100 if target_unit > 0 else 0
                omzet_total = realisasi_unit * harga_jual
                profit_total = realisasi_unit * margin_rp

                # 2. Ekstrak Teks dari PDF BMC
                pdf_reader = pypdf.PdfReader(file_pdf)
                text_bmc = ""
                for page in pdf_reader.pages:
                    text_bmc += page.extract_text() or ""

                # 3. Prompt Groq AI
                prompt = f"""
                Bertindaklah sebagai Dosen Evaluator Bisnis Wirausaha Mahasiswa yang kritis, objektif, dan konstruktif.
                Analisislah data bisnis dan teks BMC berikut:

                --- DATA KELOMPOK ---
                - Nama Produk/Bisnis: {kelompok}
                - Deskripsi Produk: {deskripsi}
                
                --- PERHITUNGAN FINANSIAL (Sistem Python) ---
                - HPP: Rp {hpp:,.0f} | Harga Jual: Rp {harga_jual:,.0f}
                - Margin Keuntungan per Unit: Rp {margin_rp:,.0f} ({margin_persen:.1f}%)
                - Target Penjualan: {target_unit} unit | Realisasi: {realisasi_unit} unit ({persen_capaian_target:.1f}% tercapai)
                - Total Omzet: Rp {omzet_total:,.0f} | Total Keuntungan Bersih: Rp {profit_total:,.0f}

                --- TEKS BMC ---
                {text_bmc[:4000]}

                --- TUGAS EVALUASI ---
                Berikan umpan balik rapi dengan format Markdown berikut:

                ### 1. Analisis Kelayakan Produk & Finansial
                Evaluasi kinerjanya berdasarkan angka omzet, margin ({margin_persen:.1f}%), dan pencapaian target ({persen_capaian_target:.1f}%).

                ### 2. Koreksi 9 Elemen BMC
                Evaluasi keselarasan antar-elemen BMC (misal: apakah Value Proposition sesuai dengan Customer Segment dan Channels).

                ### 3. Saran Strategis Ke Depan
                Berikan 2-3 langkah taktis pengembangan bisnis.

                ### 📌 REKOMENDASI KELAYAKAN BISNIS
                PILIH TEPAT SATU dari 3 predikat di bawah ini dan tuliskan dengan tebal:
                - **[ Menjanjikan ]**
                - **[ Menjanjikan dengan Catatan ]**
                - **[ Perlu Perbaikan ]**
                (Sertakan alasan ringkas 1-2 kalimat).
                """

                # 4. Panggil Groq AI Model
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Anda adalah Dosen Pengampu Kewirausahaan yang berpengalaman di Universitas Nasional Karangturi Semarang.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                )
                hasil_evaluasi = chat_completion.choices[0].message.content

                # 5. Kirim Data ke Google Sheets
                if gsheet_url:
                    payload = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "nim": nim,
                        "nama": nama,
                        "kelompok": kelompok,
                        "hpp": hpp,
                        "harga_jual": harga_jual,
                        "margin_persen": f"{margin_persen:.1f}%",
                        "capaian_target": f"{persen_capaian_target:.1f}%",
                        "total_profit": profit_total,
                        "evaluasi_ai": hasil_evaluasi
                    }
                    try:
                        requests.post(gsheet_url, json=payload, timeout=5)
                    except Exception as err_gsheet:
                        st.warning(f"⚠️ Gagal menyinkronkan ke Google Sheets: {str(err_gsheet)}")

                # 6. Simpan Juga ke File CSV Lokal
                data_baru = pd.DataFrame([{
                    "Waktu_Submit": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "NIM": nim,
                    "Nama": nama,
                    "Kelompok": kelompok,
                    "HPP": hpp,
                    "Harga_Jual": harga_jual,
                    "Margin_Persen": f"{margin_persen:.1f}%",
                    "Capaian_Target": f"{persen_capaian_target:.1f}%",
                    "Total_Profit": profit_total,
                    "Evaluasi_Lengkap_AI": hasil_evaluasi
                }])

                if not os.path.exists(CSV_FILE):
                    data_baru.to_csv(CSV_FILE, index=False)
                else:
                    data_baru.to_csv(CSV_FILE, mode='a', header=False, index=False)

                # 7. Tampilkan Hasil
                st.success("✅ Evaluasi Laporan Berhasil Diselesaikan & Data Tersimpan di Google Sheet!")
                st.markdown("---")
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Margin Keuntungan", f"{margin_persen:.1f}%", f"Rp {margin_rp:,.0f} / unit")
                col_m2.metric("Capaian Target", f"{persen_capaian_target:.1f}%", f"{realisasi_unit} dari {target_unit} unit")
                col_m3.metric("Total Profit", f"Rp {profit_total:,.0f}")

                st.markdown("---")
                st.markdown(hasil_evaluasi)

            except Exception as e:
                st.error(f"Terjadi kesalahan teknis: {str(e)}")

# --- FOOTER HAK CIPTA ---
st.markdown("""
    <div class="footer-box">
        © 2026 <b>Tim Kewirausahaan Universitas Nasional Karangturi Semarang</b>. All Rights Reserved.<br>
        <span style="font-size:12px; color:#94a3b8;">Sistem Informasi Evaluasi Wirausaha Berbasis Artificial Intelligence</span>
    </div>
""", unsafe_allow_html=True)
