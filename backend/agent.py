from tools import (
    get_holidays, get_vehicles, get_weather_from_excel,
    get_current_weather_api, get_current_date_info,
    get_istanbul_historic_places, get_iett_bus_lines,
)
from llm_client import LlamaClient
from router import SemanticRouter

# ---------------------------------------------------------------------------
# Prompt — LLM'nin cevabı neden yarıda kestiğinin ana nedeni buydu:
#   1) CEVAP: etiketinden sonra model kendi çıktısını "meta-cevap" olarak görüp duruyordu
#   2) max_tokens 300 çok kısıydı
#   3) stop token listesi çok agresifti ("1.", "adım" gibi)
# Şimdi: daha yönlendirici, cevabın bitmesini garantileyen bir prompt.
# ---------------------------------------------------------------------------

ANSWER_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Sen Bosphorus AI'sın; İstanbul hakkında kısa, doğru, Türkçe yanıtlar veren bir asistansın.
MUTLAK KURALLAR:
1. Yalnızca aşağıdaki VERİLER bölümündeki bilgileri kullan; asla uydurma.
2. Cevabın tam ve eksiksiz olsun; son cümlen nokta ile bitsin.
3. Maksimum 4 cümle yaz.
4. URL, link, madde listesi (tire/numara), başlık kullanma; düz paragraf yaz.
5. "Ziyaret edin", "ziyaret etmelisiniz", "aşağıda", "adımlar" gibi kalıplar kullanma.
6. Ulaşım sorusunda yalnızca ulaşım verisini kullan; veri yoksa "güncel rota bilgisi mevcut değil" de.
<|eot_id|><|start_header_id|>user<|end_header_id|>
VERİLER:
{data}

SORU: {question}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""


def log(msg: str):
    print(f"  ⟶  {msg}", flush=True)


class BosphorusAgent:
    def __init__(self):
        self.llm = LlamaClient()
        self.model_name = self.llm.model_name
        self.router = SemanticRouter(threshold=0.35, top_k=3)

    def _execute(self, name: str, args: dict) -> str:
        dispatch = {
            "get_holidays": lambda: get_holidays(),
            "get_vehicles": lambda: get_vehicles(),
            "get_weather_from_excel": lambda: get_weather_from_excel(),
            "get_current_weather_api": lambda: get_current_weather_api(),
            "get_current_date_info": lambda: get_current_date_info(),
            "get_istanbul_historic_places": lambda: get_istanbul_historic_places(
                args.get("query", "İstanbul turistik yerler")
            ),
            "get_iett_bus_lines": lambda: get_iett_bus_lines(
                args.get("hat_kodu", "")
            ),
        }
        fn = dispatch.get(name)
        return fn() if fn else f"⚠️ Bilinmeyen tool: {name}"

    def run(self, question: str) -> dict:
        print(f"\n{'=' * 55}", flush=True)
        print(f"📨 Soru: {question}", flush=True)
        print(f"{'=' * 55}", flush=True)

        # 1. Semantic routing
        log("Semantic routing hesaplanıyor...")
        calls = self.router.route(question)

        if not calls:
            log("Eşleşen tool bulunamadı; varsayılan olarak tarihi yerler aranıyor.")
            calls = [
                {
                    "name": "get_istanbul_historic_places",
                    "arguments": {"query": question},
                    "score": 0.0,
                }
            ]

        for c in calls:
            log(f"Tool seçildi: {c['name']} (skor: {c.get('score', '?')}, args: {c['arguments']})")

        # 2. Tool etiketleri
        labels = {
            "get_holidays": "📅 Tatil verisi (Excel) okunuyor...",
            "get_vehicles": "🚗 Araç verisi (Excel) okunuyor...",
            "get_weather_from_excel": "📊 İklim verisi (Excel) okunuyor...",
            "get_current_weather_api": "🌤  Open-Meteo API'ye bağlanılıyor...",
            "get_current_date_info": "🗓  Tarih bilgisi alınıyor...",
            "get_istanbul_historic_places": "🏛  Wikipedia API'ye bağlanılıyor...",
            "get_iett_bus_lines": "🚌  Toplu taşıma verisi alınıyor (OSM)...",
        }

        results = {}
        for call in calls:
            name = call["name"]
            log(labels.get(name, f"⚙️  {name}..."))
            try:
                results[name] = self._execute(name, call.get("arguments", {}))
                log(f"✓ {name} tamamlandı")

                # Excel hava başarıyla okunduysa API ile de destekle
                if name == "get_weather_from_excel":
                    log("🌤  Excel verisi alındı, anlık API tahminiyle destekleniyor...")
                    try:
                        results["get_current_weather_api"] = get_current_weather_api()
                        log("✓ Open-Meteo API tamamlandı")
                    except Exception as api_err:
                        log(f"⚠️  Open-Meteo API ek çağrısı başarısız: {api_err}")

            except FileNotFoundError as e:
                log(f"⚠️  {name}: Dosya bulunamadı — {e}")
                # Excel yoksa direkt API'ye geç
                if name == "get_weather_from_excel":
                    log("🌤  Excel yok → Open-Meteo API'ye geçiliyor...")
                    try:
                        results["get_current_weather_api"] = get_current_weather_api()
                        log("✓ Open-Meteo API fallback tamamlandı")
                    except Exception as e2:
                        log(f"✗ API fallback hata: {e2}")

            except Exception as e:
                log(f"✗ {name} hata: {e}")
                if name == "get_weather_from_excel":
                    log("⚠️  Excel okunamadı → Open-Meteo API'ye geçiliyor...")
                    try:
                        results["get_current_weather_api"] = get_current_weather_api()
                        log("✓ Open-Meteo API fallback tamamlandı")
                    except Exception as e2:
                        log(f"✗ API fallback hata: {e2}")
                else:
                    log(f"⚠️  {name} atlanıyor.")

        if not results:
            return {
                "answer": "Şu anda veri kaynaklarına ulaşamıyorum, lütfen tekrar deneyin.",
                "sources_used": [],
            }

        log(f"Sonuç derleniyor ({len(results)} kaynaktan veri alındı)...")
        log("🤖 LLM cevap üretiyor...")

        # Her kaynaktan max 600 karakter al (önceden 500'dü; daha fazla bağlam = daha iyi cevap)
        data_summary = "\n\n".join(
            [f"[{k}]:\n{v[:600]}" for k, v in results.items()]
        )

        raw_answer = self.llm.complete(
            ANSWER_PROMPT.format(data=data_summary, question=question),
            max_tokens=400,
            temperature=0.35,
        )

        answer = _clean_answer(raw_answer)
        log("✓ Cevap hazır.\n")
        return {
            "answer": answer.strip(),
            "sources_used": list(results.keys()),
        }


def _clean_answer(text: str) -> str:
    """
    Hallüsinasyon ve meta-çıktı kalıplarını temizler.
    Artık cümle ortasında kesme yok — sadece belirli meta kalıpları içeren satırlar kaldırılır.
    """
    import re

    # URL'leri temizle
    text = re.sub(r"https?://\S+", "", text)

    # Yalnızca bu satırları at — cümleleri kırpma
    meta_triggers = [
        "bosphorus ai",
        "sen misin",
        "ben de sen",
        "ziyaret edin",
        "ziyaret etmelisiniz",
        "siteyi ziyaret",
        "yanıtınızdan",
        "aşağıdaki şekilde",
        "<|",       # kalan token kalıpları
        "|>",
    ]

    lines = [l for l in text.split("\n") if l.strip()]
    cleaned = [
        l for l in lines
        if not any(t in l.lower() for t in meta_triggers)
    ]

    result = " ".join(cleaned).strip()

    # Birden fazla boşluğu tek boşluğa indir
    result = re.sub(r" {2,}", " ", result)

    return result