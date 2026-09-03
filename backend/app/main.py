import os
import ast
import math
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
WORKSPACE = BASE / "workspace"
WORKSPACE.mkdir(exist_ok=True)

app = FastAPI(
    title="NOVA AI Agent",
    version="1.0.0"
)

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = []


class ChatRequest(BaseModel):
    message: str


class PlanRequest(BaseModel):
    goal: str


def safe_calculate(expression: str) -> str:
    allowed = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "pi": math.pi,
        "e": math.e,
    }

    node = ast.parse(expression, mode="eval")

    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id not in allowed:
            raise ValueError("Unsupported name")

        if isinstance(n, ast.Call) and not isinstance(n.func, ast.Name):
            raise ValueError("Unsupported call")

        if isinstance(
            n,
            (
                ast.Attribute,
                ast.Lambda,
                ast.Dict,
                ast.ListComp,
                ast.SetComp,
                ast.GeneratorExp,
                ast.Await,
                ast.Yield,
            ),
        ):
            raise ValueError("Unsafe expression")

    return str(
        eval(
            compile(node, "<calc>", "eval"),
            {"__builtins__": {}},
            allowed,
        )
    )


async def llm(messages):
    key = os.getenv("LLM_API_KEY", "").strip()
    base = os.getenv("LLM_BASE_URL", "").rstrip("/")
    model = os.getenv("LLM_MODEL", "").strip()

    if not (key and base and model):
        return None

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.2,
            },
        )

        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]


SYSTEM = """
You are NOVA, an advanced autonomous AI agent.

Your responsibilities:
- Understand the user's goal.
- Break complex tasks into practical steps.
- Give accurate and useful answers.
- Never claim an external action was completed unless it actually was.
- Protect API keys, passwords and private information.
- Ask for approval before irreversible actions.

Available local tools:
- Calculator
- Workspace
- Conversation memory
"""


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "mode": "llm" if os.getenv("LLM_API_KEY") else "demo",
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    message = req.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message is empty"
        )

    if message.lower().startswith("/calc "):
        try:
            answer = safe_calculate(
                message[6:].strip()
            )
        except Exception as error:
            answer = f"Calculator error: {error}"

        memory.extend(
            [
                {
                    "role": "user",
                    "content": message
                },
                {
                    "role": "assistant",
                    "content": answer
                },
            ]
        )

        return {
            "answer": answer,
            "mode": "tool"
        }

    messages = (
        [{"role": "system", "content": SYSTEM}]
        + memory[-12:]
        + [{"role": "user", "content": message}]
    )

    answer = await llm(messages)

    if answer is None:
        answer = (
            "NOVA is running in DEMO mode. "
            "Configure LLM_API_KEY and LLM_MODEL "
            "in the .env file to activate the real AI model."
        )

    memory.extend(
        [
            {
                "role": "user",
                "content": message
            },
            {
                "role": "assistant",
                "content": answer
            },
        ]
    )

    return {
        "answer": answer,
        "mode": (
            "llm"
            if os.getenv("LLM_API_KEY")
            else "demo"
        ),
    }


@app.post("/api/plan")
async def plan(req: PlanRequest):
    goal = req.goal.strip()

    if not goal:
        raise HTTPException(
            status_code=400,
            detail="Goal is empty"
        )

    messages = [
        {
            "role": "system",
            "content": (
                SYSTEM
                + "\nReturn a practical numbered execution plan."
            ),
        },
        {
            "role": "user",
            "content": f"Goal: {goal}",
        },
    ]

    answer = await llm(messages)

    if answer is None:
        answer = (
            "1. Understand the goal and constraints.\n"
            "2. Gather required information.\n"
            "3. Execute safe actions.\n"
            "4. Verify the result.\n"
            "5. Report completed and remaining work."
        )

    return {
        "plan": answer
    }


@app.get("/api/workspace")
def workspace():
    items = []

    for path in WORKSPACE.iterdir():
        if path.name == ".gitkeep":
            continue

        items.append(
            {
                "name": path.name,
                "type": (
                    "directory"
                    if path.is_dir()
                    else "file"
                ),
            }
        )

    return {
        "items": items
    }
