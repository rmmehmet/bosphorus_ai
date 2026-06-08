from fastmcp import FastMCP
from tools import (
    get_holidays,
    get_vehicles,
    get_weather_from_excel,
    get_current_weather_api,
    get_current_date_info,
    get_istanbul_historic_places,
    get_iett_bus_lines,
)

mcp = FastMCP("Bosphorus AI")


@mcp.tool()
def tatiller() -> str:
    """Türkiye resmi tatillerini listeler."""
    return get_holidays()


@mcp.tool()
def araclar() -> str:
    """Araç yakıt tüketim verilerini getirir."""
    return get_vehicles()


@mcp.tool()
def istanbul_iklim() -> str:
    """İstanbul historik ortalama iklim verileri (Excel kaynaklı)."""
    try:
        return get_weather_from_excel()
    except FileNotFoundError:
        return "⚠️ weather.xlsx bulunamadı. Güncel API verisi kullanılıyor:\n" + get_current_weather_api()


@mcp.tool()
def istanbul_hava() -> str:
    """İstanbul anlık sıcaklık ve 7 günlük hava tahmini (Open-Meteo)."""
    return get_current_weather_api()


@mcp.tool()
def bugun() -> str:
    """Bugünün tarihi, günü ve resmi tatil durumu."""
    return get_current_date_info()


@mcp.tool()
def tarihi_yerler(sorgu: str = "İstanbul tarihi yerler") -> str:
    """İstanbul tarihi ve turistik yerler hakkında bilgi. Örn: sorgu='Ayasofya'"""
    return get_istanbul_historic_places(sorgu)


@mcp.tool()
def toplu_tasima(hat_kodu: str = "") -> str:
    """
    İstanbul toplu taşıma güzergâh bilgileri (OpenStreetMap/Overpass).
    hat_kodu boş bırakılırsa genel özet döner.
    Örn: hat_kodu='M2', hat_kodu='T1'
    """
    return get_iett_bus_lines(hat_kodu)


if __name__ == "__main__":
    mcp.run(transport="stdio")