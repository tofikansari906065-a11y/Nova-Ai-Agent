# NOVA AI Agent

A GitHub-ready autonomous AI agent starter with:
- FastAPI backend
- Modern browser chat UI
- Provider support for OpenAI-compatible APIs
- Tool framework (web research hook, calculator, file workspace)
- Conversation memory
- Autonomous planning endpoint
- Safe tool execution boundaries

## Quick start

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
Open another terminal:
```bash
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite (normally http://localhost:5173).

## Model setup

Copy `backend/.env.example` to `backend/.env` and configure an OpenAI-compatible provider:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_key
LLM_MODEL=your_model
```

The app also works in DEMO mode without an API key so the UI can be tested.

## GitHub

Create a repository named `nova-ai-agent`, then:
```bash
git init
git add .
git commit -m "Initial NOVA AI Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nova-ai-agent.git
git push -u origin main
```

## Architecture

frontend -> FastAPI -> agent planner -> tools/memory -> LLM provider

This is a foundation for a larger autonomous agent. Keep API keys server-side and review/permission-gate any powerful tools before deploying publicly.
