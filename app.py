import streamlit as st
import google.generativeai as genai
import pypdf
import pandas as pd
import os
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Portal Evaluasi Bisnis Wirausaha",
    page_icon="🎓",
    layout="wide"
)

# --- HEADER ---
st.title("🎓 Portal Evaluasi Laporan Wirausaha Mahasiswa")
st.write("Silakan isi data keuangan, deskripsi bisnis, dan unggah dokumen BMC kelompok Anda.")
st.markdown("---")

# --- SIDEBAR DOSEN (API KEY & REKAP) ---
st.sidebar.header("🔑 Panel Dosen / Evaluator")
api_key = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)

st.sidebar.markdown("---")
st.sidebar.header("📊 Rekapitulasi Nilai")

CSV_FILE = "rekap_nilai_wirausaha.csv"

if os.path.exists(CSV_FILE):
    df_rekap = pd.read_csv(CSV_FILE)
    st.sidebar.write(f"Total Laporan Masuk: **{len(df_rekap)}**")
    st.sidebar.download_button(
        label="📥 Download Rekap (CSV/Excel)",
        data=df_rekap.to_csv(index=False).encode('utf-8'),
        file_name=f"rekap_wirausaha_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )
else:
    st.sidebar.info("Belum ada data masuk.")

# --- FORM INPUT MAHASISWA ---
with st.form("form_wirausaha"):
    st.subheader("1. Identitas Kelompok")
    col1, col2 = st.columns(2)
    with col1:
        nim = st.text_input("NIM Ketua / Perwakilan:")
        nama = st.text_input("Nama Ketua / Perwakilan:")
    with col2:
        kelompok = st.text_input("Nama Kelompok / Produk Bisnis:")

    st.subheader("2. Data Finansial & Operasional (Penjualan)")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        hpp = st.number_input("HPP per Unit (Rp):", min_value=0, step=1000)
        harga_jual = st.number_input("Harga Jual per Unit (Rp):", min_value=0, step=1000)
    with col_b:
        target_unit = st.number_input("Target Penjualan (Unit):", min_value=0, step=1)
        realisasi_unit = st.number_input("Realisasi Penjualan (Unit):", min_value=0, step=1)
    with col_c:
        st.write("**Keterangan Tambahan:**")
        deskripsi = st.text_area("Deskripsi Singkat Produk & Target Pasar:", height=100)

    st.subheader("3. Dokumen Business Model Canvas (BMC)")
    file_pdf = st.file_uploader("Upload PDF / Diagram BMC (Maksimal 2 MB):", type=["pdf"])

    submit_button = st.form_submit_button("🚀 Kirim & Evaluasi Laporan")

# --- LOGIKA PEMROSESAN ---
if submit_button:
    if not api_key:
        st.error("⚠️ Sistem belum siap: Dosen perlu memasukkan API Key di sidebar kiri.")
    elif not nim or not nama or not kelompok or not file_pdf:
        st.warning("⚠️ Mohon lengkapi seluruh data identitas dan unggah file PDF BMC!")
    elif hpp <= 0 or harga_jual <= 0:
        st.warning("⚠️ HPP dan Harga Jual harus lebih dari 0!")
    else:
        # Pengecekan Ukuran File (Maksimal 2 MB = 2 * 1024 * 1024 bytes)
        if file_pdf.size > 2 * 1024 * 1024:
            st.error("❌ Ukuran file melebihi 2 MB! Mohon kompres file PDF BMC Anda terlebih dahulu.")
            st.stop()

        with st.spinner("⏳ Menghitung margin & menganalisis BMC dengan AI..."):
            try:
                # 1. Perhitungan Otomatis via Python (100% Akurat)
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

                # 3. Prompt Khusus Gemini AI
                prompt = f"""
                Bertindaklah sebagai Dosen Evaluator Bisnis Wirausaha Mahasiswa yang kritis dan konstruktif.
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

                ### 1. Indikasi Penggunaan AI Writing
                 Berikan estimasi % indikasi pola teks buatan AI beserta alasannya singkat.

                ### 2. Analisis Kelayakan Produk & Finansial
                 Evaluasi kinerjanya berdasarkan angka omzet, margin ({margin_persen:.1f}%), dan pencapaian target ({persen_capaian_target:.1f}%).

                ### 3. Koreksi 9 Elemen BMC
                 Evaluasi keselarasan antar-elemen BMC (misal: apakah Value Proposition sesuai dengan Customer Segment dan Channels).

                ### 4. Saran Strategis Ke Depan
                 Berikan 2-3 langkah taktis pengembangan bisnis.

                ### 📌 REKOMENDASI KELAYAKAN BISNIS
                PILIH TEPAT SATU dari 3 predikat di bawah ini dan tuliskan dengan tebal:
                - **[ Menjanjikan ]**
                - **[ Menjanjikan dengan Catatan ]**
                - **[ Perlu Perbaikan ]**
                (Sertakan alasan ringkas 1-2 kalimat).
                """

                # 4. Panggil Gemini Model
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                hasil_evaluasi = response.text

                # 5. Tampilkan Hasil ke Layar
                st.success("✅ Evaluasi Berhasil Diselesaikan!")
                st.markdown("---")
                
                # Tampilkan Metric Ringkas
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Margin Keuntungan", f"{margin_persen:.1f}%", f"Rp {margin_rp:,.0f}/unit")
                col_m2.metric("Capaian Target", f"{persen_capaian_target:.1f}%", f"{realisasi_unit}/{target_unit} unit")
                col_m3.metric("Total Profit", f"Rp {profit_total:,.0f}")

                st.markdown("---")
                st.markdown(hasil_evaluasi)

                # 6. Simpan ke Rekap Excel Dosen
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

            except Exception as e:
                st.error(f"Terjadi kesalahan teknis: {str(e)}")
