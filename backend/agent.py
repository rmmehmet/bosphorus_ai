"""
BosphorusAgent: Kullanıcı sorusunu analiz eder, doğru tool'ları seçer ve
llama.cpp (local LLM) üzerinden doğal dil cevabı üretir.
"""
import json
import re
from tools import (
    get_holidays,
    get_vehicles,
    get_weather_from_excel,
    get_current_weather_api,
    get_current_date_info,
)
from llm_client import LlamaClient

TOOL_REGISTRY = {
    "get_holidays": {
        "fn": get_holidays,
        "description": "Resmi tatilleri listeler. 'tatil', 'bayram', 'resmi tatil', 'bugün tatil mi' gibi sorularda kullan.",
        "keywords": ["tatil", "bayram", "resmi", "kaç gün", "izin", "holiday"],
    },
    "get_vehicles": {
        "fn": get_vehicles,
        "description": "Araç yakıt tüketimi verilerini getirir. 'araç', 'yakıt', 'tüketim', 'ekonomik', 'taşıt' gibi sorularda kullan.",
        "keywords": ["araç", "yakıt", "tüketim", "araba", "ekonomik", "taşıt", "km", "lt", "litre", "vehicle", "car"],
    },
    "get_weather_from_excel": {
        "fn": get_weather_from_excel,
        "description": "İstanbul için historik/ortalama hava durumu verilerini Excel'den getirir.",
        "keywords": ["hava", "sıcaklık", "yağış", "iklim", "ortalama", "weather", "derece"],
    },
    "get_current_weather_api": {
        "fn": get_current_weather_api,
        "description": "Bugünün veya bu haftanın gerçek zamanlı hava durumunu API'den getirir.",
        "keywords": ["bugün", "şu an", "bu hafta", "güncel", "şimdi", "gerçek"],
    },
    "get_current_date_info": {
        "fn": get_current_date_info,
        "description": "Bugünün tarihini ve tatil olup olmadığını döner.",
        "keywords": ["bugün", "tarih", "gün", "kaçıncı"],
    },
}

ROUTER_SYSTEM_PROMPT = """Sen Bosphorus AI'ın akıllı yönlendirme motorusun.
Kullanıcının sorusuna göre hangi tool'ların çağrılması gerektiğine karar ver.

Mevcut tool'lar:
{tools}

Kullanıcı sorusu: "{question}"

Sadece JSON döndür, başka hiçbir şey yazma. Format:
{{"selected_tools": ["tool_adı1", "tool_adı2"]}}

Birden fazla tool seçebilirsin. Sadece verilen tool isimlerini kullan."""

ANSWER_SYSTEM_PROMPT = """Sen Bosphorus AI'sın - İstanbul odaklı akıllı bir veri analiz asistanısın.
Kullanıcılara Türkçe, samimi ve net cevaplar verirsin.
Verilen verileri analiz edip kullanıcının sorusunu doğrudan yanıtla.
Gereksiz teknik detay verme. Kısa ve öz ol."""


class BosphorusAgent:
    def __init__(self):
        self.llm = LlamaClient()
        self.model_name = self.llm.model_name

    def _select_tools(self, question: str) -> list[str]:
        q_lower = question.lower()
        selected = set()

        for tool_name, meta in TOOL_REGISTRY.items():
            for kw in meta["keywords"]:
                if kw in q_lower:
                    selected.add(tool_name)

        # Hava durumu: her zaman hem Excel hem API'yi çek
        if "get_weather_from_excel" in selected or "get_current_weather_api" in selected:
            selected.add("get_weather_from_excel")
            selected.add("get_current_weather_api")

        # "Bugün tatil mi?" için tarih + tatil verisi
        if "get_current_date_info" in selected or "tatil" in q_lower:
            selected.add("get_current_date_info")
            selected.add("get_holidays")

        if not selected:
            selected = self._llm_route(question)

        return list(selected)

    def _llm_route(self, question: str) -> set:
        tool_desc = "\n".join(
            [f"- {name}: {meta['description']}" for name, meta in TOOL_REGISTRY.items()]
        )
        prompt = ROUTER_SYSTEM_PROMPT.format(tools=tool_desc, question=question)
        raw = self.llm.complete(prompt, max_tokens=200, temperature=0.1)
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return set(data.get("selected_tools", []))
        except Exception:
            pass
        return set(TOOL_REGISTRY.keys())

    def _call_tools(self, tool_names: list[str]) -> dict:
        results = {}
        for name in tool_names:
            if name in TOOL_REGISTRY:
                try:
                    results[name] = TOOL_REGISTRY[name]["fn"]()
                except Exception as e:
                    results[name] = f"Hata: {str(e)}"
        return results

    def run(self, question: str) -> dict:
        selected_tools = self._select_tools(question)
        tool_results = self._call_tools(selected_tools)

        data_summary = "\n\n".join(
            [f"[{name}]:\n{result}" for name, result in tool_results.items()]
        )

        full_prompt = f"""{ANSWER_SYSTEM_PROMPT}

Elde edilen veriler:
{data_summary}

Kullanıcı sorusu: {question}

Cevap:"""

        answer = self.llm.complete(full_prompt, max_tokens=600, temperature=0.7)

        return {
            "answer": answer.strip(),
            "sources_used": selected_tools,
        }