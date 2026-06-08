import os
from datetime import datetime
import pandas as pd
import requests

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
WIKIPEDIA_API = "https://tr.wikipedia.org/w/api.php"
OVERPASS_API = "https://overpass-api.de/api/interpreter"  # IETT yerine OSM tabanlı
ISTANBUL_LAT = 41.0082
ISTANBUL_LON = 28.9784


# ---------------------------------------------------------------------------
# Tatil
# ---------------------------------------------------------------------------

def get_holidays() -> str:
    path = os.path.join(DATA_DIR, "holidays.xlsx")
    try:
        df = pd.read_excel(path, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        lines = ["Türkiye Resmi Tatilleri:"]
        for _, row in df.iterrows():
            tarih = str(row.get("Tarih / Dönem", "")).strip()
            gun = str(row.get("Gün", "")).strip()
            tatil = str(row.get("Tatil / Bayram", "")).strip()
            tur = str(row.get("Türü", "")).strip()
            sure = str(row.get("Süre", "")).strip()
            if tatil and tatil != "nan":
                lines.append(f"- {tarih} ({gun}): {tatil} [{tur}, {sure}]")
        return "\n".join(lines)
    except FileNotFoundError:
        return "⚠️ holidays.xlsx bulunamadı. data/ klasörüne ekleyin."
    except Exception as e:
        return f"⚠️ Tatil verisi okunamadı: {e}"


# ---------------------------------------------------------------------------
# Araçlar
# ---------------------------------------------------------------------------

def get_vehicles() -> str:
    path = os.path.join(DATA_DIR, "vehicles.xlsx")
    try:
        df = pd.read_excel(path, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        lines = ["Araç Yakıt Tüketim Verileri (L/100km):"]
        for _, row in df.sort_values("consumption").iterrows():
            lines.append(
                f"- {row.get('brand', '?')}: {row.get('consumption', '?')} L/100km"
                f" | {row.get('type', '?')} | Bagaj: {row.get('luggage space(L)', '?')}L"
                f" | {row.get('seater', '?')} kişilik"
            )
        return "\n".join(lines)
    except FileNotFoundError:
        return "⚠️ vehicles.xlsx bulunamadı. data/ klasörüne ekleyin."
    except Exception as e:
        return f"⚠️ Araç verisi okunamadı: {e}"


# ---------------------------------------------------------------------------
# Hava — Excel (tarihsel) + API (güncel) birleşimi
# ---------------------------------------------------------------------------

def get_weather_from_excel() -> str:
    """
    Excel'deki tarihsel iklim ortalamalarını okur.
    Dosya yoksa veya bozuksa hata döndürür — agent API fallback'e geçer.
    """
    path = os.path.join(DATA_DIR, "weather.xlsx")
    if not os.path.exists(path):
        raise FileNotFoundError("weather.xlsx bulunamadı")

    df = pd.read_excel(path, header=0, engine="openpyxl")
    months_tr = [
        "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
    ]
    current_month = months_tr[datetime.now().month - 1]

    # Kolon adı normalize edilirken boşluklar kaldırılır, böylece "Sıcaklık (°C)" → "Sıcaklık(°C)" olur ve LLM'in parametre eşleştirmesi kolaylaşır
    df.columns = [str(c).strip() for c in df.columns]
    metric_col = df.columns[0]

    # Hedef ay kolonu var mı kontrolü — eğer yoksa Excel yapısı değişmiş olabilir, bu durumda hata fırlatılır ve agent API'ye geçer
    if current_month not in df.columns:
        raise ValueError(f"Excel'de '{current_month}' kolonu yok. Mevcut: {list(df.columns)}")

    result = [f"İstanbul Tarihsel İklim Ortalamaları ({current_month}, 1950-2025):"]
    for _, row in df.iterrows():
        metric = str(row[metric_col]).strip()
        if metric in ("", "nan", "Ölçüm"):
            continue
        val = row.get(current_month)
        if pd.notna(val):
            result.append(f"- {metric}: {val}")

    if len(result) == 1:
        raise ValueError("Excel'den hiç veri okunamadı.")

    return "\n".join(result)


def get_current_weather_api() -> str:
    """Open-Meteo API ile anlık + 7 günlük tahmin."""
    params = {
        "latitude": ISTANBUL_LAT,
        "longitude": ISTANBUL_LON,
        "current": [
            "temperature_2m", "apparent_temperature",
            "relative_humidity_2m", "precipitation",
            "wind_speed_10m", "weather_code",
        ],
        "daily": [
            "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "weather_code",
        ],
        "timezone": "Europe/Istanbul",
        "forecast_days": 7,
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cur = data.get("current", {})

        lines = [
            f"İstanbul Anlık Hava ({cur.get('time', '?')}):",
            f"- Sıcaklık: {cur.get('temperature_2m', '?')}°C"
            f" (Hissedilen: {cur.get('apparent_temperature', '?')}°C)",
            f"- Nem: {cur.get('relative_humidity_2m', '?')}%",
            f"- Yağış: {cur.get('precipitation', '?')} mm",
            f"- Rüzgar: {cur.get('wind_speed_10m', '?')} km/h",
            f"- Durum: {_wmo(cur.get('weather_code', 0))}",
            "",
            "7 Günlük Tahmin:",
        ]
        daily = data.get("daily", {})
        for i, date in enumerate(daily.get("time", [])):
            lines.append(
                f"- {date}: {daily['temperature_2m_min'][i]}°C / {daily['temperature_2m_max'][i]}°C"
                f" | {_wmo(daily['weather_code'][i])}"
                f" | Yağış: {daily['precipitation_sum'][i]} mm"
            )
        return "\n".join(lines)
    except requests.exceptions.Timeout:
        return "⚠️ Open-Meteo API zaman aşımı."
    except Exception as e:
        return f"⚠️ Güncel hava alınamadı: {e}"


def _wmo(code: int) -> str:
    m = {
        0: "Açık ☀️",
        1: "Az bulutlu 🌤",
        2: "Parçalı bulutlu ⛅",
        3: "Bulutlu ☁️",
        45: "Sisli 🌫",
        48: "Dondurucu sis 🌫",
        51: "Hafif çisenti 🌦",
        53: "Çisenti 🌦",
        61: "Hafif yağmur 🌧",
        63: "Yağmur 🌧",
        65: "Şiddetli yağmur 🌧",
        71: "Hafif kar 🌨",
        73: "Kar 🌨",
        75: "Yoğun kar ❄️",
        80: "Sağanak 🌦",
        81: "Kuvvetli sağanak 🌦",
        95: "Gök gürültülü fırtına ⛈",
        99: "Dolu ile fırtına ⛈",
    }
    return m.get(code, f"Durum kodu {code}")


# ---------------------------------------------------------------------------
# Tarih bilgisi
# ---------------------------------------------------------------------------

def get_current_date_info() -> str:
    now = datetime.now()
    months_tr = [
        "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
    ]
    days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    month_name = months_tr[now.month - 1]
    info = [
        f"Bugün: {now.day} {month_name} {now.year} {days_tr[now.weekday()]}",
        f"Saat: {now.strftime('%H:%M')}",
        f"Hafta sonu: {'Evet' if now.weekday() >= 5 else 'Hayır'}",
    ]
    try:
        path = os.path.join(DATA_DIR, "holidays.xlsx")
        df = pd.read_excel(path, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        today_str = f"{now.day} {month_name}"
        matched = [
            str(row.get("Tatil / Bayram", "")).strip()
            for _, row in df.iterrows()
            if today_str in str(row.get("Tarih / Dönem", ""))
        ]
        info.append(f"Resmi tatil: {'EVET — ' + ', '.join(matched) if matched else 'Hayır'}")
    except Exception:
        info.append("Resmi tatil: Kontrol edilemedi (holidays.xlsx yok)")
    return "\n".join(info)


# ---------------------------------------------------------------------------
# İstanbul tarihi yerler (Wikipedia)
# ---------------------------------------------------------------------------

def get_istanbul_historic_places(query: str = "İstanbul tarihi yerler") -> str:
    try:
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 3,
            "srnamespace": 0,
        }
        resp = requests.get(WIKIPEDIA_API, params=search_params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
        if not results:
            return f"'{query}' için Wikipedia'da sonuç bulunamadı."

        lines = [f"Wikipedia — {query}:"]
        for r in results:
            snippet = (
                r["snippet"]
                .replace('<span class="searchmatch">', "")
                .replace("</span>", "")
            )
            lines.append(f"- {r['title']}: {snippet}...")

        # İlk sonucun özeti
        summary_params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": results[0]["title"],
            "format": "json",
        }
        s = requests.get(WIKIPEDIA_API, params=summary_params, timeout=10)
        for page in s.json().get("query", {}).get("pages", {}).values():
            extract = page.get("extract", "")
            if extract:
                lines.append(f"\n{results[0]['title']}:\n{extract[:600]}")

        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Wikipedia verisi alınamadı: {e}"


# ---------------------------------------------------------------------------
# Toplu taşıma — Overpass API (OpenStreetMap) ile İstanbul hat/durak bilgisi
# IETT resmi API güvenilmez olduğu için OSM tabanlı ücretsiz alternatif kullanılıyor
# ---------------------------------------------------------------------------

def get_iett_bus_lines(hat_kodu: str = "") -> str:
    """
    OpenStreetMap Overpass API üzerinden İstanbul toplu taşıma güzergâhlarını sorgular.
    hat_kodu boş bırakılırsa Kadıköy–Taksim gibi popüler hatları döndürür.
    """
    try:
        if hat_kodu:
            # Belirli bir hat adını / referansını ara
            query = f"""
[out:json][timeout:25];
area["name"="İstanbul"]["admin_level"="4"]->.istanbul;
(
  relation["type"="route"]["route"="bus"]["ref"~"^{hat_kodu}$",i](area.istanbul);
  relation["type"="route"]["route"="tram"]["ref"~"^{hat_kodu}$",i](area.istanbul);
  relation["type"="route"]["route"="subway"]["ref"~"^{hat_kodu}$",i](area.istanbul);
);
out tags;
"""
        else:
            # Popüler hatlardan örnekler
            query = """
[out:json][timeout:25];
area["name"="İstanbul"]["admin_level"="4"]->.istanbul;
(
  relation["type"="route"]["route"="bus"]["operator"~"İETT|IETT",i](area.istanbul);
  relation["type"="route"]["route"="subway"](area.istanbul);
  relation["type"="route"]["route"="tram"](area.istanbul);
  relation["type"="route"]["route"="ferry"](area.istanbul);
);
out tags 20;
"""

        resp = requests.post(
            OVERPASS_API,
            data={"data": query},
            timeout=30,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])

        if not elements:
            # Fallback: statik popüler İstanbul hatları
            return _static_istanbul_transit(hat_kodu)

        lines_out = [
            f"İstanbul Toplu Taşıma Güzergâhları"
            f"{' — Ref: ' + hat_kodu.upper() if hat_kodu else ''} (OpenStreetMap):"
        ]
        for el in elements[:15]:
            tags = el.get("tags", {})
            ref = tags.get("ref", "—")
            name = tags.get("name", tags.get("from", "?") + " → " + tags.get("to", "?"))
            route = tags.get("route", "?").capitalize()
            operator = tags.get("operator", "")
            lines_out.append(
                f"- [{route}] {ref}: {name}"
                + (f" ({operator})" if operator else "")
            )

        if len(elements) > 15:
            lines_out.append(f"... ve {len(elements) - 15} güzergâh daha")

        return "\n".join(lines_out)

    except requests.exceptions.Timeout:
        return _static_istanbul_transit(hat_kodu)
    except Exception as e:
        return _static_istanbul_transit(hat_kodu)


def _static_istanbul_transit(hat_kodu: str = "") -> str:
    """
    Overpass erişilemez olduğunda gösterilen statik İstanbul toplu taşıma özeti.
    """
    lines = [
        "İstanbul Toplu Taşıma — Temel Hat Bilgileri:",
        "Metro:",
        "- M1A/M1B: Yenikapı – Atatürk Havalimanı / Kirazlı",
        "- M2: Yenikapı – Hacıosman",
        "- M3: Kirazlı – Olimpiyat",
        "- M4: Kadıköy – Sabiha Gökçen Havalimanı",
        "- M5: Üsküdar – Çekmeköy",
        "- M6: Levent – Boğaziçi Üni.",
        "- M7: Mecidiyeköy – Kabataş",
        "Tramvay:",
        "- T1: Kabataş – Bağcılar (Tarihi Yarımada geçişi)",
        "- T3: Kadıköy – Moda",
        "Vapur:",
        "- Eminönü ↔ Kadıköy, Eminönü ↔ Üsküdar (IDO/Şehir Hatları)",
        "- Karaköy ↔ Haydarpaşa",
        "Marmaray:",
        "- Halkalı – Gebze (Boğaz altı geçişi, Kazlıçeşme – Ayrılıkçeşme arası)",
    ]
    if hat_kodu:
        lines.insert(1, f"⚠️ '{hat_kodu.upper()}' için anlık veri alınamadı, genel bilgi gösteriliyor.")
    return "\n".join(lines)