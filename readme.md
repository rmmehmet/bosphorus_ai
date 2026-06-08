# 🌊 Bosphorus AI

Kullanıcıların doğal dil ile soru sorabildiği, Excel veri kaynaklarını ve harici API'leri analiz ederek Türkçe cevap üreten yapay zeka destekli bir agent sistemi.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)
![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-FF6B35?style=flat-square&logo=meta&logoColor=white)
![sentence-transformers](https://img.shields.io/badge/sentence--transformers-multilingual-orange?style=flat-square&logo=huggingface&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Excel-150458?style=flat-square&logo=pandas&logoColor=white)
![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-Overpass_API-7EBC6F?style=flat-square&logo=openstreetmap&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [Mimari](#mimari)
- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Proje Yapısı](#proje-yapısı)
- [Veri Kaynakları](#veri-kaynakları)
- [Tool Listesi](#tool-listesi)
- [Konfigürasyon](#konfigürasyon)

---

## Genel Bakış

Bosphorus AI, İstanbul'da tatil yapmak isteyen bir kullanıcının sorabileceği çeşitli soruları yanıtlamak üzere tasarlanmıştır. Sistem; hava durumu, resmi tatiller, araç yakıt tüketimi, tarihi yerler ve toplu taşıma gibi konularda hem Excel tabanlı tarihsel verilerden hem de canlı API'lerden bilgi toplayarak LLM ile doğal dilde cevap üretir.

**Temel yaklaşım:** Excel dosyaları birincil veri kaynağı olarak önceliklidir; eksik veya güncel olmayan veriler harici API'lerle otomatik olarak tamamlanır.

---

## Mimari

```
Kullanıcı Sorusu
      │
      ▼
SemanticRouter  ──►  Cosine Similarity (sentence-transformers)
      │               Tool açıklamalarıyla karşılaştırma
      │               Combo kuralları ile çoklu tool seçimi
      ▼
Tool Executor
      │
      ├── Excel Okuma (pandas)       → holidays.xlsx, vehicles.xlsx, weather.xlsx
      ├── Open-Meteo API             → Anlık + 7 günlük hava tahmini
      ├── Wikipedia API (TR)         → Tarihi yerler bilgisi
      ├── Overpass API (OSM)         → İstanbul toplu taşıma güzergâhları
      └── Fallback katmanları        → Excel yoksa API, API yoksa statik veri
      │
      ▼
LlamaClient  ──►  llama-server (llama.cpp)
      │            Llama-3.1-8B-Q4 (veya tercih edilen model)
      ▼
Temizlenmiş Türkçe Cevap
      │
      ▼
FastAPI  ──►  React Frontend
```

**Veri akışı özeti:**

1. Soru `SemanticRouter`'a gelir; `paraphrase-multilingual-MiniLM-L12-v2` modeli ile tool açıklamalarına karşı cosine similarity hesaplanır.
2. Skoru eşiği (0.35) geçen tool'lar ve combo kurallarına göre ek tool'lar seçilir.
3. Seçilen tool'lar çalışır; Excel başarısızsa API fallback devreye girer.
4. Tüm veri kaynakları birleştirilerek LLM prompt'una eklenir.
5. LLM (Llama-3.1) kısa, doğal Türkçe bir cevap üretir.
6. Cevap temizlenerek kullanıcıya döndürülür.

---

## Özellikler

- **Semantic Routing** — LLM çağrısı yapmadan, tamamen lokal cosine similarity ile doğru tool seçimi
- **Çoklu kaynak desteği** — Aynı soruya birden fazla tool paralel çalışabilir
- **Akıllı fallback** — Excel dosyası yoksa API'ye, API erişilemezse statik veriye otomatik geçiş
- **Lokal LLM** — llama.cpp üzerinde GGUF modeli, internet gerekmez
- **MCP Server** — Claude Desktop entegrasyonu için `fastmcp` tabanlı server
- **FastAPI backend** — REST API ile frontend veya harici sistemlerle entegrasyon
- **React frontend** — Arayüz (frontend/ klasöründe)

---

## Kurulum

### Gereksinimler

- Python 3.10+
- Node.js (sadece frontend için)
- [llama.cpp](https://github.com/ggerganov/llama.cpp) (lokal LLM için)

### 1. Repoyu klonla

```bash
git clone https://github.com/kullanici-adi/bosphorus-ai.git
cd bosphorus-ai
```

### 2. Python ortamı

```bash
python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. LLM Sunucusunu başlat

llama.cpp ile bir GGUF modeli indir ve sunucuyu başlat:

```bash
# Model indirme örneği (Meta-Llama-3.1-8B-Instruct-Q4_K_M)
# https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF

./llama-server \
  --model models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  --port 8080 \
  --n-gpu-layers 999 \
  --ctx-size 4096
```

> GPU yoksa `--n-gpu-layers 0` kullan; cevap süresi uzar.

### 4. Ortam değişkenleri

`backend/.env` dosyası oluştur:

```env
LLAMA_SERVER_URL=http://127.0.0.1:8080
MODEL_NAME=llama-3.1-8b-q4
LLM_TIMEOUT=300
```

### 5. Backend'i başlat

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Frontend'i başlat (opsiyonel)

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173 adresinde çalışır
```

---

## Kullanım

### API üzerinden

```bash
# Sağlık kontrolü
curl http://localhost:8000/health

# Soru sor
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"message": "Bugün İstanbul hava durumu nasıl?"}'
```

**Örnek yanıt:**

```json
{
  "answer": "İstanbul'da bugün hava parçalı bulutlu ve 22°C civarında. Hafif rüzgar bekleniyor, yağış öngörülmüyor.",
  "sources_used": ["get_current_weather_api", "get_weather_from_excel"]
}
```

### MCP Server (Claude Desktop)

```bash
cd backend
python mcp_server.py
```

Claude Desktop `claude_desktop_config.json` ayarı:

```json
{
  "mcpServers": {
    "bosphorus-ai": {
      "command": "python",
      "args": ["/tam/yol/backend/mcp_server.py"]
    }
  }
}
```

### Örnek sorular

| Soru | Kullanılan Tool'lar |
|------|---------------------|
| "Bugün hava nasıl?" | `get_current_weather_api`, `get_weather_from_excel` |
| "Bu hafta tatil var mı?" | `get_holidays`, `get_current_date_info` |
| "En az yakan araç hangisi?" | `get_vehicles` |
| "Ayasofya hakkında bilgi ver" | `get_istanbul_historic_places` |
| "Kadıköy'den Taksim'e nasıl gidebilirim?" | `get_iett_bus_lines` |
| "Güneşliyse nereye gideyim?" | `get_current_weather_api`, `get_istanbul_historic_places` |

---

## Proje Yapısı

```
BOSPHORUS_AI/
├── backend/
│   ├── agent.py          # Ana orkestrasyon — tool yönetimi ve LLM çağrısı
│   ├── router.py         # SemanticRouter — cosine similarity ile tool seçimi
│   ├── tools.py          # Tüm tool implementasyonları (Excel + API)
│   ├── llm_client.py     # llama.cpp HTTP client
│   ├── main.py           # FastAPI uygulama ve endpoint'ler
│   ├── mcp_server.py     # MCP server (Claude Desktop entegrasyonu)
│   ├── requirements.txt  # Python bağımlılıkları
│   └── .env              # Ortam değişkenleri (git'e eklenmez)
├── data/
│   ├── holidays.xlsx     # Türkiye resmi tatilleri
│   ├── vehicles.xlsx     # Araç yakıt tüketim verileri
│   └── weather.xlsx      # İstanbul tarihsel iklim ortalamaları
├── frontend/             # React arayüzü
└── README.md
```

---

## Veri Kaynakları

| Kaynak | Tür | İçerik | Fallback |
|--------|-----|--------|----------|
| `holidays.xlsx` | Excel | Türkiye resmi tatilleri | — |
| `vehicles.xlsx` | Excel | Araç yakıt tüketim verileri | — |
| `weather.xlsx` | Excel | İstanbul 1950–2025 iklim ortalamaları | Open-Meteo API |
| Open-Meteo | API | Anlık + 7 günlük hava tahmini | Ücretsiz, kayıt gerektirmez |
| Wikipedia (TR) | API | Tarihi yerler özet bilgileri | — |
| Overpass (OSM) | API | İstanbul toplu taşıma güzergâhları | Statik hat özeti |

> **Not:** `weather.xlsx` eksikse veya okunamazsa sistem otomatik olarak Open-Meteo API'ye geçer. Veri bütünlüğü kullanıcıdan bağımsız olarak korunur.

---

## Tool Listesi

| Tool | Açıklama |
|------|----------|
| `get_holidays` | Türkiye resmi tatillerini Excel'den okur |
| `get_vehicles` | Araç yakıt tüketim verilerini Excel'den okur |
| `get_weather_from_excel` | Tarihsel iklim ortalamalarını Excel'den okur |
| `get_current_weather_api` | Open-Meteo API ile anlık + 7 günlük tahmin |
| `get_current_date_info` | Bugünün tarihi ve tatil durumu |
| `get_istanbul_historic_places` | Wikipedia TR API ile tarihi yer bilgisi |
| `get_iett_bus_lines` | Overpass/OSM ile İstanbul toplu taşıma güzergâhları |

---

## Konfigürasyon

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `LLAMA_SERVER_URL` | `http://127.0.0.1:8080` | llama-server adresi |
| `MODEL_NAME` | `llama-3.1-8b-q4` | Model adı (sadece log için) |
| `LLM_TIMEOUT` | `300` | LLM istek zaman aşımı (saniye) |

**SemanticRouter parametreleri** (`router.py`):

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|----------|
| `threshold` | `0.35` | Minimum cosine similarity skoru |
| `top_k` | `3` | Maksimum seçilecek tool sayısı |

---

## Bağımlılıklar

```
fastapi
uvicorn
pydantic
requests
pandas
openpyxl
sentence-transformers
torch
fastmcp
```

Tüm liste için: `backend/requirements.txt`