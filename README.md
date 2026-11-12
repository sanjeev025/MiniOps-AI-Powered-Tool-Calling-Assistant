# MiniOps – Tool-Calling AI Assistant
### Hermes Agent + UTCP + Langfuse Proof of Concept (POC)

MiniOps is an experimental proof of concept demonstrating the integration of three core agentic technologies:

1. **Hermes Agent (Nous Research)**: Agent reasoning, natural-language interaction, and tool orchestration.
2. **UTCP (Universal Tool Calling Protocol)**: Standardized, wrapperless tool discovery and HTTP execution directly against native API endpoints.
3. **Langfuse**: End-to-end LLM observability, trace visualization, and tool execution observation via OpenTelemetry-compatible tracing.

---

## 📁 Repository Structure

```text
.
├── demo_api/                 # FastAPI service serving operational endpoints + UTCP manual
│   ├── __init__.py
│   ├── main.py               # FastAPI application factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── status.py         # GET /api/status
│   │   └── events.py         # GET /api/events
│   └── utcp_manual.py        # GET /utcp (UTCP manual definition)
│
├── hermes_plugin/            # Custom Hermes Agent plugin source
│   ├── plugin.yaml           # Plugin manifest
│   ├── __init__.py           # register(ctx): registers every tool found in the UTCP manual
│   ├── discovery.py          # Fetches /utcp and converts tools into Hermes schemas
│   ├── tools.py              # Generic UTCP handler factory & @observe instrumentation
│   └── schemas.py            # Fallback schemas, used only if /utcp is unreachable at load time
│
├── config/
│   ├── __init__.py
│   ├── settings.py           # Pydantic Settings: single source of truth for provider mapping
│   └── export_env.py         # `python -m config.export_env` → shell exports for run_agent.sh
│
├── scripts/
│   ├── install_plugin.sh     # Script to install plugin into ~/.hermes/plugins/
│   └── run_agent.sh          # Agent runner reading provider & model from .env
│
├── tests/
│   ├── conftest.py           # Shared live-server fixture (free port)
│   ├── test_api.py           # FastAPI endpoints unit tests
│   ├── test_utcp.py          # UTCP discovery and tool invocation tests
│   ├── test_integration.py   # Plugin registration and handler bridge tests
│   └── test_config.py        # Configurable provider & model settings tests
│
├── .env.example              # Environment variables template
├── requirements.txt          # Pinned runtime dependencies
├── requirements-dev.txt      # + pytest tooling
├── PROJECT_PLAN.md           # Detailed technical architecture and roadmap
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup

Prerequisites:
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or standard `venv`
- An API key for your chosen provider (Groq, OpenAI, xAI, Anthropic, or OpenRouter)
- A Langfuse account (Cloud or Self-Hosted)

Create and activate a virtual environment:
```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r requirements-dev.txt   # or requirements.txt for runtime only
```

Copy the environment template and set your API keys:
```bash
cp .env.example .env
```

---

### 2. Provider & Model Configuration in `.env`

You can change the provider and model at any time by editing `.env`:

#### Option A: Groq (Recommended for ultra-fast LPU inference)
```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=gsk_...
```

#### Option B: OpenAI (Default)
```env
LLM_PROVIDER=openai-api
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

#### Option C: xAI (Grok)
```env
LLM_PROVIDER=xai
LLM_MODEL=grok-2
XAI_API_KEY=xai-...
```

#### Option D: Anthropic
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

#### Option E: OpenRouter
```env
LLM_PROVIDER=openrouter
LLM_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_API_KEY=sk-or-...
```

---

### 3. Running the Demo API Service

Start the FastAPI service:
```bash
source .venv/bin/activate
uvicorn demo_api.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify endpoints in another terminal:
```bash
# Check service health
curl http://127.0.0.1:8000/api/status

# Check recent events
curl http://127.0.0.1:8000/api/events

# Inspect the UTCP manual
curl http://127.0.0.1:8000/utcp
```

---

### 4. Running the MiniOps Agent

Launch the agent with your configured `.env` settings:
```bash
./scripts/run_agent.sh
```

`run_agent.sh` automatically:
1. Resolves provider, model and credentials through `config/settings.py` (reads `.env`; shell exports override it).
2. Forwards `LLM_PROVIDER` and `LLM_MODEL` to Hermes. Groq and custom endpoints go through Hermes' OpenAI-compatible `custom` provider. `LLM_MODEL` is always used exactly as configured.
3. Passes API keys only as environment variables, never as command-line arguments (so they don't show up in `ps`).
4. Ensures the `hermes-utcp` tool plugin is installed and active.
5. Passes through any additional flags you specify (e.g. `./scripts/run_agent.sh -q "Check my demo service status"`).

> **Tool discovery:** at load time the plugin fetches the UTCP manual from `UTCP_MANUAL_URL` and registers every tool it lists. Adding an endpoint to `demo_api/utcp_manual.py` exposes it to the agent with no plugin changes. Start the demo API before the agent; if it's down, the plugin falls back to the built-in schemas and logs a warning. After editing the plugin source, re-run `./scripts/install_plugin.sh`.

---

### 5. Running the Test Suite

Run all unit and integration tests:
```bash
pytest tests/ -v
```

All 22 tests verify:
- FastAPI endpoints schema conformance
- Live UTCP manual parsing and tool discovery
- Direct HTTP endpoint execution via `UtcpClient`
- Plugin registration from the live manual, plus the fallback when it's unreachable
- Handlers across fresh event loops, and recovery after the service was down
- Secrets never appear in Hermes CLI args; `export_env` output round-trips through bash
- Native Groq, OpenAI, xAI, and Anthropic provider switching via `.env`
- Graceful exception handling on unreachable services

---

## 🔍 How It Works

1. **User asks Hermes:**
   > *"Check my demo service status and tell me whether there are any recent changes."*
2. **Hermes Agent** evaluates the user intent against its registered tool schemas using the model specified in `.env` (e.g. `openai/gpt-oss-120b` on Groq, `gpt-4o`, `grok-2`).
3. The **`hermes-utcp` plugin** (whose tools were discovered from `/utcp`) invokes the native **UTCP client** (`utcp.utcp_client.UtcpClient`).
4. The UTCP client executes native HTTP `GET` requests against `/api/status` and `/api/events` (tool inputs such as `limit` become query parameters) without middleware proxies.
5. Structured responses are returned to Hermes, which synthesizes a natural-language answer.
6. The entire conversation turn, LLM generations, and discrete UTCP tool calls are recorded and visible in the **Langfuse dashboard**.
