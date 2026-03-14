# JARVIS-X: Autonomous AI Operations Center

JARVIS-X is a fully local, zero-trust, ReAct-based AI agent orchestration platform designed to run directly on Windows hardware. It combines a sophisticated LangGraph backend with a premium React/Vite dashboard, capable of autonomous tool usage, multi-modal perception, persistent memory tracking, and real-time voice interaction.

---

## 🏗️ Architecture Overview

The system is strictly decoupled into a **FastAPI backend** and a **React frontend**, communicating synchronously via REST and asynchronously via WebSockets for real-time telemetry and execution streaming.

### Core Modules

1. **Agentic Core (`backend/agents/`)**
   - **graph.py**: The LangGraph state machine orchestrating the execution flow (`planner -> executor -> memory -> security`). Uses a strict 25-step cycle limit and checkpointing (`SQLiteSaver`) to prevent infinite loops and preserve session state.
   - **planner.py**: The "Brain" node. Generates step-by-step plans using dynamic system prompts customized by `user_profile.json`. Incorporates exponential retry backoffs (`tenacity`) and fallback models to prevent execution crashes on LLM failure.
   - **executor.py**: The "Hands" node. Contains `try...except` isolation blocks. Dynamically parses ReAct logs (`Action`/`Action Input`) and maps them to physical tools or loadable plugins.

2. **Tool Arsenal (`backend/tools/`)**
   - **system.py**: Executes terminal commands within a strictly locked-down Docker Sandbox (`alpine` image, `--network none`, `256m` memory limit, `10s` timeout).
   - **browser.py**: Uses Playwright for headless autonomous web navigation and DOM scraping.
   - **vision.py**: Integrates PyAutoGUI, Pillow, and LM Studio vision models. Can take physical screenshots of your desktop and send them to the LLM for multi-modal context analysis.
   - **filesystem.py**: Standard CRUD operations on the local disk.

3. **Memory Pipeline (`backend/memory/`)**
   - **chroma_store.py**: Implements FAISS-styled local vector memory for L2-normalized situational awareness (Episodic Memory).
   - **semantic_graph.json**: Operates as a static graph database capturing hard facts (e.g., "User -> likes -> Pizza").

4. **Security Gateway (`backend/security/`)**
   - **validator.py**: Enforces a microscopic, Zero-Trust **Allowlist** architecture. Blocks Path Traversal (`../`) attacks natively. Automatically flags unknown commands for required human approval in the React UI.
   - **audit.py**: SQLite database (`audit.db`) persistently logging every system request and security incident.
   - **secrets.py**: Avoids plain-text `.env` keys by using the native Windows Credential Manager (`keyring`).

5. **Voice Engine (`backend/voice/`)**
   - **stt.py**: Employs `faster-whisper` (`base.en`) for real-time speech transcription locally.
   - **tts.py**: Employs `piper-tts` hooked to a thread-safe Queue for concurrent, non-blocking conversational audio generation. Includes an interrupt endpoint (`/voice/mute`).
   - **wakeword.py**: Uses `openwakeword` to constantly monitor incoming mic streams for "Alexa" without draining CPU.

---

## 🖥️ The Air Traffic Control (ATC) Dashboard

The React frontend (`frontend/src/App.jsx`) is engineered for maximum operational visibility:

*   **Dark Gradient & Glassmorphism Theme**: Inspired by cinematic tech interfaces.
*   **Live Reasoning Trace**: Streams intermediate agent thoughts and WebSocket communication statuses.
*   **Execution Graph Visualizer**: A pulsing dynamic React Flow chart visually indicating whether the Planner, Executor, or Security layer is taking action.
*   **System Vitals**: Progress rings monitoring host CPU and RAM via a 2-second background broadcasting loop (`psutil` over WebSockets).
*   **Security Gateway Modal**: Stacks untrusted tool invocations (e.g. `file_write`) for physical human approval, grouped with severity colors. Features Batch-Approval capabilities.
*   **Voice 'Push-to-Talk' (PTT)**: Uses modern Browser MediaRecorder APIs allowing users to physically hold a button, record a raw `.wav` stream, and instantly translate it to text on the backend.

---

## ⚡ Quickstart Guide

### 1. Prerequisites
*   Python 3.10+
*   Node.js v18+
*   LM Studio installed and running a local model on `http://localhost:1234/v1`
*   Docker Desktop running (for sandboxing tools)

### 2. Environment Setup
Create a `.env` file in the project root:
```ini
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=local-lm-studio
```

### 3. Start Backend (FastAPI / Uvicorn)
```powershell
Current directory: d:\Projects\JARVIS\
pip install -r backend/requirements.txt
set PYTHONPATH=d:\Projects\JARVIS
python -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Start Frontend (Vite / React)
```powershell
cd frontend
npm install
npm run dev
```

### 5. Access
Navigate to `http://localhost:5173/` in your browser. Hold the **🎤 PTT** button to wake JARVIS up!
