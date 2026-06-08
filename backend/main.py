from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import BosphorusAgent

app = FastAPI(title="Bosphorus AI", version="2.0.0")

# Geliştirme sırasında tüm originlere izin ver; prod'da sıkılaştır
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent başlatma hatası sunucuyu çökertmesin
try:
    agent = BosphorusAgent()
    _agent_ready = True
except Exception as e:
    print(f"⚠️  BosphorusAgent başlatılamadı: {e}")
    _agent_ready = False


class QueryRequest(BaseModel):
    message: str


class QueryResponse(BaseModel):
    answer: str
    sources_used: list[str]


@app.get("/health")
def health():
    return {
        "status": "ok" if _agent_ready else "degraded",
        "model": agent.model_name if _agent_ready else "unavailable",
    }


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if not _agent_ready:
        raise HTTPException(
            status_code=503,
            detail="Agent başlatılamadı. Sunucu loglarını kontrol edin.",
        )
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")
    result = agent.run(req.message)
    return result