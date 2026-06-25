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

def tentukan_level(skor, waspada, urgent, pct_change=None):
    if skor is None or pd.isna(skor): return "aman"
    sedang_turun = pct_change is not None and not pd.isna(pct_change) and pct_change < 0
    if skor >= urgent:
        return "waspada" if sedang_turun else "urgent"
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
    # Pakai sumber yang sudah terbukti punya key "Propinsi"
    url = "https://raw.githubusercontent.com/ans-4175/peta-indonesia-geojson/master/indonesia-prov.geojson"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

geojson = muat_geojson()
geo_key = "Propinsi"

# Mapping khusus untuk nama yang tidak bisa dikonversi langsung ke uppercase
NAMA_KHUSUS = {
    "Aceh":                      "DI. ACEH",
    "DI Yogyakarta":             "DAERAH ISTIMEWA YOGYAKARTA",
    "Kepulauan Bangka Belitung": "BANGKA BELITUNG",
    "Nusa Tenggara Barat":       "NUSATENGGARA BARAT",
}

def cari_nama_geojson(provinsi, geojson, key):
    # Cek mapping khusus dulu
    if provinsi in NAMA_KHUSUS:
        return NAMA_KHUSUS[provinsi]
    # Sisanya tinggal uppercase
    return provinsi.upper()


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
    tgl_min = daftar_tanggal[0]
    tgl_max = daftar_tanggal[-1]
    tanggal_dipilih = st.date_input(
        "📅 Tanggal pemantauan",
        value=tgl_max,
        min_value=tgl_min,
        max_value=tgl_max,
    )
    # Snap ke tanggal terdekat yang ada di data
    import bisect
    idx = bisect.bisect_right(daftar_tanggal, tanggal_dipilih) - 1
    idx = max(0, min(idx, len(daftar_tanggal) - 1))
    tanggal_dipilih = daftar_tanggal[idx]


# ======================================================================
# BANGUN RINGKASAN -- ini dijalankan ulang setiap tanggal berubah
# ======================================================================
with st.spinner("Menyusun analisis..."):
    ringkasan = bangun_ringkasan_semua_provinsi(aset, tanggal_dipilih)

# Ambang batas ABSOLUT berdasarkan distribusi skor keseluruhan data
# (bukan persentil per hari, supaya tidak selalu ada 2 urgent)
AMBANG_WASPADA = 0.58
AMBANG_URGENT  = 0.65

ringkasan["level"] = ringkasan.apply(
    lambda r: tentukan_level(r["Skor_Anomali"], AMBANG_WASPADA, AMBANG_URGENT, r["Perubahan_1Hari_Persen"]),
    axis=1
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
# PETA CHOROPLETH -- gradasi skor anomali continuous
# ======================================================================
st.markdown('<div class="sek-header">🗺️ Peta Anomali Harga per Provinsi</div>', unsafe_allow_html=True)

if geojson and geo_key:
    ringkasan["nama_geo"] = ringkasan["Provinsi"].apply(
        lambda p: cari_nama_geojson(p, geojson, geo_key)
    )
    # Isi NaN dengan 0 supaya semua provinsi tetap muncul di peta
    ringkasan["Skor_Anomali"] = ringkasan["Skor_Anomali"].fillna(0)

    df_peta = ringkasan.dropna(subset=["nama_geo"]).copy()

    if len(df_peta) > 0:
        fig_peta = px.choropleth(
            df_peta,
            geojson=geojson,
            locations="nama_geo",
            featureidkey=f"properties.{geo_key}",
            color="Skor_Anomali",
            color_continuous_scale=[
                [0.0,  "#2E7D52"],
                [0.4,  "#7FB069"],
                [0.6,  "#E9C46A"],
                [0.75, "#B8860B"],
                [1.0,  "#8B2635"],
            ],
            range_color=[df_peta["Skor_Anomali"].min(), df_peta["Skor_Anomali"].max()],
            hover_name="Provinsi",
            hover_data={
                "Harga_Saat_Ini": ":,.0f",
                "Perubahan_1Hari_Persen": ":.1f",
                "Skor_Anomali": ":.3f",
                "nama_geo": False,
            },
            labels={
                "Skor_Anomali": "Skor Anomali",
                "Harga_Saat_Ini": "Harga (Rp)",
                "Perubahan_1Hari_Persen": "Δ Harian (%)",
            },
        fig_peta.update_geos(
            visible=False,
            bgcolor=WARNA["latar"],
            lonaxis_range=[94, 142],
            lataxis_range=[-12, 8],
        )
        fig_peta.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=400,
            paper_bgcolor=WARNA["latar"],
            geo=dict(
                projection_type="mercator",
                lonaxis_range=[94, 142],
                lataxis_range=[-12, 8],
            ),
            coloraxis=dict(
                colorbar=dict(
                    title="Skor<br>Anomali",
                    thickness=12,
                    len=0.6,
                    tickformat=".2f",
                )
            ),
        )
        st.plotly_chart(fig_peta, use_container_width=True)
        st.markdown(f"""
        <div style="display:flex;gap:20px;font-size:0.80rem;margin-top:-8px;margin-bottom:8px">
            <span><span style="display:inline-block;width:12px;height:12px;background:#2E7D52;border-radius:2px;margin-right:5px;vertical-align:middle"></span>Skor rendah (stabil)</span>
            <span><span style="display:inline-block;width:12px;height:12px;background:#E9C46A;border-radius:2px;margin-right:5px;vertical-align:middle"></span>Skor sedang</span>
            <span><span style="display:inline-block;width:12px;height:12px;background:#8B2635;border-radius:2px;margin-right:5px;vertical-align:middle"></span>Skor tinggi (anomali)</span>
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
