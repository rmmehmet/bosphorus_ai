"""
Bosphorus AI Tool'ları:
Her tool bağımsız bir fonksiyondur ve string döner (LLM'e aktarılacak metin).
"""
import os
from datetime import datetime
import pandas as pd
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
ISTANBUL_LAT = 41.0082
ISTANBUL_LON = 28.9784


def get_holidays() -> str:
    path = os.path.join(DATA_DIR, "holidays.xlsx")
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    lines = ["Türkiye Resmi Tatilleri:"]
    for _, row in df.iterrows():
        tarih = str(row.get("Tarih / Dönem", "")).strip()
        gun = str(row.get("Gün", "")).strip()
        tatil = str(row.get("Tatil / Bayram", "")).strip()
        tur = str(row.get("Türü", "")).strip()
        sure = str(row.get("Süre", "")).strip()
        lines.append(f"- {tarih} ({gun}): {tatil} [{tur}, {sure}]")
    return "\n".join(lines)


def get_vehicles() -> str:
    path = os.path.join(DATA_DIR, "vehicles.xlsx")
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    lines = ["Araç Yakıt Tüketim Verileri (100km/L):"]
    df_sorted = df.sort_values("consumption")
    for _, row in df_sorted.iterrows():
        brand = str(row.get("brand", "")).strip()
        cons = row.get("consumption", "?")
        atype = str(row.get("type", "")).strip()
        luggage = row.get("luggage space(L)", "?")
        seater = row.get("seater", "?")
        lines.append(
            f"- {brand}: {cons} L/100km | Tip: {atype} | Bagaj: {luggage}L | {seater} kişilik"
        )
    return "\n".join(lines)


def get_weather_from_excel() -> str:
    path = os.path.join(DATA_DIR, "weather.xlsx")
    df = pd.read_excel(path, header=0)
    months_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

    now = datetime.now()
    current_month = months_tr[now.month - 1]
    metric_col = df.columns[0]
    result = [f"İstanbul Ortalama İklim Verileri ({current_month} ayı, 1950-2025):"]

    for _, row in df.iterrows():
        metric = str(row[metric_col]).strip()
        if "Ölçüm" in metric or metric == "nan":
            continue
        val = row.get(current_month, None)
        if pd.notna(val):
            result.append(f"- {metric}: {val}")

    result.append(f"\nYıllık Genel Ortalama:")
    for _, row in df.iterrows():
        metric = str(row[metric_col]).strip()
        if "Ölçüm" in metric or metric == "nan":
            continue
        val = row.get("Yıllık", None)
        if pd.notna(val):
            result.append(f"- {metric}: {val}")

    return "\n".join(result)


def get_current_weather_api() -> str:
    params = {
        "latitude": ISTANBUL_LAT,
        "longitude": ISTANBUL_LON,
        "current": ["temperature_2m", "relative_humidity_2m", "precipitation",
                    "wind_speed_10m", "weather_code"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                  "weather_code"],
        "timezone": "Europe/Istanbul",
        "forecast_days": 7,
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        cur = data.get("current", {})
        lines = [
            f"İstanbul Güncel Hava Durumu ({cur.get('time', 'bilinmiyor')}):",
            f"- Sıcaklık: {cur.get('temperature_2m', '?')}°C",
            f"- Nem: {cur.get('relative_humidity_2m', '?')}%",
            f"- Yağış: {cur.get('precipitation', '?')} mm",
            f"- Rüzgar: {cur.get('wind_speed_10m', '?')} km/h",
            f"- Durum: {wmo_to_text(cur.get('weather_code', 0))}",
            "",
            "7 Günlük Tahmin:",
        ]

        daily = data.get("daily", {})
        for i, date in enumerate(daily.get("time", [])):
            tmax = daily["temperature_2m_max"][i]
            tmin = daily["temperature_2m_min"][i]
            prec = daily["precipitation_sum"][i]
            wcode = daily["weather_code"][i]
            lines.append(
                f"- {date}: {tmin}°C / {tmax}°C | {wmo_to_text(wcode)} | Yağış: {prec}mm"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Güncel hava durumu alınamadı: {str(e)}"


def wmo_to_text(code: int) -> str:
    mapping = {
        0: "Açık", 1: "Az bulutlu", 2: "Parçalı bulutlu", 3: "Bulutlu",
        45: "Sisli", 48: "Kırağılı sis",
        51: "Hafif çisenti", 53: "Orta çisenti", 55: "Yoğun çisenti",
        61: "Hafif yağmur", 63: "Orta yağmur", 65: "Şiddetli yağmur",
        71: "Hafif kar", 73: "Orta kar", 75: "Yoğun kar",
        80: "Hafif sağanak", 81: "Orta sağanak", 82: "Şiddetli sağanak",
        95: "Fırtınalı", 96: "Doluşlu fırtına", 99: "Şiddetli fırtına",
    }
    return mapping.get(code, f"Kod {code}")


def get_current_date_info() -> str:
    now = datetime.now()
    months_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

    day_name = days_tr[now.weekday()]
    month_name = months_tr[now.month - 1]
    is_weekend = now.weekday() >= 5

    info = [
        f"Bugünün tarihi: {now.day} {month_name} {now.year} {day_name}",
        f"Hafta sonu: {'Evet' if is_weekend else 'Hayır'}",
    ]

    path = os.path.join(DATA_DIR, "holidays.xlsx")
    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]
    today_str = f"{now.day} {month_name}"

    matched = []
    for _, row in df.iterrows():
        t = str(row.get("Tarih / Dönem", "")).strip()
        if today_str in t or t in today_str:
            tatil = str(row.get("Tatil / Bayram", "")).strip()
            matched.append(tatil)

    if matched:
        info.append(f"Bugün resmi tatil: EVET - {', '.join(matched)}")
    else:
        info.append("Bugün resmi tatil: Hayır (sabit tarihli tatillere göre)")

    return "\n".join(info)