from datetime import datetime
import os
import requests
from groq import Groq
import streamlit as st

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Portal Evaluasi Laporan Wirausaha Mahasiswa",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Custom CSS UI
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        color: white;
        text-align: left;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .hero-subtitle { 
        font-size: 0.95rem; 
        color: #cbd5e1;
        font-weight: 400;
    }

    .eval-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)

api_key = st.secrets.get("GROQ_API_KEY")

# --- HEADER BANNER ---
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">💼 Portal Evaluasi Laporan Wirausaha Mahasiswa</div>
        <div class="hero-subtitle">Sistem Evaluasi Kinerja Bisnis & Business Model Canvas (BMC) Berbasis Artificial Intelligence</div>
    </div>
""",
    unsafe_allow_html=True,
)

with st.form("evaluasi_form"):
    # Section 1: Identitas Kelompok
    st.markdown("### 👤 1. Identitas Kelompok")
    col1, col2 = st.columns(2)
    with col1:
        nim = st.text_input("NIM Ketua / Perwakilan:")
        nama_ketua = st.text_input("Nama Ketua / Perwakilan:")
    with col2:
        nama_bisnis = st.text_input("Nama Kelompok / Produk Bisnis:")

    st.markdown("---")

    # Section 2: Data Finansial & Operasional (Dalam Rupiah)
    st.markdown("### 📈 2. Data Finansial & Operasional (Penjualan)")
    
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1.2])
    
    with col_f1:
        hpp = st.number_input("HPP per Unit (Rp):", min_value=0, value=0, step=1000)
        harga_jual = st.number_input("Harga Jual per Unit (Rp):", min_value=0, value=0, step=1000)

    with col_f2:
        target_penjualan_rp = st.number_input("Target Penjualan (Rp):", min_value=0, value=0, step=50000)
        realisasi_penjualan_rp = st.number_input("Realisasi Penjualan (Rp):", min_value=0, value=0, step=50000)

    with col_f3:
        deskripsi_produk = st.text_area(
            "Deskripsi Singkat Produk & Target Pasar:",
            placeholder="Jelaskan produk, manfaat, serta keunggulan target pasar...",
            height=130
        )

    st.markdown("---")

    # Section 3: Upload Document Business Model Canvas (BMC)
    st.markdown("### 📑 3. Upload Business Model Canvas (BMC)")
    bmc_file = st.file_uploader(
        "Upload Dokumen BMC (Format Gambar JPG/PNG atau PDF):", 
        type=["jpg", "jpeg", "png", "pdf"]
    )

    submit_btn = st.form_submit_button("⚡ Analisis Laporan Wirausaha", type="primary", use_container_width=True)

# Proses AI & Perhitungan Finansial Berbasis Rupiah
if submit_btn:
    if not nim or not nama_ketua or not nama_bisnis:
        st.warning("⚠️ Mohon lengkapi data Identitas Kelompok terlebih dahulu!")
    elif target_penjualan_rp <= 0:
        st.warning("⚠️ Target Penjualan (Rp) harus lebih dari 0!")
    elif not api_key:
        st.error("⚠️ GROQ API Key belum dikonfigurasi di Streamlit Secrets.")
    else:
        # Perhitungan Finansial Berbasis Rupiah
        pencapaian_persen = (realisasi_penjualan_rp / target_penjualan_rp) * 100
        selisih_rp = realisasi_penjualan_rp - target_penjualan_rp
        
        # Margin dan estimasi laba kotor
        margin_per_unit = harga_jual - hpp
        margin_ratio = (margin_per_unit / harga_jual) if harga_jual > 0 else 0
        estimasi_laba_kotor = realisasi_penjualan_rp * margin_ratio

        status_bmc = "Dokumen BMC Terlampir" if bmc_file is not None else "Dokumen BMC Belum Diunggah"

        # Prompt AI difokuskan pada Nominal Rupiah & Evaluasi BMC
        prompt = (
            f"Kamu Dosen Evaluator Kewirausahaan. Berikan analisis kinerja keuangan dan operasional bisnis mahasiswa berikut.\n\n"
            f"**DATA BISNIS:**\n"
            f"- Kelompok / Bisnis: {nama_bisnis} (Ketua: {nama_ketua} - {nim})\n"
            f"- Deskripsi & Pasar: {deskripsi_produk}\n"
            f"- Harga Jual: Rp {harga_jual:,.0f} | HPP: Rp {hpp:,.0f}\n"
            f"- Target Penjualan (Nominal): Rp {target_penjualan_rp:,.0f}\n"
            f"- Realisasi Penjualan (Nominal): Rp {realisasi_penjualan_rp:,.0f}\n"
            f"- Pencapaian Target: {pencapaian_persen:.1f}%\n"
            f"- Selisih Target (Rupiah): Rp {selisih_rp:,.0f}\n"
            f"- Estimasi Laba Kotor: Rp {estimasi_laba_kotor:,.0f}\n"
            f"- Status Lampiran BMC: {status_bmc}\n\n"
            f"**INSTRUKSI FORMAT JAWABAN:**\n"
            f"1. **📊 Evaluasi Capaian Penjualan (Rupiah)**: Bahas kinerja omset secara singkat berbasis nominal rupiah dan persentase capaian target.\n"
            f"2. **💰 Analisis Profitabilitas (Rupiah)**: Evaluasi estimasi laba kotor, struktur HPP vs Harga Jual, serta ketahanan margin rupiah bisnis ini.\n"
            f"3. **🎯 Alignment Business Model Canvas (BMC)**: Evaluasi kesesuaian antara model bisnis dengan realisasi penjualan rupiah yang dicapai.\n"
            f"4. **💡 Saran Strategis Pengembangan**: Berikan 2-3 rekomendasi konkret untuk meningkatkan pendapatan rupiah pada periode berikutnya.\n"
            f"5. **🎓 Catatan Evaluator**: 1-2 kalimat apresiasi dan motivasi untuk kelompok mahasiswa."
        )

        try:
            client = Groq(api_key=api_key)

            with st.spinner("⏳ AI sedang menganalisis data finansial dan omset rupiah..."):
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    max_tokens=650,
                    temperature=0.5,
                )
                res_text = chat_completion.choices[0].message.content

            # Display Ringkasan Metrik Finansial
            st.markdown("### 📊 Ringkasan Finansial Bisnis")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Target Omset", f"Rp {target_penjualan_rp:,.0f}")
            m2.metric("Realisasi Omset", f"Rp {realisasi_penjualan_rp:,.0f}", f"{pencapaian_persen:.1f}% Target")
            m3.metric("Selisih Omset", f"Rp {selisih_rp:,.0f}")
            m4.metric("Est. Laba Kotor", f"Rp {estimasi_laba_kotor:,.0f}")

            # Menampilkan File Preview jika gambar diunggah
            if bmc_file is not None and bmc_file.type in ["image/jpeg", "image/png", "image/jpg"]:
                st.markdown("### 🖼️ Preview Dokumen BMC")
                st.image(bmc_file, use_container_width=True)

            # Display Hasil Evaluasi AI
            st.markdown(
                f"""
                <div class="eval-card">
                    <h3 style="color: #1e3a8a; margin-top:0;">📋 Hasil Evaluasi Laporan Wirausaha: {nama_bisnis}</h3>
                    <p><b>Ketua Kelompok:</b> {nama_ketua} ({nim})</p>
                    <hr>
                </div>
            """,
                unsafe_allow_html=True,
            )
            st.markdown(res_text)

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses analisis: {e}")
