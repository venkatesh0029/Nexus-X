<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0a0a,40:1a0533,80:0d1b2a,100:0a0a0a&height=220&section=header&text=JARVIS-X&fontSize=90&fontColor=00f5ff&fontAlignY=40&desc=Autonomous%20AI%20Operations%20Center&descAlignY=62&descSize=20&animation=fadeIn&fontStyle=bold" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct%20Agent-FF6B35?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Sandboxed-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-00f5ff?style=for-the-badge)](LICENSE)

<br/>

> **JARVIS-X** is a fully local, zero-trust, ReAct-based AI agent orchestration platform.  
> Runs directly on Windows hardware — combining a LangGraph backend with a premium  
> React/Vite dashboard for autonomous tool usage, multi-modal perception, persistent memory, and real-time voice.

<br/>

[🚀 Quickstart](#️-quickstart-guide) · [🏗️ Architecture](#️-architecture-overview) · [🖥️ Dashboard](#️-the-atc-dashboard) · [🐛 Issues](https://github.com/venkatesh0029/Nexus-X/issues)

</div>

---

## 📋 Table of Contents

- [✨ What is JARVIS-X?](#-what-is-jarvis-x)
- [🏗️ Architecture Overview](#️-architecture-overview)
- [🧠 Core Modules](#-core-modules)
- [🖥️ The ATC Dashboard](#️-the-atc-dashboard)
- [⚡ Quickstart Guide](#️-quickstart-guide)
- [📁 Project Structure](#-project-structure)
- [🛠️ Tech Stack](#️-tech-stack)
- [🔐 Security Model](#-security-model)
- [🤝 Contributing](#-contributing)

---

## ✨ What is JARVIS-X?

JARVIS-X is a **fully local**, **zero-trust** autonomous AI agent that runs on your own hardware — no cloud, no data leakage. It uses a **LangGraph ReAct state machine** as its cognitive core, paired with a cinematic React dashboard for real-time operational control.

```
You speak → JARVIS-X thinks → plans → executes → reports back
    🎤          🧠             📋        🛠️          📡
```

**Key highlights:**

- 🧠 **ReAct Agent** — LangGraph state machine with Planner → Executor → Memory → Security flow
- 🔒 **Zero-Trust Security** — Every tool call passes through a strict allowlist & human approval gate
- 🎤 **Voice Interface** — Wake word detection + real-time STT/TTS, fully offline
- 👁️ **Multi-Modal Vision** — Takes desktop screenshots and feeds them to the LLM for context
- 💾 **Persistent Memory** — Episodic (Chroma vector store) + Semantic (JSON knowledge graph)
- 🐳 **Docker Sandboxing** — All shell commands run inside isolated Alpine containers
- 📡 **WebSocket Streaming** — Live reasoning traces, CPU/RAM vitals, execution graph in real time

---

## 🏗️ Architecture Overview

The system is strictly decoupled: a **FastAPI backend** and a **React/Vite frontend**, communicating via REST + WebSockets.

```
┌─────────────────────────────────────────────────────────────────┐
│                        JARVIS-X SYSTEM                          │
│                                                                 │
│  ┌──────────────────────┐       WebSocket / REST               │
│  │   React/Vite ATC     │ ◄──────────────────────────────┐    │
│  │      Dashboard       │                                 │    │
│  └──────────────────────┘                                 │    │
│                                                           │    │
│  ┌────────────────────────────────────────────────────┐   │    │
│  │                  FastAPI Backend                   │───┘    │
│  │                                                    │        │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │        │
│  │  │ Planner  │→ │ Executor │→ │     Memory      │  │        │
│  │  │  (Brain) │  │ (Hands)  │  │ (Chroma + Graph)│  │        │
│  │  └──────────┘  └──────────┘  └─────────────────┘  │        │
│  │        │              │                             │        │
│  │        ▼              ▼                             │        │
│  │  ┌──────────┐  ┌──────────────────────────────┐   │        │
│  │  │ Security │  │         Tool Arsenal          │   │        │
│  │  │ Gateway  │  │ Browser│Vision│Shell│FS│Voice │   │        │
│  │  └──────────┘  └──────────────────────────────┘   │        │
│  │                        │                           │        │
│  │                 ┌──────▼──────┐                    │        │
│  │                 │   Docker    │                    │        │
│  │                 │  Sandbox    │                    │        │
│  │                 └─────────────┘                    │        │
│  └────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Core Modules

### 1. 🤖 Agentic Core — `backend/agents/`

| File | Role | Key Detail |
|---|---|---|
| `graph.py` | LangGraph State Machine | 25-step cycle limit + SQLiteSaver checkpointing |
| `planner.py` | "Brain" Node | Dynamic system prompts from `user_profile.json`; exponential retry via `tenacity` |
| `executor.py` | "Hands" Node | Isolated `try/except` blocks; parses ReAct logs (`Action` / `Action Input`) |

### 2. 🛠️ Tool Arsenal — `backend/tools/`

| Tool | Technology | Capability |
|---|---|---|
| `system.py` | Docker Alpine | Terminal commands in `--network none`, 256MB RAM, 10s timeout sandbox |
| `browser.py` | Playwright | Headless web navigation & DOM scraping |
| `vision.py` | PyAutoGUI + Pillow | Desktop screenshots → LM Studio vision model |
| `filesystem.py` | Python stdlib | CRUD operations on local disk |

### 3. 💾 Memory Pipeline — `backend/memory/`

```
┌──────────────────────────┐    ┌───────────────────────────┐
│     Episodic Memory       │    │      Semantic Memory       │
│   (chroma_store.py)       │    │   (semantic_graph.json)    │
│                           │    │                            │
│  FAISS-style L2-norm      │    │  Static fact graph:        │
│  vector store for         │    │  "User → likes → Pizza"    │
│  situational awareness    │    │  Hard knowledge, persisted │
└──────────────────────────┘    └───────────────────────────┘
```

### 4. 🔐 Security Gateway — `backend/security/`

| Component | Function |
|---|---|
| `validator.py` | Zero-Trust Allowlist; blocks Path Traversal (`../`); flags unknowns for human approval |
| `audit.py` | SQLite `audit.db` — persistent log of every request & security incident |
| `secrets.py` | Windows Credential Manager via `keyring` — no plain-text `.env` API keys |

### 5. 🎤 Voice Engine — `backend/voice/`

| Module | Technology | Role |
|---|---|---|
| `stt.py` | `faster-whisper` (base.en) | Real-time local speech transcription |
| `tts.py` | `piper-tts` + thread-safe Queue | Non-blocking concurrent audio generation |
| `wakeword.py` | `openwakeword` | Always-on "Alexa" wake word monitoring |

---

## 🖥️ The ATC Dashboard

The React frontend is designed for **maximum operational visibility** — inspired by cinematic tech interfaces:

```
┌──────────────────────────────────────────────────────────────────┐
│  🌑  JARVIS-X Air Traffic Control                       [🎤 PTT] │
├─────────────────────┬────────────────────────────────────────────┤
│   Execution Graph   │          Live Reasoning Trace              │
│                     │                                            │
│  [Planner]  ●──►   │  > Thinking: analyzing user intent...     │
│      │              │  > Action: browser_navigate               │
│  [Executor] ●──►   │  > Action Input: https://...              │
│      │              │  > Observation: Page loaded               │
│  [Security] ●──►   │  > Final Answer: Task complete ✓          │
│                     │                                            │
├─────────────────────┼────────────────────────────────────────────┤
│    System Vitals    │        🔐 Security Gateway                 │
│                     │                                            │
│  CPU  [████░] 72%   │  ⚠️  file_write → /system32   [BLOCK]    │
│  RAM  [███░░] 58%   │  ✅  browser_navigate          [ALLOW]    │
│                     │  ❓  unknown_tool_xyz    [APPROVE?] 🔴     │
└─────────────────────┴────────────────────────────────────────────┘
```

**Dashboard Features:**
- 🌑 **Dark Glassmorphism Theme** — cinematic high-contrast interface
- 📡 **Live Reasoning Trace** — streams intermediate agent thoughts via WebSocket
- 🔀 **Execution Graph Visualizer** — pulsing React Flow chart showing active nodes
- 📊 **System Vitals** — CPU & RAM rings updating every 2 seconds via `psutil`
- 🛡️ **Security Gateway Modal** — human approval queue with severity colours & batch approve
- 🎤 **Push-to-Talk (PTT)** — Browser MediaRecorder records `.wav` → instant backend transcription

---

## ⚡ Quickstart Guide

### Prerequisites

```
✅  Python 3.10+
✅  Node.js v18+
✅  LM Studio running on http://localhost:1234/v1
✅  Docker Desktop running
```

### Step 1 — Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=local-lm-studio
```

### Step 2 — Start the Backend

```bash
# From: d:\Projects\JARVIS\
pip install -r backend/requirements.txt

set PYTHONPATH=d:\Projects\JARVIS

python -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 3 — Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### Step 4 — Launch 🚀

Open **[http://localhost:5173](http://localhost:5173)** and hold the **🎤 PTT** button to wake JARVIS-X!

---

## 📁 Project Structure

```
Nexus-X/
│
├── 📁 backend/
│   ├── 📁 agents/              # LangGraph ReAct state machine
│   │   ├── graph.py            # Main orchestration graph
│   │   ├── planner.py          # LLM planning node
│   │   └── executor.py         # Tool execution node
│   │
│   ├── 📁 tools/               # Physical capability layer
│   │   ├── system.py           # Docker-sandboxed shell
│   │   ├── browser.py          # Playwright web automation
│   │   ├── vision.py           # Screenshot + vision LLM
│   │   └── filesystem.py       # Local file CRUD
│   │
│   ├── 📁 memory/              # Persistent context
│   │   ├── chroma_store.py     # Episodic vector memory
│   │   └── semantic_graph.json # Fact knowledge graph
│   │
│   ├── 📁 security/            # Zero-trust layer
│   │   ├── validator.py        # Allowlist + approval gate
│   │   ├── audit.py            # SQLite audit logging
│   │   └── secrets.py          # Windows Credential Manager
│   │
│   ├── 📁 voice/               # Offline voice I/O
│   │   ├── stt.py              # faster-whisper transcription
│   │   ├── tts.py              # piper-tts generation
│   │   └── wakeword.py         # openwakeword detection
│   │
│   └── 📁 api/
│       └── main.py             # FastAPI + WebSocket server
│
├── 📁 frontend/
│   └── 📁 src/
│       └── App.jsx             # React ATC dashboard
│
├── 📁 docs/                    # Documentation
├── 📁 .github/workflows/       # CI/CD pipelines
├── .env.example
├── pyrightconfig.json
└── README.md
```

---

## 🛠️ Tech Stack

<div align="center">

### 🐍 Backend
![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6B35?style=for-the-badge&logo=langchain&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-222222?style=for-the-badge&logo=gunicorn&logoColor=white)

### 🤖 AI & ML
![LM Studio](https://img.shields.io/badge/LM_Studio-Local_LLM-8B5CF6?style=for-the-badge)
![Whisper](https://img.shields.io/badge/faster--whisper-STT-FF4444?style=for-the-badge)
![Piper TTS](https://img.shields.io/badge/piper--tts-TTS-00AA88?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B00?style=for-the-badge)

### ⚛️ Frontend
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![React Flow](https://img.shields.io/badge/React_Flow-Execution_Graph-FF0072?style=for-the-badge)

### 🔧 DevOps & Tools
![Docker](https://img.shields.io/badge/Docker-Sandbox-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Browser-45BA4B?style=for-the-badge&logo=playwright&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Audit_Log-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Pyright](https://img.shields.io/badge/Pyright-Type_Check-1B6AC6?style=for-the-badge)

</div>

---

## 🔐 Security Model

JARVIS-X implements a **Zero-Trust** security architecture — nothing runs without verification:

```
Every tool call  →  Allowlist Check  →  Known & Safe?  →  Execute ✅
                          │                   │
                          ▼                   ▼ No
                     Block + Log         Human Approval Gate
                    (audit.db)           (React UI modal)
                          │                   │
                          └──── audit.db ──────┘
                               (all events logged)
```

- **No command runs without passing the allowlist** — unknown tools are held for human review
- **Path traversal attacks** (`../`) are blocked natively at the validator layer
- **No plain-text secrets** — API keys stored in Windows Credential Manager via `keyring`
- **Shell isolation** — Docker Alpine with `--network none`, 256MB RAM cap, 10s timeout

---

## 🤝 Contributing

Contributions are warmly welcome!

```bash
# 1. Fork the repo on GitHub

# 2. Create your feature branch
git checkout -b feature/amazing-feature

# 3. Make your changes and commit
git commit -m "feat: add amazing feature"

# 4. Push to your fork
git push origin feature/amazing-feature

# 5. Open a Pull Request
```

Please ensure:
- Pyright type checking passes: `pyright`
- Pre-commit hooks run clean: `pre-commit run --all-files`
- New tools/agents include appropriate tests

---

## 👤 Author

<div align="center">

**venkatesh0029**

[![GitHub](https://img.shields.io/badge/GitHub-venkatesh0029-181717?style=for-the-badge&logo=github)](https://github.com/venkatesh0029)

*If you find this project useful, consider giving it a ⭐ — it helps a lot!*

</div>

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0a0a,40:1a0533,80:0d1b2a,100:0a0a0a&height=120&section=footer&animation=fadeIn" width="100%"/>

**JARVIS-X** — *Because your AI shouldn't need the cloud to be powerful.*

</div>
