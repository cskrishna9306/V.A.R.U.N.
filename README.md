# V.A.R.U.N.

**Versatile AI for Running Ur Next move**

## Overview

V.A.R.U.N. is a Discord bot that pairs a local LLM (via [Ollama](https://ollama.com/) and Microsoft AutoGen) with tools for chat, weather, and shared expense handling. The main conversational agent (`V_A_R_U_N`) loads its behavior from markdown prompts and structured responses. A separate agent stack (**N.A.M.I.**) helps log group expenses through a **Beri** layer that wraps the Splitwise API, fuzzy-matching participants and recording transactions. Optional assets include a `Dockerfile` for containerized runs and shell templates under `src/gcp/` for deploying on Google Cloud.

## Directory Structure

| Path | Purpose |
|------|---------|
| `src/main.py` | Entry point: starts the Discord bot. |
| `src/discord/` | Bot client, slash-command cogs (`yap`, `expense`), guild configuration, and tool wiring. |
| `src/llm/` | Agent orchestration (`orchestrator.py`), N.A.M.I. wiring, Pydantic verdict/plan models, utilities (e.g. weather, GIFs), and markdown system prompts under `prompts/`. |
| `src/llm/sub_agents/` | Specialized agents (for example the accountant flow used with expenses). |
| `src/beri/` | Splitwise-backed ledger (`Beri`), domain models, Splitwise config, and journaling helpers. |
| `src/gcp/` | Boot scripts and Route 53 template for cloud instance setup. |
| `src/app.py` | Small FastAPI sample (separate from the bot; may require extra setup to run). |
| `requirements.in` / `requirements.txt` | Top-level and compiled Python dependencies. |

## Quickstart

1. **Prerequisites**
   - Python 3.13 (matches the pinned dependency set).
   - [Ollama](https://ollama.com/) running locally. Pull the model configured in `src/llm/config.py` (default `qwen2.5:latest`) so tool-calling and JSON-style outputs match expectations.

2. **Install**
   ```bash
   cd /path/to/V.A.R.U.N.
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Environment**
   Create a `.env` in the project root (see `load_dotenv()` usage in `src/discord/config.py` and `src/beri/config.py`):
   - `DISCORD_BOT_TOKEN` — required for the bot.
   - `GIPHY_API_KEY` — optional; enables GIF search behavior when configured.
   - `SPLITWISE_CONSUMER_KEY`, `SPLITWISE_CONSUMER_SECRET`, `SPLITWISE_API_KEY` — required for Beri / expense logging features.

4. **Run the bot**
   From the repository root:
   ```bash
   python -m src.main
   ```

5. **Docker (optional)**
   ```bash
   docker build -t varun-bot .
   docker run --env-file .env varun-bot
   ```
   Ensure Ollama is reachable from the container if you rely on the default `LLM_BASE_URL` in `src/llm/config.py` (often `http://localhost:11434` on the host).
