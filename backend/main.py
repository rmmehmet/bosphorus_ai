from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import BosphorusAgent

app = FastAPI(title="Bosphorus AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = BosphorusAgent()


class QueryRequest(BaseModel):
    message: str


class QueryResponse(BaseModel):
    answer: str
    sources_used: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "model": agent.model_name}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")
    result = agent.run(req.message)
    return result