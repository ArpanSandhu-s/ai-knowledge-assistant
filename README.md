# Internship Knowledge Bot

A local, agentic question-answering system over personal documents (resume, business proposal), built with LangChain, Ollama, and a Chroma vector store. Runs entirely on-device — no cloud API calls, no data leaves the machine.

## What it does

The bot answers questions about uploaded PDFs (a resume and a business proposal) and can summarize content, extract key points, or generate quiz questions from retrieved sections. It also correctly handles questions unrelated to the documents (e.g. general knowledge, arithmetic) by answering directly instead of forcing irrelevant retrieval.

## Architecture: Handoff via tool selection

This project uses the **Handoff** pattern from Azure's AI agent design patterns, implemented through LangChain's tool-calling mechanism rather than a hardcoded router.

The first version of this system used a plain Python `if/elif` block to inspect keywords in the user's query (`"summary" in query`) and manually call the matching function. That is not agentic — it is a rules engine that happens to call an LLM. It was replaced with a single `create_agent` instance holding four tools:

- `retrieve_documents` — fetches relevant chunks from the vector store
- `summarize_text` — summarizes a block of already-retrieved text
- `generate_quiz` — generates quiz questions from a block of text
- `extract_key_points` — extracts key points from a block of text

The model itself decides which tool(s) to call, in what order, based on the user's question and each tool's docstring — not a Python conditional. This is the core distinction between routing and Handoff: in Handoff, an agent (here, the single agent reasoning over its tool list) decides where control goes next, rather than the developer deciding it ahead of time.

**Why Handoff over the other four patterns:** the four request types (raw lookup, summarize, quiz, key points) are genuinely different specialist behaviors operating on the same retrieved content, not independent sub-tasks (ruling out Concurrent), not a fixed multi-stage pipeline (ruling out Sequential), and not a task requiring debate or iterative re-planning (ruling out Group Chat and Magentic). Handoff is the correct fit when request *types* differ but the underlying knowledge source is shared.

## Model choice: llama3.2 → qwen2.5:7b

The project started on `llama3.2` (3B parameters, the standard Ollama default). It produced two clear, reproducible failure modes during testing:

1. **Hallucinated tool calls.** Asked a basic math question ("what's 17 times 4"), the model occasionally invented a tool that didn't exist in its tool list (`calculate`) and printed a fake JSON-formatted tool call as its final answer, instead of either calling a real tool or answering directly.
2. **Inconsistent tool invocation.** On vague, meta-phrased queries ("summarize the key points of my resume"), the model sometimes failed to call `retrieve_documents` at all, and instead asked the user to paste in resume text — despite having direct tool access to fetch it itself.

After swapping to `qwen2.5:7b` (7B parameters), both failure modes stopped appearing in testing. Qwen reliably distinguished between "this needs a tool" and "I can answer this directly," and consistently used its actual tool list instead of inventing entries.

**Takeaway:** tool-calling reliability is not purely a prompt-engineering problem — it is also a function of base model capability. Smaller local models are noticeably less consistent at structured tool selection than mid-sized ones, even with identical prompts and tool definitions. This is a real constraint to plan around when choosing a local model for an agentic system, not just a performance/disk-space tradeoff.

## Bug: vague queries broke retrieval

Even after the model swap, one specific query reliably failed: *"summarize the key points of my resume."* Debug logging of the raw model output revealed two distinct causes, found in sequence:

1. The model occasionally passed text copied from a tool's **docstring** as the `retrieve_documents` query argument, rather than the user's actual question. The `extract_key_points` docstring's wording ("key points or main ideas from a block of text") was similar enough to the user's phrasing that the model confused tool description with tool input.
2. On vague, meta-style queries, the model sometimes hallucinated plausible-sounding but entirely fictional resume content (e.g. invented marketing/sales experience that does not appear anywhere in the actual document) rather than retrieving real content.

**Fix:** the system prompt now explicitly instructs the agent to translate vague or meta-phrased questions ("summarize my resume") into concrete search terms ("resume", "skills", "experience") before calling `retrieve_documents`, and explicitly forbids fabricating document content — instructing the model to say retrieval was insufficient rather than guess. After this change, the same query correctly triggered `retrieve_documents` with a real search term, returned actual resume content, and produced an accurate summary with no fabrication.

## Reliability layer

Every agent invocation passes through `run_agent_safely`, which provides:

- **Recursion limit** (`recursion_limit=8`) — caps how many reasoning/tool-call steps the agent can take before stopping, preventing runaway loops.
- **Timeout** (`timeout_seconds=60`) — caps total wall-clock time per query.
- **Malformed-output detection** — a regex check catches cases where the model prints unexecuted tool-call syntax as plain text (the hallucinated-tool failure mode above) and returns a clear, user-facing message instead of leaking raw, confusing output.
- **Exception handling** — any unhandled error returns a readable message rather than a stack trace.

### The speed/reliability tradeoff

The timeout was originally set to 10–20 seconds based on llama3.2's response time. After switching to qwen2.5:7b, multi-tool queries began timing out — not because anything was broken, but because the larger model takes meaningfully longer per inference pass, and an agentic query can require 2–4 model passes (reason → retrieve → reason → summarize → compose). The timeout was raised to 60 seconds to accommodate this.

This is a genuine, demonstrable tradeoff: **larger local models are more reliable at tool selection but slower per response.** On constrained hardware, this is a real design decision a team has to make — not a one-time bug fix.

## Project structure

```
core/
├── agents.py          # single create_agent instance with full tool list + system prompt
├── tools.py            # @tool-decorated functions: retrieve_documents, summarize_text,
│                        #   generate_quiz, extract_key_points
├── orchestration.py     # thin wrapper calling run_agent_safely with timeout + recursion limit
├── safe_runner.py       # resilience layer: timeout, recursion limit, malformed-output detection
└── rag.py               # Chroma vector store + similarity search
db/                       # persisted Chroma vector store
docs/                     # source PDFs (resume, business proposal)
main.py                   # CLI entry point
```

## What I'd improve with more time

- Add LangSmith tracing as a permanent part of the pipeline (currently checked manually per-session) to catch silent wrong answers in production use, not just during debugging.
- Evaluate whether a quantized or distilled model could match qwen2.5:7b's tool-calling reliability at lower latency.
- Add automated test queries (including the specific failure cases documented above) so regressions are caught before a live demo, rather than discovered during one.
