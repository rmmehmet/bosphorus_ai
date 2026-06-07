"""
LlamaClient: llama.cpp sunucusuna HTTP üzerinden bağlanır.
Başlatma: llama-server --model models/llama-3.1-8b-q4.gguf --port 8080 --n-gpu-layers 35
"""
import os
import requests

LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://localhost:8080")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-8b-q4")


class LlamaClient:
    def __init__(self):
        self.base_url = LLAMA_SERVER_URL
        self.model_name = MODEL_NAME

    def complete(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "stop": ["</s>", "<|eot_id|>", "Kullanıcı sorusu:"],
            "stream": False,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json().get("content", "").strip()
        except requests.exceptions.ConnectionError:
            return (
                "⚠️ LLM sunucusuna bağlanılamadı. "
                "llama-server'ın çalıştığından emin olun: "
                "llama-server --model models/llama-3.1-8b-q4.gguf --port 8080 --n-gpu-layers 35"
            )
        except Exception as e:
            return f"⚠️ LLM hatası: {str(e)}"