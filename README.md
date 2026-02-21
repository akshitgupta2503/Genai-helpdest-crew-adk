# 🤖 AI-Powered Multi-Agent Helpdesk System

An intelligent, multi-agent IT helpdesk system that automates support ticket resolution using **CrewAI**, **Google ADK**, **LangGraph**, **MCP (Model Context Protocol)**, and **Agent-to-Agent (A2A)** communication — all orchestrated through a central coordinator and powered by local LLMs via **Ollama**.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [License](#license)

---

## Overview

This system receives a user's support ticket (e.g., *"I cannot log in"*), routes it through a pipeline of specialized AI agents, and produces:

- A **structured JSON report** with troubleshooting steps and escalation decisions.
- A **human-readable Markdown report** summarizing the resolution.

Each agent is built on a different AI framework, demonstrating real-world multi-framework orchestration.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Streamlit / CLI Interface                  │
└────────────────────────────┬─────────────────────────────────┘
                             │  User submits ticket
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                      COORDINATOR                             │
│              (Starts all agents, dispatches tickets)         │
└────────────────────────────┬─────────────────────────────────┘
                             │  A2A Message Bus
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────────┐  ┌────────────────┐
│  CrewAI       │  │  Google ADK       │  │  LangGraph      │
│  Agents (5)   │  │  Search Agent     │  │  Validation     │
│               │  │                   │  │  Agent          │
│ • Triage      │  │  Enriches context │  │                 │
│ • Retrieval   │  │  with external    │  │  Rule engine +  │
│ • Knowledge   │  │  search data      │  │  LLM-based      │
│ • Troubleshoot│  │                   │  │  hallucination  │
│ • Escalation  │  │                   │  │  detection      │
└───────┬───────┘  └────────┬──────────┘  └───────┬─────────┘
        │                   │                     │
        └───────────────────┼─────────────────────┘
                            ▼
               ┌─────────────────────┐
               │   Monitor Agent      │
               │   (Final Output)     │
               │   → final.json       │
               │   → final.md         │
               └─────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     MCP Tool Server                          │
│            FastAPI server exposing shared tools               │
│         (SQLite KB lookup, File parser, Web search)          │
│                  http://localhost:8001                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Agent Pipeline

| #  | Agent                | Framework  | Role                                                                 |
|----|----------------------|------------|----------------------------------------------------------------------|
| 1  | **Triage Agent**     | CrewAI     | Classifies the ticket — extracts category, urgency, summary, entities |
| 2  | **Retrieval Agent**  | CrewAI     | Searches the knowledge base (SQLite) and web for relevant solutions   |
| 3  | **Knowledge Agent**  | CrewAI     | Synthesises retrieved information into a concise knowledge summary    |
| 4  | **Troubleshoot Agent** | CrewAI   | Generates step-by-step troubleshooting instructions                  |
| 5  | **Escalation Agent** | CrewAI     | Decides whether to escalate the ticket to a human agent              |
| 6  | **Search Agent**     | Google ADK | Enriches context with external search data                           |
| 7  | **LangGraph Agent**  | LangGraph  | Validates outputs — rule checks, SLA enforcement, hallucination detection |
| 8  | **Monitor Agent**    | Custom     | Aggregates final results and writes `final.json` / `final.md`        |

---

## Tech Stack

| Component              | Technology                        |
|------------------------|-----------------------------------|
| **Agent Frameworks**   | CrewAI, Google ADK, LangGraph     |
| **LLM Runtime**        | Ollama (local) — `gemma:2b`       |
| **Inter-Agent Comms**  | Custom A2A Protocol (message bus)  |
| **Tool Server**        | MCP Server (FastAPI + Uvicorn)     |
| **Knowledge Base**     | SQLite                             |
| **Web Interface**      | Streamlit                          |
| **Configuration**      | YAML agent configs                 |
| **Data Validation**    | Pydantic                           |

---

## Project Structure

```
genai_helpdesk/
│
├── main.py                    # CLI entry point (starts MCP + Coordinator)
├── streamlit_app.py           # Streamlit Web UI
├── monitor.py                 # Monitor agent — writes final output
├── create_db.py               # Seeds the SQLite knowledge base
├── test_runner.py             # Test runner script
├── coordinator_input.txt      # Temp file for ticket input
├── requirements.txt           # Python dependencies
├── .gitignore
│
├── coordinator/
│   └── coordinator.py         # Central orchestrator — starts all agents
│
├── crew/                      # CrewAI-based agents
│   ├── triage_agent.py
│   ├── retrieval_agent.py
│   ├── knowledge_agent.py
│   ├── troubleshoot_agent.py
│   └── escalation_agent.py
│
├── adk_agents/                # Google ADK agents
│   ├── agent_base.py
│   ├── search_agent.py
│   └── search_agent.yaml
│
├── langgraph/                 # LangGraph validation agent
│   └── langgraph_agent.py
│
├── a2a/                       # Agent-to-Agent communication protocol
│   └── a2a_protocol.py
│
├── mcp_server/                # MCP Tool Server (FastAPI)
│   └── mcp_server.py
│
├── tools/                     # Shared tools exposed via MCP
│   ├── sqlite_tool.py
│   ├── file_parser.py
│   └── web_search.py
│
├── utils/                     # Utility modules
│   ├── ollama_client.py
│   ├── ollama_patch.py
│   ├── crewai_ollama.py
│   ├── crewai_patch_disable_llm.py
│   └── json_parser.py
│
├── yaml/                      # YAML configurations for each agent
│   ├── triage_agent.yaml
│   ├── retrieval_agent.yaml
│   ├── knowledge_agent.yaml
│   ├── troubleshoot_agent.yaml
│   ├── escalation_agent.yaml
│   └── langgraph_agent.yaml
│
├── data/
│   └── sample_kb.sqlite       # SQLite knowledge base
│
└── output/                    # Generated at runtime (gitignored)
    ├── logs/
    │   └── run.log
    ├── final.json
    └── final.md
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Ollama** installed and running locally — [Install Ollama](https://ollama.com/)
- Pull the required model:
  ```bash
  ollama pull gemma:2b
  ```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/akshit-helpdest-crew-adk.git
   cd genai_helpdesk
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**

   - **Windows (PowerShell)**
     ```powershell
     .\.venv\Scripts\Activate
     ```
   - **macOS / Linux**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Seed the knowledge base** (first-time setup)
   ```bash
   python create_db.py
   ```

---

## Usage

### Option 1 — Streamlit Web UI (Recommended)

```bash
streamlit run streamlit_app.py
```

Opens a browser at `http://localhost:8501` with:
- A text area to submit support tickets
- Live system logs
- Final Markdown and JSON output panels

### Option 2 — CLI Mode

```bash
python main.py
```

This starts both the MCP server and the coordinator, then presents an interactive CLI:

```
=== AI Multi-Agent Helpdesk (CLI Mode) ===
Type your issue below. Type 'exit' to quit.

Enter issue: I cannot log in to my account
✔ Issue submitted: "I cannot log in to my account"
Agents processing...
```

---

## How It Works

1. **User submits a ticket** via Streamlit UI or CLI.
2. **Coordinator** dispatches the ticket to the **Triage Agent** over the A2A message bus.
3. **Triage Agent** (CrewAI) classifies the issue → sends `triage_result` to **Retrieval Agent**.
4. **Retrieval Agent** (CrewAI) queries the SQLite KB and web search via the **MCP Server** → sends `retrieval_ready`.
5. **Knowledge Agent** (CrewAI) synthesises the retrieved data into a concise summary.
6. **Search Agent** (Google ADK) enriches the context with additional external search results → sends `adk_context`.
7. **Troubleshoot Agent** (CrewAI) generates step-by-step troubleshooting instructions → sends `troubleshoot_done`.
8. **LangGraph Validation Agent** intercepts intermediate outputs, applies rule-based checks (ticket ID, step count limits) and LLM-powered hallucination detection.
9. **Escalation Agent** (CrewAI) decides whether the issue needs human intervention → sends `final_decision`.
10. **Monitor Agent** aggregates everything, writes `output/final.json` and `output/final.md`.

---

## Configuration

All agent configurations are stored in `yaml/` as YAML files. Each file defines:

- `name` — Agent identifier
- `role` — Description of the agent's role
- `goal` — What the agent aims to achieve
- `backstory` — Context for the LLM persona
- `tools` — List of MCP tools the agent can use

The LangGraph agent has additional configuration for validation rules and message routing.

---

## Key Protocols

### A2A (Agent-to-Agent) Protocol

A thread-safe in-process message bus (`a2a/a2a_protocol.py`) enabling structured communication between agents using **Pydantic** message envelopes:

```python
class A2AMessage(BaseModel):
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any]
    timestamp: str
```

### MCP (Model Context Protocol) Server

A **FastAPI** server (`mcp_server/mcp_server.py`) that exposes shared tools:

| Tool             | Description                                  |
|------------------|----------------------------------------------|
| `sqlite_lookup`  | Keyword search across the SQLite knowledge base |
| `file_parser`    | Reads and returns file contents               |
| `web_search`     | Web search (mock — can be replaced with a live API) |

---

## License

This project is for educational and demonstration purposes.
