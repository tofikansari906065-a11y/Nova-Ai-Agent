import os
import ast
import math
from pathlib import Path
from typing import Any
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
WORKSPACE = BASE / "workspace"
WORKSPACE.mkdir(exist_ok=True)

app = FastAPI(title="NOVA AI Agent", version="1.0.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory: list[dict[str, str]] = []

class ChatRequest(BaseModel):
    message: str

class PlanRequest(BaseModel):
    goal: str

def safe_calculate(expression: str) -> str:
    allowed = {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
               "tan": math.tan, "log": math.log, "pi": math.pi, "e": math.e}
    node = ast.parse(expression, mode="eval")
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id not in allowed:
            raise ValueError("Unsupported name")
        if isinstance(n, ast.Call) and not isinstance(n.func, ast.Name):
            raise ValueError("Unsupported call")
        if isinstance(n, (ast.Attribute, ast.Lambda, ast.Dict, ast.ListComp, ast.SetComp,
                          ast.GeneratorExp, ast.Await, ast.Yield)):
            raise ValueError("Unsafe expression")
    return str(eval(compile(node, "<calc>", "eval"), {"__builtins__": {}}, allowed))

async def llm(messages: list[dict[str, str]]) -> str | None:
    key = os.getenv("LLM_API_KEY", "").strip()
    base = os.getenv("LLM_BASE_URL", "").rstrip("/")
    model = os.getenv("LLM_MODEL", "").strip()
    if not (key and base and model):
        return None
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": 0.2},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

SYSTEM = """You are NOVA, a capable autonomous AI agent.
Be concise but useful. Break complex tasks into steps. Never claim you performed an
external action unless the tool actually did it. Protect secrets and ask for approval
before irreversible actions. Available local tools: calculator and workspace file listing."""

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "llm" if os.getenv("LLM_API_KEY") else "demo"}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        raise HTTPException(400, "Message is empty")

    if msg.lower().startswith("/calc "):
        try:
            answer = safe_calculate(msg[6:].strip())
        except Exception as e:
            answer = f"Calculator error: {e}"
        memory.extend([{"role": "user", "content": msg}, {"role": "assistant", "content": answer}])
        return {"answer": answer, "mode": "tool"}

    context = memory[-12:]
    messages = [{"role": "system", "content": SYSTEM}] + context + [{"role": "user", "content": msg}]
    answer = await llm(messages)
    if answer is None:
        answer = (
            "NOVA is running in DEMO mode. Add LLM_API_KEY and LLM_MODEL in "
            "backend/.env to activate the real model. I can still calculate with "
            "`/calc 25*4` and use the local workspace."
        )
    memory.extend([{"role": "user", "content": msg}, {"role": "assistant", "content": answer}])
    return {"answer": answer, "mode": "llm" if os.getenv("LLM_API_KEY") else "demo"}

@app.post("/api/plan")
async def plan(req: PlanRequest):
    goal = req.goal.strip()
    if not goal:
        raise HTTPException(400, "Goal is empty")
    prompt = [
        {"role": "system", "content": SYSTEM + "\nReturn a practical numbered execution plan. Do not pretend actions were completed."},
        {"role": "user", "content": f"Goal: {goal}"}
    ]
    answer = await llm(prompt)
    if answer is None:
        answer = (
            "1. Clarify the desired outcome and constraints.\n"
            "2. Gather the required information.\n"
            "3. Execute the smallest safe actions.\n"
            "4. Verify the result.\n"
            "5. Report what was completed and what remains."
        )
    return {"plan": answer}

@app.get("/api/workspace")
def workspace():
    items = []
    for p in WORKSPACE.iterdir():
        if p.name == ".gitkeep":
            continue
        items.append({"name": p.name, "type": "directory" if p.is_dir() else "file"})
    return {"items": items}
