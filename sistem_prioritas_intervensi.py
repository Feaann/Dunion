# ======================================================================
# BACKEND: SISTEM PRIORITAS INTERVENSI
# Menggabungkan 3 komponen yang sudah dibangun jadi 1 "cerita" per provinsi:
#   1. Isolation Forest -> skor "seberapa aneh" harga hari ini
#   2. Granger Causality -> kandidat sumber + lag + kekuatan pengaruh
#   3. RF-Granger -> prediksi harga 14 hari ke depan
#
# Modul ini dipanggil oleh dashboard (dashboard_dunion.py). Bisa juga
# dijalankan sendiri buat ngecek hasilnya di terminal/Colab.
# ======================================================================

import glob
import warnings

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

FOLDER_DATA = "data_bersih"
FOLDER_ANOMALI = "hasil_anomali"
FOLDER_GRANGER = "hasil_granger"
FOLDER_KEKUATAN = "hasil_granger_kekuatan"
FOLDER_MODEL_RF = "hasil_prediksi_granger_rf/model_tersimpan"

# Provinsi yang diketahui modelnya cenderung meremehkan kenaikan harga
# (ditemukan saat diagnosis -- bias > 1000 rupiah, selalu ke arah bawah)
PROVINSI_BIAS_RENDAH = {"Gorontalo", "Bali", "Nusa Tenggara Barat"}

HORIZON = 14


# ======================================================================
# MUAT SEMUA ASET SEKALI (dipanggil sekali, dipakai berkali-kali)
# ======================================================================
def muat_aset():
    harga = pd.read_csv(f"{FOLDER_DATA}/harga_bersih.csv", parse_dates=["Tanggal"])
    harga_wide = harga.pivot(index="Tanggal", columns="Provinsi", values="Harga").sort_index()
    delta_wide = harga_wide.diff()

    anomali = pd.read_csv(f"{FOLDER_ANOMALI}/anomali_harga.csv", parse_dates=["Tanggal"])

    granger = pd.read_csv(f"{FOLDER_GRANGER}/granger_hasil_lengkap.csv")
    granger_sig = granger[granger["signifikan"]]
    peta_sumber = granger_sig.groupby("Provinsi_Tujuan")["Provinsi_Asal"].unique().to_dict()

    try:
        kekuatan = pd.read_csv(f"{FOLDER_KEKUATAN}/kekuatan_hubungan_granger.csv")
    except FileNotFoundError:
        kekuatan = pd.DataFrame(columns=["Provinsi_Asal", "Provinsi_Tujuan", "lag_hari", "kekuatan_tambahan_R2"])

    model_rf = {}
    for file_model in glob.glob(f"{FOLDER_MODEL_RF}/rf_*.joblib"):
        paket = joblib.load(file_model)
        nama_dari_file = file_model.split("rf_")[-1].replace(".joblib", "").replace("_", " ")
        provinsi_asli = next((p for p in peta_sumber if p.replace(" ", "_") == file_model.split("rf_")[-1].replace(".joblib", "")), nama_dari_file)
        model_rf[provinsi_asli] = paket

    return {
        "harga_wide": harga_wide,
        "delta_wide": delta_wide,
        "anomali": anomali,
        "peta_sumber": peta_sumber,
        "kekuatan": kekuatan,
        "model_rf": model_rf,
        "semua_provinsi": sorted(harga_wide.columns),
    }


# ======================================================================
# FUNGSI UTAMA: bangun "cerita" lengkap 1 provinsi pada 1 tanggal acuan
# ======================================================================
def bangun_cerita_provinsi(aset, provinsi, tanggal_acuan):
    tanggal_acuan = pd.Timestamp(tanggal_acuan)
    hasil = {"provinsi": provinsi, "tanggal": tanggal_acuan}

    # --- 1. SKOR ANOMALI ---
    baris_anomali = aset["anomali"][
        (aset["anomali"]["Provinsi"] == provinsi) & (aset["anomali"]["Tanggal"] == tanggal_acuan)
    ]
    if len(baris_anomali) == 0:
        hasil["skor_anomali"] = None
        hasil["harga_saat_ini"] = aset["harga_wide"].loc[:tanggal_acuan, provinsi].iloc[-1] if provinsi in aset["harga_wide"].columns else None
        hasil["pct_change_1h"] = None
    else:
        hasil["skor_anomali"] = float(baris_anomali["skor_anomali"].iloc[0])
        hasil["harga_saat_ini"] = float(baris_anomali["Harga"].iloc[0])
        hasil["pct_change_1h"] = float(baris_anomali["pct_change_1h"].iloc[0])

    # --- 2. KANDIDAT SUMBER (Granger), diurutkan dari paling kuat ---
    sumber_list = aset["peta_sumber"].get(provinsi, [])
    kandidat_sumber = []
    for sumber in sumber_list:
        baris_kekuatan = aset["kekuatan"][
            (aset["kekuatan"]["Provinsi_Asal"] == sumber) & (aset["kekuatan"]["Provinsi_Tujuan"] == provinsi)
        ]
        if len(baris_kekuatan) == 0:
            continue
        lag = int(baris_kekuatan["lag_hari"].iloc[0])
        kekuatan_r2 = float(baris_kekuatan["kekuatan_tambahan_R2"].iloc[0])

        # VALIDASI: apakah provinsi sumber ini JUGA menunjukkan pergerakan
        # tak biasa di sekitar (lag) hari kerja sebelum tanggal_acuan?
        tanggal_kira_kira_sumber = tanggal_acuan - pd.tseries.offsets.BDay(lag)
        jendela_cek = aset["delta_wide"][sumber].loc[
            tanggal_kira_kira_sumber - pd.tseries.offsets.BDay(2): tanggal_kira_kira_sumber + pd.tseries.offsets.BDay(2)
        ]
        std_sumber = aset["delta_wide"][sumber].std()
        tervalidasi = bool((jendela_cek.abs() > 1.5 * std_sumber).any()) if len(jendela_cek) > 0 and std_sumber > 0 else False

        kandidat_sumber.append({
            "provinsi_asal": sumber,
            "lag_hari": lag,
            "kekuatan_r2": kekuatan_r2,
            "tervalidasi": tervalidasi,
        })

    kandidat_sumber.sort(key=lambda x: x["kekuatan_r2"], reverse=True)
    hasil["kandidat_sumber"] = kandidat_sumber

    # --- 3. PREDIKSI RF-GRANGER (14 hari ke depan) ---
    if provinsi in aset["model_rf"]:
        paket = aset["model_rf"][provinsi]
        model, kolom_fitur = paket["model"], paket["kolom_fitur"]
        try:
            fitur_baris = {}
            for lag in paket["lag_ar"]:
                fitur_baris[f"AR_{provinsi}_lag{lag}"] = aset["delta_wide"][provinsi].shift(lag).loc[tanggal_acuan]
            for sumber in paket["sumber_signifikan"]:
                for lag in paket["lag_asal"]:
                    fitur_baris[f"{sumber}_lag{lag}"] = aset["delta_wide"][sumber].shift(lag).loc[tanggal_acuan]
            X_baris = pd.DataFrame([fitur_baris])[kolom_fitur]
            if X_baris.isna().any(axis=1).iloc[0]:
                hasil["prediksi_14_hari"] = None
                hasil["status_prediksi"] = "Data tidak cukup untuk prediksi di tanggal ini"
            else:
                delta_pred = model.predict(X_baris)[0]
                hasil["prediksi_14_hari"] = hasil["harga_saat_ini"] + delta_pred if hasil["harga_saat_ini"] else None
                hasil["status_prediksi"] = "OK"
                if provinsi in PROVINSI_BIAS_RENDAH:
                    hasil["status_prediksi"] = "OK (model cenderung meremehkan kenaikan di provinsi ini -- waspada ekstra)"
        except KeyError:
            hasil["prediksi_14_hari"] = None
            hasil["status_prediksi"] = "Data tidak cukup untuk prediksi di tanggal ini"
    else:
        hasil["prediksi_14_hari"] = None
        hasil["status_prediksi"] = "Data tidak cukup -- tidak ada sumber Granger yang tervalidasi untuk provinsi ini"

    return hasil


# ======================================================================
# BANGUN RINGKASAN SEMUA PROVINSI DI 1 TANGGAL (buat tabel prioritas)
# ======================================================================
def bangun_ringkasan_semua_provinsi(aset, tanggal_acuan):
    daftar_hasil = []
    for provinsi in aset["semua_provinsi"]:
        cerita = bangun_cerita_provinsi(aset, provinsi, tanggal_acuan)
        sumber_utama = cerita["kandidat_sumber"][0] if cerita["kandidat_sumber"] else None
        daftar_hasil.append({
            "Provinsi": provinsi,
            "Skor_Anomali": cerita["skor_anomali"],
            "Harga_Saat_Ini": cerita["harga_saat_ini"],
            "Perubahan_1Hari_Persen": cerita["pct_change_1h"],
            "Sumber_Utama": sumber_utama["provinsi_asal"] if sumber_utama else "-",
            "Lag_Hari": sumber_utama["lag_hari"] if sumber_utama else None,
            "Kekuatan_Sumber": sumber_utama["kekuatan_r2"] if sumber_utama else None,
            "Sumber_Tervalidasi": sumber_utama["tervalidasi"] if sumber_utama else None,
            "Prediksi_14_Hari": cerita["prediksi_14_hari"],
            "Status_Prediksi": cerita["status_prediksi"],
        })
    return pd.DataFrame(daftar_hasil).sort_values("Skor_Anomali", ascending=False)


# ======================================================================
# TES MANDIRI (jalankan langsung file ini buat ngecek backend-nya)
# ======================================================================
if __name__ == "__main__":
    aset = muat_aset()

    print("Contoh cerita lengkap -- Kepulauan Bangka Belitung, 2024-04-17:")
    cerita = bangun_cerita_provinsi(aset, "Kepulauan Bangka Belitung", "2024-04-17")
    import json
    print(json.dumps(cerita, indent=2, default=str))

    print("\n\nRingkasan TOP 10 provinsi paling anomali di 2024-04-17:")
    ringkasan = bangun_ringkasan_semua_provinsi(aset, "2024-04-17")
    print(ringkasan.head(10).to_string(index=False))
