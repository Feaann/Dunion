# ======================================================================
# DASHBOARD DUNION v3
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

WARNA = {
    "latar":      "#F5F2EC",
    "teks_utama": "#1A1F2E",
    "teks_sub":   "#5C6070",
    "aksen":      "#2D5F8A",
    "aman":       "#2E7D52",
    "waspada":    "#B8860B",
    "urgent":     "#8B2635",
    "garis":      "#DDD8CF",
    "kartu":      "#FFFFFF",
    "header_bg":  "#1A1F2E",
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    .stApp {{ background-color: {WARNA['latar']}; }}

    html, body, [class*="css"], p, div, span, label {{
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: {WARNA['teks_utama']};
    }}

    /* Fix dropdown teks gelap */
    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: white !important;
        color: {WARNA['teks_utama']} !important;
    }}
    .stSelectbox span, .stSelectbox div {{
        color: {WARNA['teks_utama']} !important;
    }}
    [data-baseweb="menu"] {{
        background-color: white !important;
    }}
    [data-baseweb="option"] {{
        color: {WARNA['teks_utama']} !important;
        background-color: white !important;
    }}
    [data-baseweb="option"]:hover {{
        background-color: #f0f0f0 !important;
    }}

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
        font-size: 0.88rem;
        color: #9BA3B8 !important;
        margin-top: 6px;
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

    .prov-card {{
        background: {WARNA['kartu']};
        border: 1px solid {WARNA['garis']};
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 12px;
        min-height: 160px;
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

    .rantai {{
        background: {WARNA['latar']};
        border-left: 3px solid {WARNA['aksen']};
        border-radius: 0 6px 6px 0;
        padding: 12px 16px;
        margin-top: 8px;
        font-size: 0.88rem;
    }}

    .sek-header {{
        font-family: 'IBM Plex Serif', serif !important;
        font-size: 1.1rem;
        font-weight: 700;
        color: {WARNA['teks_utama']} !important;
        border-bottom: 2px solid {WARNA['garis']};
        padding-bottom: 8px;
        margin: 28px 0 16px 0;
    }}

    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 1.5rem !important; padding-bottom: 2rem !important; }}
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
    if skor is None or pd.isna(skor): return "aman"
    if skor >= urgent: return "urgent"
    if skor >= waspada: return "waspada"
    return "aman"

def delta_warna(pct):
    if pct is None or pd.isna(pct): return WARNA["teks_sub"]
    return WARNA["urgent"] if pct > 2 else (WARNA["aman"] if pct < -2 else WARNA["teks_sub"])


# ======================================================================
# LOAD DATA
# ======================================================================
@st.cache_resource
def muat():
    return muat_aset()

aset = muat()


# ======================================================================
# GEOJSON -- coba beberapa sumber
# ======================================================================
@st.cache_data
def muat_geojson():
    urls = [
        "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-province-simple.json",
        "https://raw.githubusercontent.com/ans-4175/peta-indonesia-geojson/master/indonesia-prov.geojson",
    ]
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                data = json.loads(r.read().decode())
                return data
        except Exception:
            continue
    return None

geojson = muat_geojson()

# Cek key nama di GeoJSON (beda sumber beda key)
def cari_key_nama(geojson):
    if not geojson or not geojson.get("features"):
        return None
    props = geojson["features"][0].get("properties", {})
    for k in ["state", "name", "NAME_1", "PROVINSI", "propinsi", "Propinsi"]:
        if k in props:
            return k
    return list(props.keys())[0] if props else None

geo_key = cari_key_nama(geojson)

NAMA_GEOJSON = {
    "Aceh": ["Aceh", "Nanggroe Aceh Darussalam"],
    "Sumatera Utara": ["Sumatera Utara"],
    "Sumatera Barat": ["Sumatera Barat"],
    "Riau": ["Riau"],
    "Kepulauan Riau": ["Kepulauan Riau"],
    "Jambi": ["Jambi"],
    "Sumatera Selatan": ["Sumatera Selatan"],
    "Kepulauan Bangka Belitung": ["Bangka Belitung", "Kepulauan Bangka Belitung", "Bangka-Belitung"],
    "Bengkulu": ["Bengkulu"],
    "Lampung": ["Lampung"],
    "DKI Jakarta": ["DKI Jakarta", "Jakarta"],
    "Jawa Barat": ["Jawa Barat"],
    "Jawa Tengah": ["Jawa Tengah"],
    "DI Yogyakarta": ["DI Yogyakarta", "Yogyakarta", "D.I. Yogyakarta"],
    "Jawa Timur": ["Jawa Timur"],
    "Banten": ["Banten"],
    "Bali": ["Bali"],
    "Nusa Tenggara Barat": ["Nusa Tenggara Barat", "NTB"],
    "Nusa Tenggara Timur": ["Nusa Tenggara Timur", "NTT"],
    "Kalimantan Barat": ["Kalimantan Barat"],
    "Kalimantan Tengah": ["Kalimantan Tengah"],
    "Kalimantan Selatan": ["Kalimantan Selatan"],
    "Kalimantan Timur": ["Kalimantan Timur"],
    "Kalimantan Utara": ["Kalimantan Utara"],
    "Sulawesi Utara": ["Sulawesi Utara"],
    "Sulawesi Tengah": ["Sulawesi Tengah"],
    "Sulawesi Selatan": ["Sulawesi Selatan"],
    "Sulawesi Tenggara": ["Sulawesi Tenggara"],
    "Gorontalo": ["Gorontalo"],
    "Sulawesi Barat": ["Sulawesi Barat"],
    "Maluku": ["Maluku"],
    "Maluku Utara": ["Maluku Utara"],
    "Papua Barat": ["Papua Barat"],
    "Papua": ["Papua"],
}

def cari_nama_geojson(provinsi, geojson, key):
    """Cari nama provinsi yang cocok di GeoJSON secara fleksibel."""
    if not geojson or not key:
        return None
    nama_di_geo = [f["properties"].get(key, "") for f in geojson["features"]]
    kandidat = NAMA_GEOJSON.get(provinsi, [provinsi])
    for k in kandidat:
        for nama in nama_di_geo:
            if k.lower() == str(nama).lower():
                return nama
    return None


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
# BANGUN RINGKASAN -- ini dijalankan ulang setiap tanggal berubah
# ======================================================================
with st.spinner("Menyusun analisis..."):
    ringkasan = bangun_ringkasan_semua_provinsi(aset, tanggal_dipilih)

AMBANG_WASPADA = ringkasan["Skor_Anomali"].quantile(0.80)
AMBANG_URGENT  = ringkasan["Skor_Anomali"].quantile(0.95)
ringkasan["level"] = ringkasan["Skor_Anomali"].apply(
    lambda s: tentukan_level(s, AMBANG_WASPADA, AMBANG_URGENT)
)

n_urgent      = int((ringkasan["level"] == "urgent").sum())
n_waspada     = int((ringkasan["level"] == "waspada").sum())
n_tervalidasi = int(ringkasan["Sumber_Tervalidasi"].fillna(False).sum())


# ======================================================================
# KPI -- pakai st.metric supaya auto-update saat tanggal berubah
# ======================================================================
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div style="background:white;border:1px solid {WARNA["garis"]};border-top:3px solid {WARNA["aksen"]};border-radius:8px;padding:18px 20px"><div style="font-size:0.72rem;font-weight:600;color:{WARNA["teks_sub"]};text-transform:uppercase;letter-spacing:0.8px">Provinsi Dipantau</div><div style="font-family:IBM Plex Serif,serif;font-size:2.2rem;font-weight:700;margin-top:8px">{len(ringkasan)}</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div style="background:white;border:1px solid {WARNA["garis"]};border-top:3px solid {WARNA["urgent"]};border-radius:8px;padding:18px 20px"><div style="font-size:0.72rem;font-weight:600;color:{WARNA["teks_sub"]};text-transform:uppercase;letter-spacing:0.8px">Perlu Tindakan Segera</div><div style="font-family:IBM Plex Serif,serif;font-size:2.2rem;font-weight:700;margin-top:8px;color:{WARNA["urgent"] if n_urgent > 0 else WARNA["teks_utama"]}">{n_urgent}</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div style="background:white;border:1px solid {WARNA["garis"]};border-top:3px solid {WARNA["waspada"]};border-radius:8px;padding:18px 20px"><div style="font-size:0.72rem;font-weight:600;color:{WARNA["teks_sub"]};text-transform:uppercase;letter-spacing:0.8px">Perlu Dipantau</div><div style="font-family:IBM Plex Serif,serif;font-size:2.2rem;font-weight:700;margin-top:8px;color:{WARNA["waspada"] if n_waspada > 0 else WARNA["teks_utama"]}">{n_waspada}</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div style="background:white;border:1px solid {WARNA["garis"]};border-top:3px solid {WARNA["aman"]};border-radius:8px;padding:18px 20px"><div style="font-size:0.72rem;font-weight:600;color:{WARNA["teks_sub"]};text-transform:uppercase;letter-spacing:0.8px">Sumber Tervalidasi</div><div style="font-family:IBM Plex Serif,serif;font-size:2.2rem;font-weight:700;margin-top:8px">{n_tervalidasi}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ======================================================================
# PETA CHOROPLETH
# ======================================================================
st.markdown('<div class="sek-header">🗺️ Peta Anomali Harga per Provinsi</div>', unsafe_allow_html=True)

if geojson and geo_key:
    ringkasan["nama_geo"] = ringkasan["Provinsi"].apply(
        lambda p: cari_nama_geojson(p, geojson, geo_key)
    )
    ringkasan["level_num"] = ringkasan["level"].map({"aman": 0, "waspada": 1, "urgent": 2})

    df_peta = ringkasan.dropna(subset=["nama_geo"]).copy()

    if len(df_peta) > 0:
        fig_peta = px.choropleth(
            df_peta,
            geojson=geojson,
            locations="nama_geo",
            featureidkey=f"properties.{geo_key}",
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
                "nama_geo": False,
                "level_num": False,
            },
            labels={
                "Harga_Saat_Ini": "Harga (Rp)",
                "Perubahan_1Hari_Persen": "Δ Harian (%)",
                "Skor_Anomali": "Skor Anomali",
            },
        )
        fig_peta.update_geos(fitbounds="locations", visible=False, bgcolor=WARNA["latar"])
        fig_peta.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=420,
            paper_bgcolor=WARNA["latar"],
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_peta, use_container_width=True)
        st.markdown(f"""
        <div style="display:flex;gap:20px;font-size:0.80rem;margin-top:-8px;margin-bottom:8px">
            <span><span style="display:inline-block;width:12px;height:12px;background:#2E7D52;border-radius:2px;margin-right:5px;vertical-align:middle"></span>Stabil</span>
            <span><span style="display:inline-block;width:12px;height:12px;background:#B8860B;border-radius:2px;margin-right:5px;vertical-align:middle"></span>Perlu Dipantau</span>
            <span><span style="display:inline-block;width:12px;height:12px;background:#8B2635;border-radius:2px;margin-right:5px;vertical-align:middle"></span>Perlu Tindakan</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Nama provinsi tidak cocok dengan GeoJSON. Peta tidak dapat ditampilkan.")
else:
    st.info("⚠️ Peta tidak tersedia — GeoJSON gagal dimuat. Pastikan Streamlit Cloud punya akses internet.")


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
            pct = b["Perubahan_1Hari_Persen"]
            delta_str = ""
            if pd.notna(pct):
                arah = "▲" if pct > 0 else "▼"
                wc = delta_warna(pct)
                delta_str = f'<span style="color:{wc};font-weight:600">{arah} {abs(pct):.1f}%</span> dari hari sebelumnya'

            proj_str = ""
            if pd.notna(b["Prediksi_14_Hari"]):
                selisih = b["Prediksi_14_Hari"] - b["Harga_Saat_Ini"]
                arah_p = "▲" if selisih > 0 else "▼"
                wc_p = WARNA["urgent"] if selisih > 0 else WARNA["aman"]
                proj_str = f'<div style="font-size:0.85rem;color:{WARNA["teks_sub"]};margin-top:6px">Proyeksi 14 hari: <strong>Rp {b["Prediksi_14_Hari"]:,.0f}</strong> <span style="color:{wc_p}">{arah_p} Rp {abs(selisih):,.0f}</span></div>'
                if "waspada ekstra" in str(b["Status_Prediksi"]):
                    proj_str += f'<div style="font-size:0.75rem;color:{WARNA["waspada"]};margin-top:3px">⚠ Model cenderung meremehkan kenaikan di provinsi ini</div>'

            st.markdown(f"""
            <div class="prov-card">
                <div class="prov-name">{b['Provinsi']}</div>
                {badge_html(b['level'])}
                <div style="margin-top:12px">
                    <div class="prov-harga">Rp {b['Harga_Saat_Ini']:,.0f}</div>
                    <div style="font-size:0.82rem;color:{WARNA['teks_sub']};margin-top:2px">{delta_str}</div>
                </div>
                {proj_str}
            </div>
            """, unsafe_allow_html=True)

        with kol_b:
            if b["Sumber_Utama"] != "-" and pd.notna(b["Sumber_Utama"]):
                status = "✅ Tervalidasi" if b["Sumber_Tervalidasi"] else "❔ Belum terkonfirmasi"
                catatan = ""
                if not b["Sumber_Tervalidasi"]:
                    catatan = f'<div style="font-size:0.75rem;color:{WARNA["teks_sub"]};margin-top:8px">Provinsi sumber tidak menunjukkan pergerakan tak biasa di jeda waktu yang sesuai.</div>'
                st.markdown(f"""
                <div class="prov-card">
                    <div style="font-size:0.72rem;font-weight:600;color:{WARNA['teks_sub']};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px">Rantai Distribusi</div>
                    <div class="rantai">
                        <div style="font-weight:600;color:{WARNA['teks_utama']};margin-bottom:4px">{b['Sumber_Utama']} → {b['Provinsi']}</div>
                        <div style="color:{WARNA['teks_sub']};font-size:0.80rem;font-family:IBM Plex Mono,monospace">
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
                <div class="prov-card">
                    <span style="color:{WARNA['teks_sub']};font-size:0.85rem">Tidak ada provinsi sumber yang tervalidasi secara statistik untuk provinsi ini.</span>
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
fig.add_trace(go.Scatter(
    x=harga_historis.index, y=harga_historis.values,
    fill="tozeroy", fillcolor="rgba(45,95,138,0.06)",
    line=dict(color=WARNA["aksen"], width=2),
    name="Harga historis",
))

if cerita["prediksi_14_hari"]:
    tgl_proj = pd.Timestamp(tanggal_dipilih) + pd.tseries.offsets.BDay(14)
    harga_terakhir = float(harga_historis.iloc[-1])
    selisih = cerita["prediksi_14_hari"] - harga_terakhir
    wc_proj = WARNA["urgent"] if selisih > 0 else WARNA["aman"]
    fig.add_trace(go.Scatter(
        x=[harga_historis.index[-1], tgl_proj],
        y=[harga_terakhir, cerita["prediksi_14_hari"]],
        mode="lines", line=dict(color=wc_proj, width=1.5, dash="dot"), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[tgl_proj], y=[cerita["prediksi_14_hari"]],
        mode="markers+text",
        marker=dict(size=12, symbol="diamond", color=wc_proj, line=dict(color="white", width=2)),
        text=[f"  Rp {cerita['prediksi_14_hari']:,.0f}"],
        textposition="middle right",
        textfont=dict(size=11, color=wc_proj),
        name="Proyeksi +14 hari",
    ))

fig.update_layout(
    plot_bgcolor="white", paper_bgcolor=WARNA["latar"],
    font=dict(family="IBM Plex Sans", color=WARNA["teks_utama"], size=12),
    yaxis_title="Harga (Rp)",
    yaxis=dict(gridcolor="#F0EDE6", tickformat=",.0f"),
    xaxis=dict(gridcolor="#F0EDE6"),
    height=360, margin=dict(t=16, b=16, l=16, r=16),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True)

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
                <div style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;color:{WARNA['aksen']}">lag {sumber['lag_hari']}h · {sumber['kekuatan_r2']*100:.1f}%</div>
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
