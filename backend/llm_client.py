import os
import requests

LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-8b-q4")
REQUEST_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))  # Timeout artırıldı


class LlamaClient:
    def __init__(self):
        self.base_url = LLAMA_SERVER_URL
        self.model_name = MODEL_NAME

    def complete(self, prompt: str, max_tokens: int = 400, temperature: float = 0.4) -> str:
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,  
            "temperature": temperature,
            "repeat_penalty": 1.3,
            "repeat_last_n": 64,
            "stop": [
                "</s>",
                "<|eot_id|>",
                "<|end_of_text|>",
                "\nSoru:",
                "\nKullanıcı:",
                "\nVERİLER:",
                "###",
            ],
            "stream": False,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            content = resp.json().get("content", "").strip()
            # Cevap gerçekten boşsa açıklayıcı mesaj döndürlür
            if not content:
                return "Yanıt üretilemedi, lütfen tekrar deneyin."
            return content
        except requests.exceptions.Timeout:
            return (
                "⚠️ Model zaman aşımına uğradı. "
                "llama-server'ı --n-gpu-layers 999 parametresiyle yeniden başlatın."
            )
        except requests.exceptions.ConnectionError:
            return "⚠️ LLM sunucusuna bağlanılamadı. Sunucunun çalıştığından emin olun."
        except Exception as e:
            return f"⚠️ LLM hatası: {str(e)}"