import json
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from passlib.context import CryptContext
from starlette.datastructures import Headers
from starlette.concurrency import run_in_threadpool
from .x402_wallet import X402Wallet
from .agent import AgenticAI

load_dotenv()

cors_allow_origins = [
  origin.strip()
  for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
  if origin.strip()
] or [
  "http://localhost:3001",
  "http://127.0.0.1:3001",
  "https://localhost:3001",
  "https://127.0.0.1:3001",
]

app = FastAPI(title="AI Engine Service")
app.add_middleware(
  CORSMiddleware,
  allow_origins=cors_allow_origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Environment variables and clients
openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
qwen_model = os.getenv("QWEN_MODEL", "qwen-flash")
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
db_connection_string = os.getenv("SUPABASE_DB_URL", "")

#openai_client = OpenAI()
qwen_client = OpenAI(
  api_key=dashscope_api_key,
  base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# x402 wallet and agentic AI setup
x402_wallet = X402Wallet()
x402_wallet.initialize()

agentic_ai = AgenticAI(
  client=qwen_client,
  model=qwen_model,
  x402_wallet=x402_wallet,
)

class AgentRequest(BaseModel):
  message: str
  thread_id: str | None = None

class RegisterRequest(BaseModel):
  name: str
  email: str
  password: str
  picture: str | None = None

@app.get("/health")
async def health():
  return {"status": "ok"}

@app.post("/agent")
async def agent_endpoint(payload: AgentRequest):
  if not payload.message.strip():
    raise HTTPException(status_code=400, detail="message required")

  if not dashscope_api_key:
    raise HTTPException(status_code=500, detail="Missing DASHSCOPE_API_KEY")

  try:
    reply = await agentic_ai.run(payload.message)
    return {"reply": reply}
  except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc))

