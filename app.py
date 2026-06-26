# """
# app.py
# ------
# Streamlit entry point for the Local Multi-Agent RAG application.

# FIX APPLIED: sys.path injection at the very top so that `core.*` is always
# importable regardless of which directory Streamlit is launched from.

# NEW FEATURES:
#   - Document ingestion panel (PDF, TXT, MD, DOCX) — uploads go straight to ChromaDB
#   - Knowledge base stats panel
#   - Conversation history with role badges
#   - Expandable error detail drawer

# Run with:
#     streamlit run app.py
# """

# import sys
# import os

# # ──────────────────────────────────────────────
# # PATH FIX — must happen BEFORE any local imports
# # Ensures `from core.xxx import yyy` works regardless
# # of the working directory when Streamlit is launched.
# # ──────────────────────────────────────────────
# _APP_DIR = os.path.dirname(os.path.abspath(__file__))
# if _APP_DIR not in sys.path:
#     sys.path.insert(0, _APP_DIR)

# # ──────────────────────────────────────────────
# # Standard library
# # ──────────────────────────────────────────────
# import time
# import tempfile
# import hashlib
# from pathlib import Path

# import streamlit as st

# # ──────────────────────────────────────────────
# # Page config — MUST be first Streamlit call
# # ──────────────────────────────────────────────
# st.set_page_config(
#     page_title="Knowledge Agent",
#     page_icon="🧠",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ──────────────────────────────────────────────
# # CSS
# # ──────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

# html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

# .stApp { background-color: #0f1117; }

# section[data-testid="stSidebar"] {
#     background-color: #161b22;
#     border-right: 1px solid #21262d;
# }

# /* ── Chat bubbles ── */
# .chat-bubble {
#     padding: 14px 18px;
#     border-radius: 10px;
#     margin-bottom: 12px;
#     line-height: 1.65;
#     font-size: 0.92rem;
# }
# .chat-user      { background:#1c2128; border-left:3px solid #388bfd; color:#e6edf3; }
# .chat-assistant { background:#161b22; border-left:3px solid #3fb950; color:#e6edf3; }
# .chat-error     { background:#1a0e0e; border-left:3px solid #f85149; color:#ffa198; }

# .step-badge {
#     display:inline-block; font-size:0.72rem;
#     font-family:'JetBrains Mono',monospace;
#     color:#8b949e; background:#21262d;
#     border-radius:4px; padding:2px 7px; margin-top:6px;
# }

# /* ── Input ── */
# .stTextArea textarea {
#     background-color:#1c2128 !important;
#     color:#e6edf3 !important;
#     border:1px solid #30363d !important;
#     border-radius:8px !important;
#     font-size:0.9rem !important;
# }

# /* ── Buttons ── */
# .stButton > button {
#     background-color:#238636; color:#fff;
#     border:none; border-radius:6px;
#     padding:8px 20px; font-weight:500;
#     font-size:0.88rem; transition:background .15s;
# }
# .stButton > button:hover { background-color:#2ea043; }

# /* Upload zone */
# [data-testid="stFileUploader"] {
#     background:#1c2128;
#     border:1px dashed #30363d;
#     border-radius:8px;
#     padding:4px;
# }

# /* Metrics */
# [data-testid="metric-container"] {
#     background:#1c2128; border:1px solid #21262d;
#     border-radius:8px; padding:12px;
# }

# /* Ingestion success */
# .ingest-ok {
#     background:#0d1f12; border-left:3px solid #3fb950;
#     color:#3fb950; padding:10px 14px; border-radius:6px;
#     font-size:0.83rem; margin-bottom:8px;
# }
# .ingest-err {
#     background:#1a0e0e; border-left:3px solid #f85149;
#     color:#ffa198; padding:10px 14px; border-radius:6px;
#     font-size:0.83rem; margin-bottom:8px;
# }

# hr  { border-color:#21262d; }
# footer { visibility:hidden; }
# </style>
# """, unsafe_allow_html=True)


# # ──────────────────────────────────────────────
# # Constants
# # ──────────────────────────────────────────────
# CHROMA_PATH  = "./chroma_db"
# COLLECTION   = "knowledge_base"
# EMBED_MODEL  = "nomic-embed-text"
# CHUNK_SIZE   = 800
# CHUNK_OVERLAP = 100

# SUPPORTED_TYPES = {
#     "application/pdf":  ".pdf",
#     "text/plain":       ".txt",
#     "text/markdown":    ".md",
#     "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
# }


# # ──────────────────────────────────────────────
# # Lazy loaders (cached across reruns)
# # ──────────────────────────────────────────────
# @st.cache_resource(show_spinner="Connecting to Knowledge Agent…")
# def load_agent():
#     from core.agents import get_agent          # noqa
#     from core.orchestration import run_query   # noqa
#     return run_query


# @st.cache_resource(show_spinner="Initialising vector store…")
# def load_vectorstore():
#     from langchain_ollama import OllamaEmbeddings
#     from langchain_chroma import Chroma
#     embeddings = OllamaEmbeddings(model=EMBED_MODEL)
#     return Chroma(
#         collection_name=COLLECTION,
#         embedding_function=embeddings,
#         persist_directory=CHROMA_PATH,
#     )


# def get_doc_count() -> int:
#     """Return the number of documents stored in Chroma (0 on any error)."""
#     try:
#         vs = load_vectorstore()
#         return vs._collection.count()
#     except Exception:
#         return 0


# # ──────────────────────────────────────────────
# # Document ingestion helper
# # ──────────────────────────────────────────────
# def ingest_file(uploaded_file) -> tuple[bool, str]:
#     """
#     Parse an uploaded Streamlit file, chunk it, embed it, and store it in
#     ChromaDB.  Returns (success: bool, message: str).
#     """
#     try:
#         from langchain_community.document_loaders import (
#             PyPDFLoader, TextLoader, UnstructuredMarkdownLoader,
#             UnstructuredWordDocumentLoader,
#        )
#         from langchain_text_splitters import RecursiveCharacterTextSplitter
#     except ImportError as e:
#         print("Import error:", e)

    
       

#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=CHUNK_SIZE,
#             chunk_overlap=CHUNK_OVERLAP,
#         )

#         suffix = Path(uploaded_file.name).suffix.lower()

#         # Write to a temp file so loaders can open it by path
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#             tmp.write(uploaded_file.read())
#             tmp_path = tmp.name

#         # Choose loader
#         if suffix == ".pdf":
#             loader = PyPDFLoader(tmp_path)
#         elif suffix in (".txt",):
#             loader = TextLoader(tmp_path, encoding="utf-8")
#         elif suffix == ".md":
#             loader = UnstructuredMarkdownLoader(tmp_path)
#         elif suffix in (".docx", ".doc"):
#             loader = UnstructuredWordDocumentLoader(tmp_path)
#         else:
#             os.unlink(tmp_path)
#             return False, f"Unsupported file type: {suffix}"

#         docs = loader.load()
#         os.unlink(tmp_path)

#         if not docs:
#             return False, "No text could be extracted from the file."

#         # Stamp source metadata
#         for doc in docs:
#             doc.metadata["source"] = uploaded_file.name
#             doc.metadata["ingested_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

#         # Chunk
#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=CHUNK_SIZE,
#             chunk_overlap=CHUNK_OVERLAP,
#         )
#         chunks = splitter.split_documents(docs)

#         if not chunks:
#             return False, "Document produced no usable chunks after splitting."

#         # Generate stable IDs so re-uploading the same file doesn't duplicate
#         ids = [
#             hashlib.md5(
#                 f"{uploaded_file.name}_{i}_{c.page_content[:60]}".encode()
#             ).hexdigest()
#             for i, c in enumerate(chunks)
#         ]

#         vs = load_vectorstore()
#         vs.add_documents(chunks, ids=ids)

#         return True, (
#             f"✓ '{uploaded_file.name}' ingested — "
#             f"{len(chunks)} chunk(s) added to the knowledge base."
#         )

#     except Exception as exc:
#         return False, f"Ingestion failed: {type(exc).__name__}: {exc}"


# # ──────────────────────────────────────────────
# # Session state init
# # ──────────────────────────────────────────────
# for key, default in [
#     ("messages",     []),
#     ("total_steps",  0),
#     ("query_count",  0),
#     ("ingest_msgs",  []),
# ]:
#     if key not in st.session_state:
#         st.session_state[key] = default


# # ──────────────────────────────────────────────
# # ── SIDEBAR ──────────────────────────────────
# # ──────────────────────────────────────────────
# with st.sidebar:
#     st.markdown(
#         "<h2 style='color:#e6edf3;font-size:1.1rem;margin-bottom:2px;'>🧠 Knowledge Agent</h2>"
#         "<span style='color:#8b949e;font-size:0.80rem;'>Llama 3.2 · ChromaDB · Ollama</span>",
#         unsafe_allow_html=True,
#     )
#     st.divider()

#     # ── Tool list ──
#     st.markdown(
#         "<p style='color:#8b949e;font-size:0.78rem;font-weight:600;"
#         "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;'>Available Tools</p>",
#         unsafe_allow_html=True,
#     )
#     for name, desc in [
#         ("🔍 retrieve_documents", "Search the vector knowledge base"),
#         ("📝 summarize_text",     "Summarise retrieved content"),
#         ("❓ generate_quiz",      "Create a 3-question MCQ quiz"),
#         ("💡 extract_key_points", "Pull out the key facts & concepts"),
#     ]:
#         st.markdown(
#             f"<div style='margin-bottom:8px;'>"
#             f"<span style='font-size:0.84rem;font-weight:500;color:#e6edf3;'>{name}</span><br>"
#             f"<span style='font-size:0.77rem;color:#8b949e;'>{desc}</span>"
#             f"</div>",
#             unsafe_allow_html=True,
#         )

#     st.divider()

#     # ── KB stats ──
#     doc_count = get_doc_count()
#     st.markdown(
#         "<p style='color:#8b949e;font-size:0.78rem;font-weight:600;"
#         "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;'>Knowledge Base</p>",
#         unsafe_allow_html=True,
#     )
#     col1, col2 = st.columns(2)
#     col1.metric("Chunks", doc_count)
#     col2.metric("Queries", st.session_state.query_count)

#     st.divider()

#     # ── Document upload ──
#     st.markdown(
#         "<p style='color:#8b949e;font-size:0.78rem;font-weight:600;"
#         "letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;'>Upload Documents</p>",
#         unsafe_allow_html=True,
#     )
#     uploaded_files = st.file_uploader(
#         label="Upload",
#         type=["pdf", "txt", "md", "docx"],
#         accept_multiple_files=True,
#         label_visibility="collapsed",
#         help="PDF, TXT, Markdown, or Word documents",
#     )

#     if uploaded_files:
#         if st.button("📥 Ingest selected files", use_container_width=True):
#             st.session_state.ingest_msgs = []
#             with st.spinner("Embedding documents…"):
#                 for f in uploaded_files:
#                     ok, msg = ingest_file(f)
#                     st.session_state.ingest_msgs.append((ok, msg))
#             # Bust the vectorstore cache so the new count shows up
#             load_vectorstore.clear()
#             st.rerun()

#     # Show ingestion results
#     for ok, msg in st.session_state.ingest_msgs:
#         css = "ingest-ok" if ok else "ingest-err"
#         st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

#     st.divider()

#     if st.button("🗑️ Clear conversation", use_container_width=True):
#         st.session_state.messages    = []
#         st.session_state.total_steps = 0
#         st.session_state.query_count = 0
#         st.session_state.ingest_msgs = []
#         st.rerun()

#     st.markdown(
#         "<span style='font-size:0.73rem;color:#484f58;'>"
#         "ChromaDB: <code style='color:#3fb950'>./chroma_db</code><br>"
#         "Embed: <code style='color:#3fb950'>nomic-embed-text</code>"
#         "</span>",
#         unsafe_allow_html=True,
#     )


# # ──────────────────────────────────────────────
# # ── MAIN AREA ────────────────────────────────
# # ──────────────────────────────────────────────
# st.markdown(
#     "<h1 style='color:#e6edf3;font-weight:600;font-size:1.55rem;margin-bottom:4px;'>"
#     "Local Multi-Agent RAG"
#     "</h1>"
#     "<p style='color:#8b949e;font-size:0.87rem;margin-top:0;'>"
#     "Ask questions about your knowledge base. The agent will retrieve, reason, and respond."
#     "</p>",
#     unsafe_allow_html=True,
# )

# # Stats bar
# c1, c2, c3 = st.columns(3)
# c1.metric("Queries sent",   st.session_state.query_count)
# c2.metric("Total steps",    st.session_state.total_steps)
# c3.metric("KB chunks",      get_doc_count())

# st.divider()

# # ── Chat history ──
# chat_parts = []
# for msg in st.session_state.messages:
#     role    = msg["role"]
#     content = msg["content"].replace("\n", "<br>")
#     steps   = msg.get("steps")

#     if role == "user":
#         chat_parts.append(
#             f"<div class='chat-bubble chat-user'>"
#             f"<strong style='color:#388bfd;'>You</strong><br>{content}"
#             f"</div>"
#         )
#     elif role == "assistant":
#         badge = (
#             f"<br><span class='step-badge'>⚙ {steps} reasoning steps</span>"
#             if steps else ""
#         )
#         chat_parts.append(
#             f"<div class='chat-bubble chat-assistant'>"
#             f"<strong style='color:#3fb950;'>Agent</strong><br>{content}{badge}"
#             f"</div>"
#         )
#     elif role == "error":
#         chat_parts.append(
#             f"<div class='chat-bubble chat-error'>"
#             f"<strong>⚠ Error</strong><br>{content}"
#             f"</div>"
#         )

# if chat_parts:
#     st.markdown(
#         "<div style='max-height:58vh;overflow-y:auto;padding-right:4px;'>"
#         + "".join(chat_parts)
#         + "</div>",
#         unsafe_allow_html=True,
#     )
# else:
#     st.markdown(
#         "<div style='text-align:center;color:#484f58;padding:40px 0;font-size:0.87rem;'>"
#         "No conversation yet.<br>"
#         "Upload documents in the sidebar, then ask a question below."
#         "</div>",
#         unsafe_allow_html=True,
#     )


# # ── Input ──
# st.divider()

# with st.expander("💡 Example queries", expanded=False):
#     for q in [
#         "What are the main topics in my knowledge base?",
#         "Summarise the key points about [your topic]",
#         "Generate a quiz about [your topic]",
#         "Extract the key concepts from [your topic]",
#     ]:
#         st.markdown(
#             f"<span style='font-size:0.82rem;color:#8b949e;'>• {q}</span>",
#             unsafe_allow_html=True,
#         )

# query_input = st.text_area(
#     label="Your question",
#     placeholder="Ask anything about your knowledge base…",
#     height=88,
#     key="query_input",
#     label_visibility="collapsed",
# )

# col_btn, _ = st.columns([1, 5])
# with col_btn:
#     send_clicked = st.button("Send →", use_container_width=True)


# # ── Execute query ──
# if send_clicked and query_input.strip():
#     run_query = load_agent()

#     st.session_state.messages.append({"role": "user", "content": query_input.strip()})
#     st.session_state.query_count += 1

#     with st.spinner("Agent is thinking…"):
#         result = run_query(query_input.strip())

#     if result["success"]:
#         st.session_state.total_steps += result["steps"]
#         st.session_state.messages.append({
#             "role":    "assistant",
#             "content": result["answer"],
#             "steps":   result["steps"],
#         })
#     else:
#         st.session_state.messages.append({
#             "role":    "error",
#             "content": result["answer"],
#         })
#         with st.sidebar:
#             with st.expander("🔴 Error details", expanded=True):
#                 st.code(result["error"] or "Unknown error", language="text")

#     st.rerun()

# elif send_clicked and not query_input.strip():
#     st.warning("Please enter a question before sending.")























# from langchain_ollama import ChatOllama

# # Initialize our local LLM
# print("Connecting to Ollama...")
# llm = ChatOllama(model="llama3.2", temperature=0.2)

# # Test a simple single-shot call
# response = llm.invoke("Hello! Give me a 1-sentence response confirming you are online.")
# print("\nModel Response:")
# print(response.content)






# from core.agents import knowledge_agent
# from core.safe_runner import run_agent_safely

# def run_query(query: str) -> str:
#     messages = [
#         {
#             "role": "system",
#             "content": """You are an internship knowledge assistant. 
# Always retrieve relevant documents first, then summarize, quiz, or answer directly."""
#         },
#         {"role": "user", "content": query}
#     ]

#     response = run_agent_safely(knowledge_agent.invoke, messages, timeout_seconds=20)

#     if isinstance(response, str):
#         return response

#     if hasattr(response, "tool_calls") and response.tool_calls:
#         return f"Tool called: {response.tool_calls[0]['name']} with {response.tool_calls[0]['args']}"

#     return response.content






# from langchain_ollama import ChatOllama

# print("Connecting to Ollama...")

# # Initialize our local LLM
# llm = ChatOllama(model="llama3.2", temperature=0.2)

# # Test a simple single-shot call
# print("Sending test prompt to llama3.2...")
# response = llm.invoke("Hello! Give me a 1-sentence response confirming you are online.")

# print("\nModel Response:")
# print(response.content)








# from langchain_ollama import ChatOllama
# from langchain_core.tools import tool

# # 1. Define a tool using a plain Python function and a decorator
# @tool
# def multiply(a: int, b: int) -> int:
#     """Multiplies two numbers together. Use this whenever you need to do math multiplication."""
#     return a * b

# print("Connecting to Ollama...")
# llm = ChatOllama(model="llama3.2", temperature=0.0)

# # 2. Natively bind the tool directly to the model
# llm_with_tools = llm.bind_tools([multiply])

# print("Sending a math prompt to the AI...")
# response = llm_with_tools.invoke("What is 6 multiplied by 7?")

# # 3. Check if the AI decided to call the tool
# print("\n--- Results ---")
# print("AI's text response:", response.content)
# print("AI's tool calls decision:", response.tool_calls)









from langchain_ollama import ChatOllama
from langchain_core.tools import tool

# 1. Define the tool
@tool
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers together. Use this whenever you need to do math multiplication."""
    return a * b

print("Connecting to Ollama...")
llm = ChatOllama(model="llama3.2", temperature=0.0)
llm_with_tools = llm.bind_tools([multiply])

# We keep track of the conversation using a list of messages
user_query = "What is 6 multiplied by 7?"
messages = [{"role": "user", "content": user_query}]

print(f"Sending prompt: '{user_query}'")
response = llm_with_tools.invoke(messages)

# Check if the AI wants to call a tool
if response.tool_calls:
    tool_call = response.tool_calls[0]
    print(f"\nAI selected tool: {tool_call['name']} with args {tool_call['args']}")
    
    # Execute the actual Python function using the arguments provided by the AI
    # (Converting string arguments to integers just in case)
    tool_result = multiply.invoke(tool_call['args'])
    print(f"Python function executed. Result = {tool_result}")
    
    # Append the AI's tool call request and the tool's actual result to the history
    messages.append(response)
    messages.append({"role": "tool", "content": str(tool_result), "tool_call_id": tool_call['id']})
    
    # Call the LLM one last time with the complete history so it can formulate the final answer
    print("Asking AI to summarize the final answer...")
    final_response = llm_with_tools.invoke(messages)
    
    print("\n--- Final AI Response ---")
    print(final_response.content)
else:
    print("\n--- Final AI Response (No tools needed) ---")
    print(response.content)