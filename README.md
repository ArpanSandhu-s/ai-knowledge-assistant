# 🧠 Nexus AI Workspace
### Multi-Agent Group Chat Orchestration Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ai-knowledge-assistant-gapsv65wvsvxg6absfzemq.streamlit.app/)

🔗 **Live Demo:** https://ai-knowledge-assistant-gapsv65wvsvxg6absfzemq.streamlit.app/

---

## What it does

An interactive AI workspace that implements the **Azure AI Agent Design Pattern: Group Chat Orchestration**. Users can upload PDFs, ask document questions, check live weather, solve math, or just chat — all routed dynamically by a Manager LLM to the right specialist agent.

---

## Architecture: Group Chat Orchestration

This project implements the [Group Chat Orchestration pattern](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) from the Microsoft Azure Architecture Center.

```
User Query
    │
    ▼
┌─────────────────────┐
│   GroupChatManager  │  ◄── LLM reads shared transcript → picks next speaker or FINISH
└──────────┬──────────┘
           │
  ┌────────┼────────┐
  ▼        ▼        ▼
Data    Weather  Generalist
Analyst  Agent    Agent
  │        │        │
  └────────┼────────┘
           ▼
    Shared Transcript
           │
           ▼
        Result
```

Unlike a **Router** (hardcoded `if/else` keyword rules) or a **Sequential Chain** (fixed pipeline), Group Chat uses a **Manager LLM** that autonomously reads the full shared transcript after every turn and decides which specialist speaks next — non-deterministic, dynamic coordination.

**Evolution from v1:** The first version of this system used a plain Python `if/elif` block to inspect keywords in the user query (`"summary" in query`) and manually call matching functions. That is not agentic — it is a rules engine that happens to call an LLM. It was replaced with the Group Chat Orchestration pattern where the Manager LLM itself decides routing based on the full conversation context.

---

## The 4 Core Pillars

| Pillar | Component | Role |
|---|---|---|
| 1 | `AGENT_REGISTRY` | Defines specialist capabilities — Manager reads this to make routing decisions |
| 2 | `AGENT_SYSTEM_PROMPTS` | Each specialist has a strict, isolated role definition |
| 3 | `GroupChatManager` | An LLM that reads the shared transcript and selects the next speaker |
| 4 | `GroupChatOrchestrator` | Runs the loop: Manager → Specialist → Transcript → repeat until FINISH |

---

## Specialist Agent Roster

| Agent | Trigger | Knowledge Source |
|---|---|---|
| 🗂️ **Data Analyst Agent** | Document, PDF, summarize, quiz, key points | ChromaDB RAG (nomic-embed-text embeddings) |
| 🌤️ **Weather Agent** | Weather, temperature, forecast, climate | Open-Meteo API + wttr.in fallback |
| 🤖 **Generalist Agent** | Greetings, math, general knowledge | LLM base knowledge + conversation memory |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Orchestration | LangChain (Python) |
| Local LLM | Ollama — `llama3.2` (3B) |
| Cloud LLM | Groq — `llama-3.1-8b-instant` |
| Embeddings (local) | Ollama — `nomic-embed-text` (768d) |
| Embeddings (cloud) | HuggingFace — `all-MiniLM-L6-v2` |
| Vector Store | ChromaDB (timestamp-isolated collections) |
| Weather API | Open-Meteo (primary) + wttr.in (fallback) |

---

## Key Design Decisions

**Why Group Chat over Router?**
A Router uses hardcoded keyword matching. The `GroupChatManager` calls `llm.invoke()` on the full shared transcript to make its routing decision — the logic itself is intelligent, not rule-based.

**Why timestamp-isolated ChromaDB collections?**
On Windows, ChromaDB holds file locks on `data_level0.bin`. Deleting collections on new uploads triggers `[WinError 32]`. Timestamp-based collection names (`docs_1234567890`) isolate each upload without touching locked files.

**Why pre-fetch weather/RAG before the orchestration loop?**
`llama3.2` has no internet access. Weather data is fetched via `requests` and RAG chunks pulled from ChromaDB before the loop starts — injected into the shared transcript as system context so specialist agents work with real data.

**Termination Engine design:**
Rather than relying solely on the Manager LLM to signal `FINISH` (unreliable with smaller models), the termination check first inspects the transcript directly — if any specialist has already responded, it returns `FINISH` without an extra LLM call. The LLM is only invoked for the initial routing decision.

**Dual runtime (local + cloud):**
The app detects whether Ollama is running on `localhost:11434`. If yes → uses `llama3.2` + `nomic-embed-text` locally. If no → switches to Groq (`llama-3.1-8b-instant`) + HuggingFace embeddings for cloud deployment. Zero code changes needed between environments.

---

## How to Run Locally

### Prerequisites
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Setup
```bash
git clone https://github.com/ArpanSandhu-s/ai-knowledge-assistant
cd ai-knowledge-assistant/main
pip install -r requirements.txt
```

### Run
```bash
streamlit run gui_app.py
```

---

## Project Structure

```
main/
├── gui_app.py              # Streamlit UI + Group Chat integration
├── group_chat_engine.py    # Azure Group Chat Orchestration implementation
│   ├── AGENT_REGISTRY          # Pillar 1 — Specialist definitions
│   ├── AGENT_SYSTEM_PROMPTS    # Pillar 2 — Isolated agent roles  
│   ├── GroupChatManager        # Pillar 3 — LLM-based speaker selection
│   └── GroupChatOrchestrator   # Pillar 4 — Dynamic loop + termination engine
├── chroma_db/              # Local vector store (auto-created)
├── chat_memory.json        # Persistent chat history (auto-created)
└── .streamlit/
    └── secrets.toml        # API keys (not committed)

core/                       # v1 Handoff pattern implementation (reference)
├── agents.py
├── tools.py
├── orchestration.py
├── safe_runner.py
└── rag.py
```

---

## References

- [Azure AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [LangChain Documentation](https://python.langchain.com/)
- [Ollama](https://ollama.com/)
- [ChromaDB](https://docs.trychroma.com/)
- [Groq](https://console.groq.com/)
