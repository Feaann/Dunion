# ======================================================================
# DASHBOARD DUNION -- Sistem Intelijen Geospasial Deteksi Anomali
# Harga Bawang Merah untuk Prioritas Intervensi
#
# Cara jalanin: simpan file ini + sistem_prioritas_intervensi.py di
# folder yang sama dengan data_bersih/, hasil_anomali/, hasil_granger/,
# hasil_granger_kekuatan/, hasil_prediksi_granger_rf/, lalu:
#     streamlit run dashboard_dunion.py
# ======================================================================

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sistem_prioritas_intervensi import bangun_cerita_provinsi, bangun_ringkasan_semua_provinsi, muat_aset

st.set_page_config(page_title="DUNION -- Prioritas Intervensi Harga Bawang", layout="wide", page_icon="🧅")

# ----------------------------------------------------------------------
# DESAIN: palet warna institusional (bukan default biru-putih SaaS).
# Biru tua gelap utk elemen netral/struktur, amber utk perhatian,
# merah-bata (bukan merah terang) utk urgensi tinggi -- nuansa lembaga
# pemerintah yang serius, bukan startup yang flashy.
# ----------------------------------------------------------------------
WARNA = {
    "latar": "#F7F5F0",
    "teks_utama": "#1B2430",
    "aksen_netral": "#2C3E50",
    "aman": "#3F7259",
    "waspada": "#C68A2E",
    "urgent": "#9C3D34",
    "garis": "#D9D3C7",
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {WARNA['teks_utama']};
    }}
    .judul-utama {{
        font-family: 'Source Serif 4', serif;
        font-weight: 700;
        font-size: 2.1rem;
        color: {WARNA['teks_utama']};
        margin-bottom: 0;
    }}
    .sub-judul {{
        color: #6B6458;
        font-size: 0.95rem;
        margin-top: 0.2rem;
    }}
    .kartu-kpi {{
        background: white;
        border: 1px solid {WARNA['garis']};
        border-radius: 6px;
        padding: 16px 20px;
    }}
    .rantai-sebab {{
        font-family: 'Inter', sans-serif;
        font-size: 0.92rem;
        padding: 10px 14px;
        border-left: 4px solid {WARNA['aksen_netral']};
        background: white;
        margin-bottom: 8px;
        border-radius: 0 4px 4px 0;
    }}
    .label-status {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        color: white;
    }}
    div[data-testid="stMetricValue"] {{
        font-family: 'Source Serif 4', serif;
    }}
</style>
""", unsafe_allow_html=True)


def label_status_html(level):
    warna = {"urgent": WARNA["urgent"], "waspada": WARNA["waspada"], "aman": WARNA["aman"]}[level]
    teks = {"urgent": "PERLU PERHATIAN SEGERA", "waspada": "PANTAU", "aman": "STABIL"}[level]
    return f'<span class="label-status" style="background:{warna}">{teks}</span>'


def tentukan_level(skor_anomali, ambang_waspada, ambang_urgent):
    if skor_anomali is None:
        return "aman"
    if skor_anomali >= ambang_urgent:
        return "urgent"
    if skor_anomali >= ambang_waspada:
        return "waspada"
    return "aman"


# ======================================================================
# MUAT ASET (di-cache supaya gak diulang tiap interaksi)
# ======================================================================
@st.cache_resource
def muat():
    return muat_aset()


aset = muat()

# ======================================================================
# HEADER
# ======================================================================
kol_judul, kol_tanggal = st.columns([3, 1])
with kol_judul:
    st.markdown('<p class="judul-utama">DUNION</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-judul">Deteksi Anomali Harga Bawang Merah &amp; Prioritas Intervensi -- '
        "dibangun dari pola distribusi antar provinsi</p>",
        unsafe_allow_html=True,
    )
with kol_tanggal:
    daftar_tanggal = sorted(aset["anomali"]["Tanggal"].dt.date.unique())
    tanggal_dipilih = st.selectbox("Tanggal pemantauan", options=daftar_tanggal[::-1], index=0)

st.markdown("<br>", unsafe_allow_html=True)

# ======================================================================
# BANGUN RINGKASAN UNTUK TANGGAL TERPILIH
# ======================================================================
with st.spinner("Menyusun analisis..."):
    ringkasan = bangun_ringkasan_semua_provinsi(aset, tanggal_dipilih)

AMBANG_WASPADA = ringkasan["Skor_Anomali"].quantile(0.80)
AMBANG_URGENT = ringkasan["Skor_Anomali"].quantile(0.95)
ringkasan["level"] = ringkasan["Skor_Anomali"].apply(lambda s: tentukan_level(s, AMBANG_WASPADA, AMBANG_URGENT))

# ======================================================================
# KPI RINGKAS
# ======================================================================
kol1, kol2, kol3, kol4 = st.columns(4)
with kol1:
    st.markdown('<div class="kartu-kpi">', unsafe_allow_html=True)
    st.metric("Provinsi dipantau", len(ringkasan))
    st.markdown("</div>", unsafe_allow_html=True)
with kol2:
    st.markdown('<div class="kartu-kpi">', unsafe_allow_html=True)
    st.metric("Perlu perhatian segera", int((ringkasan["level"] == "urgent").sum()))
    st.markdown("</div>", unsafe_allow_html=True)
with kol3:
    st.markdown('<div class="kartu-kpi">', unsafe_allow_html=True)
    st.metric("Perlu dipantau", int((ringkasan["level"] == "waspada").sum()))
    st.markdown("</div>", unsafe_allow_html=True)
with kol4:
    st.markdown('<div class="kartu-kpi">', unsafe_allow_html=True)
    jumlah_tervalidasi = int(ringkasan["Sumber_Tervalidasi"].fillna(False).sum())
    st.metric("Sumber penyebab tervalidasi", jumlah_tervalidasi)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ======================================================================
# DAFTAR PRIORITAS -- diurutkan dari paling perlu perhatian
# ======================================================================
st.markdown("### Provinsi yang Perlu Diperhatikan")

prioritas = ringkasan[ringkasan["level"].isin(["urgent", "waspada"])].sort_values("Skor_Anomali", ascending=False)

if len(prioritas) == 0:
    st.success("Tidak ada provinsi yang menunjukkan keanehan signifikan pada tanggal ini.")
else:
    for _, baris in prioritas.iterrows():
        with st.container(border=True):
            kol_a, kol_b = st.columns([1, 2])
            with kol_a:
                st.markdown(f"**{baris['Provinsi']}**", unsafe_allow_html=True)
                st.markdown(label_status_html(baris["level"]), unsafe_allow_html=True)
                st.markdown(
                    f"Harga saat ini: **Rp {baris['Harga_Saat_Ini']:,.0f}** "
                    f"({baris['Perubahan_1Hari_Persen']:+.1f}% dari hari sebelumnya)"
                )
                if pd.notna(baris["Prediksi_14_Hari"]):
                    st.markdown(f"Proyeksi 14 hari ke depan: **Rp {baris['Prediksi_14_Hari']:,.0f}**")
                    if "waspada ekstra" in str(baris["Status_Prediksi"]):
                        st.caption("⚠️ Model cenderung meremehkan kenaikan di provinsi ini -- waspada ekstra.")
                else:
                    st.caption(f"Proyeksi tidak tersedia: {baris['Status_Prediksi']}")

            with kol_b:
                if baris["Sumber_Utama"] != "-" and pd.notna(baris["Sumber_Utama"]):
                    status_validasi = "✅ tervalidasi" if baris["Sumber_Tervalidasi"] else "❔ belum terkonfirmasi"
                    st.markdown(
                        f'<div class="rantai-sebab">'
                        f'<b>{baris["Sumber_Utama"]}</b> &rarr; <b>{baris["Provinsi"]}</b><br>'
                        f'Jeda waktu: {baris["Lag_Hari"]:.0f} hari kerja &nbsp;|&nbsp; '
                        f'Kekuatan pengaruh: {baris["Kekuatan_Sumber"]*100:.1f}% &nbsp;|&nbsp; '
                        f'{status_validasi}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if not baris["Sumber_Tervalidasi"]:
                        st.caption(
                            "Catatan: hubungan ini terbukti signifikan secara historis, tapi provinsi sumber "
                            "TIDAK menunjukkan pergerakan tak biasa di jeda waktu yang sesuai untuk kasus ini -- "
                            "kemungkinan penyebabnya bukan dari sini, perlu investigasi lebih lanjut."
                        )
                else:
                    st.caption("Tidak ada provinsi sumber yang tervalidasi secara statistik untuk provinsi ini.")

st.markdown("<br>", unsafe_allow_html=True)

# ======================================================================
# TABEL LENGKAP (semua provinsi, bisa di-sort manual)
# ======================================================================
with st.expander("Lihat semua 33 provinsi"):
    tabel_tampil = ringkasan[[
        "Provinsi", "Skor_Anomali", "Harga_Saat_Ini", "Perubahan_1Hari_Persen",
        "Sumber_Utama", "Lag_Hari", "Prediksi_14_Hari",
    ]].round(2)
    st.dataframe(tabel_tampil, width='stretch', height=400)

st.markdown("<br>", unsafe_allow_html=True)

# ======================================================================
# DETAIL PER PROVINSI -- grafik tren
# ======================================================================
st.markdown("### Detail Tren per Provinsi")
provinsi_pilihan = st.selectbox("Pilih provinsi", aset["semua_provinsi"])

cerita = bangun_cerita_provinsi(aset, provinsi_pilihan, tanggal_dipilih)
harga_historis = aset["harga_wide"][provinsi_pilihan].loc[:pd.Timestamp(tanggal_dipilih)].tail(60)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=harga_historis.index, y=harga_historis.values, mode="lines",
    line=dict(color=WARNA["aksen_netral"], width=2), name="Harga historis",
))
if cerita["prediksi_14_hari"]:
    tanggal_proyeksi = pd.Timestamp(tanggal_dipilih) + pd.tseries.offsets.BDay(14)
    fig.add_trace(go.Scatter(
        x=[tanggal_proyeksi], y=[cerita["prediksi_14_hari"]], mode="markers",
        marker=dict(size=14, symbol="diamond", color=WARNA["waspada"]), name="Proyeksi 14 hari",
    ))
fig.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter", color=WARNA["teks_utama"]),
    yaxis_title="Harga (Rupiah)", height=380, margin=dict(t=20),
)
st.plotly_chart(fig, width='stretch')

if cerita["kandidat_sumber"]:
    st.markdown("**Provinsi yang terbukti signifikan mempengaruhi provinsi ini (diurutkan dari paling kuat):**")
    for sumber in cerita["kandidat_sumber"][:5]:
        tanda = "✅" if sumber["tervalidasi"] else "❔"
        st.markdown(
            f"{tanda} **{sumber['provinsi_asal']}** -- jeda {sumber['lag_hari']} hari, "
            f"kekuatan {sumber['kekuatan_r2']*100:.1f}%"
        )

st.markdown("---")
st.caption(
    "DUNION menggabungkan deteksi anomali (Isolation Forest), analisis hubungan sebab-akibat antar provinsi "
    "(Granger Causality, divalidasi dengan kontrol tren nasional), dan proyeksi harga (Random Forest "
    "tersaring-Granger). Sistem ini memberi prioritas dan konteks -- keputusan kebijakan akhir tetap "
    "memerlukan penilaian manusia."
)
