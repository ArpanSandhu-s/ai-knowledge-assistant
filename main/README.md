# 🧠 Nexus AI Workspace
### Multi-Agent Group Chat Orchestration Platform

A local AI workspace implementing the **Azure AI Agent Design Pattern: Group Chat Orchestration** — built with LangChain, Ollama (llama3.2), ChromaDB, and Streamlit.

---

## 🏗️ Architecture: Group Chat Orchestration Pattern

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
```

Unlike a Router (hardcoded if/else rules) or a Sequential Chain (fixed pipeline), Group Chat uses a **Manager LLM** that autonomously reads the full shared transcript after every turn and decides which specialist speaks next — non-deterministic, dynamic coordination.

---

## 🔩 The 4 Core Pillars

| Pillar | Component | Role |
|---|---|---|
| 1 | `AGENT_REGISTRY` | Defines specialist capabilities — Manager reads this to make routing decisions |
| 2 | `AGENT_SYSTEM_PROMPTS` | Each specialist has a strict, isolated role definition |
| 3 | `GroupChatManager` | An LLM that reads the shared transcript and selects the next speaker |
| 4 | `GroupChatOrchestrator` | Runs the loop: Manager → Specialist → Transcript → repeat until FINISH |

---

## 🤖 Specialist Agent Roster

| Agent | Trigger | Responsibility |
|---|---|---|
| 🗂️ **Data Analyst Agent** | Document, PDF, summarize, quiz, key points | RAG retrieval + document analysis via ChromaDB |
| 🌤️ **Weather Agent** | Weather, temperature, forecast, climate | Live weather via Open-Meteo API with wttr.in fallback |
| 🤖 **Generalist Agent** | Greetings, math, general knowledge | Conversational assistant with full chat memory |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Orchestration | LangChain (Python) |
| Local LLM | Ollama — `llama3.2` (3B) |
| Embeddings | Ollama — `nomic-embed-text` (768d) |
| Vector Store | ChromaDB (timestamp-isolated collections) |
| Weather API | Open-Meteo (primary) + wttr.in (fallback) |

---

## 🚀 How to Run Locally

### Prerequisites
```bash
# Install Ollama and pull required models
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

## 📁 Project Structure

```
main/
├── gui_app.py              # Streamlit UI + orchestration integration
├── group_chat_engine.py    # Azure Group Chat Orchestration pattern implementation
│   ├── AGENT_REGISTRY          # Pillar 1 — Specialist definitions
│   ├── AGENT_SYSTEM_PROMPTS    # Pillar 2 — Isolated agent roles
│   ├── GroupChatManager        # Pillar 3 — LLM-based speaker selection
│   └── GroupChatOrchestrator   # Pillar 4 — Dynamic loop + termination engine
├── chroma_db/              # Local vector store (auto-created)
├── chat_memory.json        # Persistent chat history (auto-created)
└── .streamlit/
    └── secrets.toml        # API keys (not committed)
```

---

## ⚡ Key Design Decisions

**Why Group Chat over Router?**
A Router uses hardcoded keyword matching — `if "weather" in query`. The Manager Agent in Group Chat calls `llm.invoke()` on the full transcript to make its decision. The routing logic itself is intelligent, not rule-based.

**Why timestamp-isolated ChromaDB collections?**
On Windows, ChromaDB holds file locks on `data_level0.bin`. Deleting and recreating collections on new file uploads triggers `[WinError 32]`. Timestamp-based collection names (`docs_1234567890`) isolate each upload without touching existing locked files.

**Why pre-fetch weather/RAG before the orchestration loop?**
`llama3.2` has no internet access. Weather data is fetched via `requests` and RAG chunks are pulled from ChromaDB before the loop starts. These are injected into the shared transcript as system context, so specialist agents work with real data.

**Termination Engine design:**
Rather than relying on the Manager LLM to signal FINISH (which can be unreliable with smaller models), the termination check first inspects the transcript directly — if any specialist has already responded, it returns FINISH without an extra LLM call. The LLM is only invoked for the initial routing decision.

---

## 🔗 References

- [Azure AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [LangChain Documentation](https://python.langchain.com/)
- [Ollama](https://ollama.com/)
- [ChromaDB](https://docs.trychroma.com/)
