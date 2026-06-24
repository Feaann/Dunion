# ======================================================================
# DASHBOARD DUNION v2 -- Sistem Intelijen Geospasial Deteksi Anomali
# Harga Bawang Merah untuk Prioritas Intervensi
#
# Cara jalanin: streamlit run dashboard_dunion.py
# ======================================================================

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import json
import urllib.request

from sistem_prioritas_intervensi import bangun_cerita_provinsi, bangun_ringkasan_semua_provinsi, muat_aset

st.set_page_config(
    page_title="DUNION — Prioritas Intervensi Harga Bawang",
    layout="wide",
    page_icon="🧅",
    initial_sidebar_state="collapsed",
)

# ======================================================================
# PALET WARNA & CSS
# ======================================================================
WARNA = {
    "latar":       "#F5F2EC",
    "teks_utama":  "#1A1F2E",
    "teks_sub":    "#5C6070",
    "aksen":       "#2D5F8A",
    "aman":        "#2E7D52",
    "waspada":     "#B8860B",
    "urgent":      "#8B2635",
    "garis":       "#DDD8CF",
    "kartu":       "#FFFFFF",
    "header_bg":   "#1A1F2E",
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    /* Reset background */
    .stApp {{
        background-color: {WARNA['latar']};
    }}
    section[data-testid="stSidebar"] {{
        background-color: {WARNA['header_bg']};
    }}

    /* Typography */
    html, body, [class*="css"], p, div, span, label {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: {WARNA['teks_utama']};
    }}

    /* Header strip */
    .header-strip {{
        background: {WARNA['header_bg']};
        padding: 28px 36px 22px 36px;
        border-radius: 10px;
        margin-bottom: 24px;
    }}
    .header-title {{
        font-family: 'IBM Plex Serif', serif !important;
        font-size: 2.4rem;
        font-weight: 700;
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.1;
    }}
    .header-sub {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.88rem;
        color: #9BA3B8 !important;
        margin-top: 6px;
        letter-spacing: 0.3px;
    }}
    .header-tag {{
        display: inline-block;
        background: rgba(255,255,255,0.1);
        color: #CBD5E0 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.72rem;
        padding: 3px 10px;
        border-radius: 4px;
        margin-top: 10px;
        letter-spacing: 1px;
    }}

    /* KPI cards */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }}
    .kpi-card {{
        background: {WARNA['kartu']};
        border: 1px solid {WARNA['garis']};
        border-radius: 8px;
        padding: 18px 20px 14px 20px;
        position: relative;
        overflow: hidden;
    }}
    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }}
    .kpi-card.biru::before  {{ background: {WARNA['aksen']}; }}
    .kpi-card.merah::before {{ background: {WARNA['urgent']}; }}
    .kpi-card.amber::before {{ background: {WARNA['waspada']}; }}
    .kpi-card.hijau::before {{ background: {WARNA['aman']}; }}
    .kpi-label {{
        font-size: 0.72rem;
        font-weight: 600;
        color: {WARNA['teks_sub']} !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }}
    .kpi-value {{
        font-family: 'IBM Plex Serif', serif !important;
        font-size: 2.2rem;
        font-weight: 700;
        color: {WARNA['teks_utama']} !important;
        line-height: 1;
    }}

    /* Badge status */
    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.70rem;
        font-weight: 600;
        letter-spacing: 0.6px;
        color: white !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }}
    .badge-urgent  {{ background: {WARNA['urgent']}; }}
    .badge-waspada {{ background: {WARNA['waspada']}; }}
    .badge-aman    {{ background: {WARNA['aman']}; }}

    /* Kartu provinsi */
    .prov-card {{
        background: {WARNA['kartu']};
        border: 1px solid {WARNA['garis']};
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 12px;
    }}
    .prov-name {{
        font-family: 'IBM Plex Serif', serif !important;
        font-size: 1.15rem;
        font-weight: 700;
        color: {WARNA['teks_utama']} !important;
        margin-bottom: 6px;
    }}
    .prov-harga {{
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 1.3rem;
        font-weight: 500;
        color: {WARNA['teks_utama']} !important;
    }}
    .prov-delta {{
        font-size: 0.82rem;
        color: {WARNA['teks_sub']} !important;
        margin-top: 2px;
    }}
    .prov-proyeksi {{
        font-size: 0.85rem;
        color: {WARNA['teks_sub']} !important;
        margin-top: 6px;
    }}

    /* Rantai sebab */
    .rantai {{
        background: {WARNA['latar']};
        border-left: 3px solid {WARNA['aksen']};
        border-radius: 0 6px 6px 0;
        padding: 12px 16px;
        margin-top: 8px;
        font-size: 0.88rem;
    }}
    .rantai-judul {{
        font-weight: 600;
        color: {WARNA['teks_utama']} !important;
        margin-bottom: 4px;
    }}
    .rantai-detail {{
        color: {WARNA['teks_sub']} !important;
        font-size: 0.80rem;
        font-family: 'IBM Plex Mono', monospace !important;
    }}

    /* Section header */
    .sek-header {{
        font-family: 'IBM Plex Serif', serif !important;
        font-size: 1.1rem;
        font-weight: 700;
        color: {WARNA['teks_utama']} !important;
        border-bottom: 2px solid {WARNA['garis']};
        padding-bottom: 8px;
        margin: 28px 0 16px 0;
        letter-spacing: -0.2px;
    }}

    /* Sembunyikan elemen Streamlit default */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 1.5rem !important; padding-bottom: 2rem !important; }}
    div[data-testid="stMetric"] {{ display: none; }}
</style>
""", unsafe_allow_html=True)


# ======================================================================
# HELPER
# ======================================================================
def badge_html(level):
    kelas = {"urgent": "badge-urgent", "waspada": "badge-waspada", "aman": "badge-aman"}[level]
    teks  = {"urgent": "⚠ PERLU TINDAKAN", "waspada": "● PANTAU", "aman": "✓ STABIL"}[level]
    return f'<span class="badge {kelas}">{teks}</span>'

def tentukan_level(skor, waspada, urgent):
    if skor is None: return "aman"
    if skor >= urgent: return "urgent"
    if skor >= waspada: return "waspada"
    return "aman"

def delta_html(pct):
    if pct is None or pd.isna(pct): return ""
    warna = WARNA["urgent"] if pct > 2 else (WARNA["aman"] if pct < -2 else WARNA["teks_sub"])
    arah  = "▲" if pct > 0 else "▼"
    return f'<span style="color:{warna};font-weight:600">{arah} {abs(pct):.1f}%</span> dari hari sebelumnya'


# ======================================================================
# LOAD DATA
# ======================================================================
@st.cache_resource
def muat():
    return muat_aset()

aset = muat()


# ======================================================================
# GEOJSON INDONESIA (dari sumber publik)
# ======================================================================
@st.cache_data
def muat_geojson():
    url = "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-province-simple.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

geojson = muat_geojson()

# Mapping nama provinsi ke nama di GeoJSON
NAMA_GEOJSON = {
    "Aceh": "Aceh",
    "Sumatera Utara": "Sumatera Utara",
    "Sumatera Barat": "Sumatera Barat",
    "Riau": "Riau",
    "Kepulauan Riau": "Kepulauan Riau",
    "Jambi": "Jambi",
    "Sumatera Selatan": "Sumatera Selatan",
    "Kepulauan Bangka Belitung": "Bangka Belitung",
    "Bengkulu": "Bengkulu",
    "Lampung": "Lampung",
    "DKI Jakarta": "DKI Jakarta",
    "Jawa Barat": "Jawa Barat",
    "Jawa Tengah": "Jawa Tengah",
    "DI Yogyakarta": "DI Yogyakarta",
    "Jawa Timur": "Jawa Timur",
    "Banten": "Banten",
    "Bali": "Bali",
    "Nusa Tenggara Barat": "Nusa Tenggara Barat",
    "Nusa Tenggara Timur": "Nusa Tenggara Timur",
    "Kalimantan Barat": "Kalimantan Barat",
    "Kalimantan Tengah": "Kalimantan Tengah",
    "Kalimantan Selatan": "Kalimantan Selatan",
    "Kalimantan Timur": "Kalimantan Timur",
    "Kalimantan Utara": "Kalimantan Utara",
    "Sulawesi Utara": "Sulawesi Utara",
    "Sulawesi Tengah": "Sulawesi Tengah",
    "Sulawesi Selatan": "Sulawesi Selatan",
    "Sulawesi Tenggara": "Sulawesi Tenggara",
    "Gorontalo": "Gorontalo",
    "Sulawesi Barat": "Sulawesi Barat",
    "Maluku": "Maluku",
    "Maluku Utara": "Maluku Utara",
    "Papua Barat": "Papua Barat",
    "Papua": "Papua",
}


# ======================================================================
# HEADER
# ======================================================================
kol_judul, kol_kontrol = st.columns([3, 1])
with kol_judul:
    st.markdown("""
    <div class="header-strip">
        <div class="header-title">DUNION</div>
        <div class="header-sub">Sistem Intelijen Harga Bawang Merah — Deteksi Anomali & Prioritas Intervensi</div>
        <div class="header-tag">ISOLATION FOREST · GRANGER CAUSALITY · RANDOM FOREST</div>
    </div>
    """, unsafe_allow_html=True)

with kol_kontrol:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    daftar_tanggal = sorted(aset["anomali"]["Tanggal"].dt.date.unique())
    tanggal_dipilih = st.selectbox("📅 Tanggal pemantauan", options=daftar_tanggal[::-1], index=0)


# ======================================================================
# BANGUN RINGKASAN
# ======================================================================
with st.spinner("Menyusun analisis..."):
    ringkasan = bangun_ringkasan_semua_provinsi(aset, tanggal_dipilih)

AMBANG_WASPADA = ringkasan["Skor_Anomali"].quantile(0.80)
AMBANG_URGENT  = ringkasan["Skor_Anomali"].quantile(0.95)
ringkasan["level"] = ringkasan["Skor_Anomali"].apply(
    lambda s: tentukan_level(s, AMBANG_WASPADA, AMBANG_URGENT)
)

n_urgent    = int((ringkasan["level"] == "urgent").sum())
n_waspada   = int((ringkasan["level"] == "waspada").sum())
n_tervalidasi = int(ringkasan["Sumber_Tervalidasi"].fillna(False).sum())


# ======================================================================
# KPI
# ======================================================================
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card biru">
        <div class="kpi-label">Provinsi Dipantau</div>
        <div class="kpi-value">{len(ringkasan)}</div>
    </div>
    <div class="kpi-card merah">
        <div class="kpi-label">Perlu Tindakan Segera</div>
        <div class="kpi-value">{n_urgent}</div>
    </div>
    <div class="kpi-card amber">
        <div class="kpi-label">Perlu Dipantau</div>
        <div class="kpi-value">{n_waspada}</div>
    </div>
    <div class="kpi-card hijau">
        <div class="kpi-label">Sumber Tervalidasi</div>
        <div class="kpi-value">{n_tervalidasi}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ======================================================================
# PETA CHOROPLETH
# ======================================================================
st.markdown('<div class="sek-header">🗺️ Peta Anomali Harga per Provinsi</div>', unsafe_allow_html=True)

ringkasan["nama_geojson"] = ringkasan["Provinsi"].map(NAMA_GEOJSON)
ringkasan["level_num"] = ringkasan["level"].map({"aman": 0, "waspada": 1, "urgent": 2})
ringkasan["tooltip"] = ringkasan.apply(
    lambda r: f"{r['Provinsi']}<br>Harga: Rp {r['Harga_Saat_Ini']:,.0f}<br>Status: {r['level'].upper()}",
    axis=1
)

if geojson:
    fig_peta = px.choropleth(
        ringkasan.dropna(subset=["nama_geojson"]),
        geojson=geojson,
        locations="nama_geojson",
        featureidkey="properties.state",
        color="level_num",
        color_continuous_scale=[
            [0.0, "#2E7D52"],
            [0.5, "#B8860B"],
            [1.0, "#8B2635"],
        ],
        range_color=[0, 2],
        hover_name="Provinsi",
        hover_data={
            "Harga_Saat_Ini": ":,.0f",
            "Perubahan_1Hari_Persen": ":.1f",
            "Skor_Anomali": ":.3f",
            "nama_geojson": False,
            "level_num": False,
        },
        labels={
            "Harga_Saat_Ini": "Harga (Rp)",
            "Perubahan_1Hari_Persen": "Perubahan (%)",
            "Skor_Anomali": "Skor Anomali",
        },
    )
    fig_peta.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor=WARNA["latar"],
    )
    fig_peta.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
        paper_bgcolor=WARNA["latar"],
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_peta, use_container_width=True)

    # Legenda manual
    st.markdown("""
    <div style="display:flex;gap:20px;font-size:0.80rem;margin-top:-8px;margin-bottom:8px">
        <span><span style="display:inline-block;width:12px;height:12px;background:#2E7D52;border-radius:2px;margin-right:5px"></span>Stabil</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:#B8860B;border-radius:2px;margin-right:5px"></span>Perlu Dipantau</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:#8B2635;border-radius:2px;margin-right:5px"></span>Perlu Tindakan</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Peta tidak tersedia (gagal memuat GeoJSON). Pastikan koneksi internet aktif.")


# ======================================================================
# DAFTAR PRIORITAS
# ======================================================================
st.markdown('<div class="sek-header">⚡ Provinsi yang Perlu Diperhatikan</div>', unsafe_allow_html=True)

prioritas = ringkasan[ringkasan["level"].isin(["urgent", "waspada"])].sort_values("Skor_Anomali", ascending=False)

if len(prioritas) == 0:
    st.success("✓ Tidak ada provinsi yang menunjukkan anomali signifikan pada tanggal ini.")
else:
    for _, b in prioritas.iterrows():
        kol_a, kol_b = st.columns([1, 1.8])
        with kol_a:
            proyeksi_html = ""
            if pd.notna(b["Prediksi_14_Hari"]):
                selisih = b["Prediksi_14_Hari"] - b["Harga_Saat_Ini"]
                arah = "▲" if selisih > 0 else "▼"
                warna_proj = WARNA["urgent"] if selisih > 0 else WARNA["aman"]
                proyeksi_html = f"""
                <div class="prov-proyeksi">
                    Proyeksi 14 hari: <strong>Rp {b['Prediksi_14_Hari']:,.0f}</strong>
                    <span style="color:{warna_proj}">{arah} Rp {abs(selisih):,.0f}</span>
                </div>"""
                if "waspada ekstra" in str(b["Status_Prediksi"]):
                    proyeksi_html += '<div style="font-size:0.75rem;color:#B8860B;margin-top:4px">⚠ Model cenderung meremehkan kenaikan di provinsi ini</div>'
            else:
                proyeksi_html = f'<div class="prov-proyeksi" style="color:{WARNA["teks_sub"]}">Proyeksi tidak tersedia</div>'

            st.markdown(f"""
            <div class="prov-card">
                <div class="prov-name">{b['Provinsi']}</div>
                {badge_html(b['level'])}
                <div style="margin-top:12px">
                    <div class="prov-harga">Rp {b['Harga_Saat_Ini']:,.0f}</div>
                    <div class="prov-delta">{delta_html(b['Perubahan_1Hari_Persen'])}</div>
                </div>
                {proyeksi_html}
            </div>
            """, unsafe_allow_html=True)

        with kol_b:
            if b["Sumber_Utama"] != "-" and pd.notna(b["Sumber_Utama"]):
                status = "✅ Tervalidasi" if b["Sumber_Tervalidasi"] else "❔ Belum terkonfirmasi"
                catatan = ""
                if not b["Sumber_Tervalidasi"]:
                    catatan = f'<div style="font-size:0.75rem;color:{WARNA["teks_sub"]};margin-top:8px">Provinsi sumber tidak menunjukkan pergerakan tak biasa di jeda waktu yang sesuai — kemungkinan ada faktor lain.</div>'
                st.markdown(f"""
                <div class="prov-card" style="height:100%">
                    <div style="font-size:0.75rem;font-weight:600;color:{WARNA['teks_sub']};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Rantai Distribusi</div>
                    <div class="rantai">
                        <div class="rantai-judul">{b['Sumber_Utama']} → {b['Provinsi']}</div>
                        <div class="rantai-detail">
                            Jeda: {b['Lag_Hari']:.0f} hari kerja &nbsp;·&nbsp;
                            Kekuatan: {b['Kekuatan_Sumber']*100:.1f}% &nbsp;·&nbsp;
                            {status}
                        </div>
                    </div>
                    {catatan}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="prov-card" style="height:100%;display:flex;align-items:center">
                    <span style="color:{WARNA['teks_sub']};font-size:0.85rem">Tidak ada provinsi sumber yang tervalidasi secara statistik.</span>
                </div>
                """, unsafe_allow_html=True)


# ======================================================================
# TABEL LENGKAP
# ======================================================================
with st.expander("📋 Lihat semua provinsi"):
    tabel = ringkasan[[
        "Provinsi", "level", "Skor_Anomali", "Harga_Saat_Ini",
        "Perubahan_1Hari_Persen", "Sumber_Utama", "Lag_Hari", "Prediksi_14_Hari",
    ]].rename(columns={
        "level": "Status",
        "Skor_Anomali": "Skor",
        "Harga_Saat_Ini": "Harga (Rp)",
        "Perubahan_1Hari_Persen": "Δ Harian (%)",
        "Sumber_Utama": "Sumber",
        "Lag_Hari": "Lag (hari)",
        "Prediksi_14_Hari": "Proyeksi 14H (Rp)",
    }).round(2)
    st.dataframe(tabel, use_container_width=True, height=380)


# ======================================================================
# DETAIL PER PROVINSI
# ======================================================================
st.markdown('<div class="sek-header">📈 Detail Tren per Provinsi</div>', unsafe_allow_html=True)

provinsi_pilihan = st.selectbox("Pilih provinsi", aset["semua_provinsi"])
cerita = bangun_cerita_provinsi(aset, provinsi_pilihan, tanggal_dipilih)
harga_historis = aset["harga_wide"][provinsi_pilihan].loc[:pd.Timestamp(tanggal_dipilih)].tail(90)

fig = go.Figure()

# Area fill di bawah garis
fig.add_trace(go.Scatter(
    x=harga_historis.index, y=harga_historis.values,
    fill="tozeroy", fillcolor="rgba(45,95,138,0.06)",
    line=dict(color=WARNA["aksen"], width=2),
    name="Harga historis",
))

# Titik proyeksi
if cerita["prediksi_14_hari"]:
    tgl_proj = pd.Timestamp(tanggal_dipilih) + pd.tseries.offsets.BDay(14)
    harga_terakhir = float(harga_historis.iloc[-1])
    selisih = cerita["prediksi_14_hari"] - harga_terakhir
    warna_proj = WARNA["urgent"] if selisih > 0 else WARNA["aman"]

    # Garis putus-putus ke proyeksi
    fig.add_trace(go.Scatter(
        x=[harga_historis.index[-1], tgl_proj],
        y=[harga_terakhir, cerita["prediksi_14_hari"]],
        mode="lines",
        line=dict(color=warna_proj, width=1.5, dash="dot"),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[tgl_proj], y=[cerita["prediksi_14_hari"]],
        mode="markers+text",
        marker=dict(size=12, symbol="diamond", color=warna_proj,
                    line=dict(color="white", width=2)),
        text=[f"  Rp {cerita['prediksi_14_hari']:,.0f}"],
        textposition="middle right",
        textfont=dict(size=11, color=warna_proj),
        name=f"Proyeksi +14 hari",
    ))

fig.update_layout(
    plot_bgcolor="white",
    paper_bgcolor=WARNA["latar"],
    font=dict(family="IBM Plex Sans", color=WARNA["teks_utama"], size=12),
    yaxis_title="Harga (Rp)",
    yaxis=dict(gridcolor="#F0EDE6", tickformat=",.0f"),
    xaxis=dict(gridcolor="#F0EDE6"),
    height=360,
    margin=dict(t=16, b=16, l=16, r=16),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True)

# Sumber Granger
if cerita["kandidat_sumber"]:
    st.markdown(f"<div style='font-size:0.80rem;font-weight:600;color:{WARNA['teks_sub']};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px'>Provinsi yang terbukti mempengaruhi {provinsi_pilihan}</div>", unsafe_allow_html=True)
    cols = st.columns(min(len(cerita["kandidat_sumber"][:5]), 5))
    for i, sumber in enumerate(cerita["kandidat_sumber"][:5]):
        with cols[i]:
            tanda = "✅" if sumber["tervalidasi"] else "❔"
            st.markdown(f"""
            <div style="background:white;border:1px solid {WARNA['garis']};border-radius:6px;padding:12px;text-align:center">
                <div style="font-size:0.70rem;color:{WARNA['teks_sub']}">{tanda} Sumber #{i+1}</div>
                <div style="font-weight:600;font-size:0.85rem;margin:4px 0">{sumber['provinsi_asal']}</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:{WARNA['aksen']}">lag {sumber['lag_hari']}h · {sumber['kekuatan_r2']*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)


# ======================================================================
# FOOTER
# ======================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="border-top:1px solid {WARNA['garis']};padding-top:16px;font-size:0.75rem;color:{WARNA['teks_sub']}">
    <strong>DUNION</strong> · Isolation Forest + Granger Causality + Random Forest ·
    Sistem ini memberi prioritas dan konteks — keputusan kebijakan akhir tetap memerlukan penilaian manusia.
</div>
""", unsafe_allow_html=True)
