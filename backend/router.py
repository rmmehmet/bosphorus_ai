"""
SemanticRouter: Kullanıcı sorusunu tool açıklamalarıyla karşılaştırıp
cosine similarity ile en uygun tool'ları seçer.
LLM çağrısı yapmaz, tamamen local çalışır.
"""
from sentence_transformers import SentenceTransformer, util

# Tool açıklamaları — zengin tutulması routing kalitesini doğrudan etkiler
TOOL_DESCRIPTIONS = {
    "get_holidays": (
        "resmi tatil bayram milli tatil yılbaşı kurban ramazan cumhuriyet "
        "bugün tatil mi yarın tatil mi izin günleri kaç gün tatil ne zaman tatil"
    ),
    "get_vehicles": (
        "araç araba yakıt tüketim litre ekonomik taşıt benzin dizel hibrit elektrik "
        "en az yakan hangi araç daha iyi yakıt karşılaştır kilometre başına"
    ),
    "get_weather_from_excel": (
        "İstanbul iklim ortalama sıcaklık yağış nem tarihsel istatistik "
        "aylık ortalama derece kaç derece olur genel hava mevsim"
    ),
    "get_current_weather_api": (
        "bugün hava durumu bu hafta hava tahmini anlık sıcaklık şu an hava "
        "yağmur güneşli mi kar yağacak mı rüzgar şemsiye gerekir mi dışarısı nasıl"
    ),
    "get_current_date_info": (
        "bugün tarih hangi gün kaçıncı gün hafta sonu mu bugün tatil mi "
        "günün tarihi saat kaç ay yıl"
    ),
    "get_istanbul_historic_places": (
        "İstanbul tarihi yer turistik gezi müze cami saray kule kilise köprü "
        "görülecek yerler nereye gideyim öneri kalabalık olmayan sessiz "
        "seyahat tatil gezmek ziyaret etmek ayasofya topkapı galata sultanahmet"
    ),
    "get_iett_bus_lines": (
        "otobüs hat toplu taşıma ulaşım durak nereden biner nasıl gidilir "
        "metro tramvay vapur marmaray Kadıköy Beşiktaş Taksim Eminönü Üsküdar "
        "toplu taşıt rota güzergah nereden gidebilirim İETT"
    ),
}

# Anahtar kelime bazlı ek tool kombinasyonları
COMBO_RULES = [
    {
        "triggers": ["güneşli", "hava", "gezi", "gezilecek", "gideyim", "öneri", "kalabalık"],
        "add": ["get_current_weather_api", "get_istanbul_historic_places"],
    },
    {
        "triggers": ["toplu taşıma", "nasıl giderim", "otobüs", "ulaşım", "nereden binerim", "metro", "tramvay", "vapur"],
        "add": ["get_iett_bus_lines"],
    },
    {
        "triggers": ["tatil", "bayram", "resmi tatil"],
        "add": ["get_holidays", "get_current_date_info"],
    },
    {
        "triggers": ["bugün", "yarın", "bu hafta"],
        "add": ["get_current_date_info"],
    },
]

# Parametre çıkarımı — LLM yerine kural tabanlı
PARAM_EXTRACTORS = {
    "get_istanbul_historic_places": lambda q: _extract_place_query(q),
    "get_iett_bus_lines": lambda q: _extract_hat_kodu(q),
}


def _extract_place_query(question: str) -> dict:
    place_keywords = [
        "ayasofya", "topkapı", "galata", "sultanahmet", "kapalıçarşı",
        "boğaz", "üsküdar", "beşiktaş", "kadıköy", "eminönü", "eyüp",
        "balat", "fener", "büyükada", "çamlıca", "pierre loti",
        "dolmabahçe", "rumeli hisarı", "kariye", "chora",
    ]
    q_lower = question.lower()
    for place in place_keywords:
        if place in q_lower:
            return {"query": place}
    return {"query": "İstanbul turistik gezilecek yerler kalabalık olmayan"}


def _extract_hat_kodu(question: str) -> dict:
    import re
    # Hat kodu: 34, 500T, M1, T1 gibi
    match = re.search(r"\b([A-Za-z]?\d{1,3}[A-Za-z]?)\b", question)
    if match:
        return {"hat_kodu": match.group(1)}
    return {"hat_kodu": ""}


class SemanticRouter:
    def __init__(self, threshold: float = 0.35, top_k: int = 3):
        print("  ⟶  SemanticRouter yükleniyor (paraphrase-multilingual-MiniLM-L12-v2)...")
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.threshold = threshold
        self.top_k = top_k

        self.tool_names = list(TOOL_DESCRIPTIONS.keys())
        self.tool_embeddings = self.model.encode(
            list(TOOL_DESCRIPTIONS.values()),
            convert_to_tensor=True,
            show_progress_bar=False,
        )
        print("  ⟶  SemanticRouter hazır.\n")

    def route(self, question: str) -> list[dict]:
        q_embedding = self.model.encode(
            question, convert_to_tensor=True, show_progress_bar=False
        )
        scores = util.cos_sim(q_embedding, self.tool_embeddings)[0]

        scored = sorted(
            zip(self.tool_names, scores.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )

        selected: dict[str, dict] = {}
        for name, score in scored[: self.top_k]:
            if score >= self.threshold:
                args = {}
                if name in PARAM_EXTRACTORS:
                    args = PARAM_EXTRACTORS[name](question)
                selected[name] = {
                    "name": name,
                    "arguments": args,
                    "score": round(score, 3),
                }

        # Combo kuralları
        q_lower = question.lower()
        for rule in COMBO_RULES:
            if any(trigger in q_lower for trigger in rule["triggers"]):
                for tool_name in rule["add"]:
                    if tool_name not in selected:
                        args = {}
                        if tool_name in PARAM_EXTRACTORS:
                            args = PARAM_EXTRACTORS[tool_name](question)
                        selected[tool_name] = {
                            "name": tool_name,
                            "arguments": args,
                            "score": 0.0,
                        }

        return list(selected.values())