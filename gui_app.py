# import re
# import os
# import sys
# import time
# import shutil
# import tempfile
# import requests
# import urllib.parse
# import streamlit as st
# from langchain_ollama import ChatOllama
# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# # ── PATH FIX ─────────────────────────────────────────────────────────────────
# PROJECT_ROOT = r"C:\Users\Ranvijay Singh\OneDrive\Dokumen\ollama"
# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)

# # We bypass retrieve_documents completely now to prevent WinError 32
# from core.tools import summarize_text, generate_quiz, extract_key_points

# # ─────────────────────────────────────────────────────────────────────────────
# # 1. PAGE CONFIG & PREMIUM UI STYLING
# # ─────────────────────────────────────────────────────────────────────────────
# st.set_page_config(page_title="Nexus AI Workspace", page_icon="🧠", layout="wide")

# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
#     html, body, [data-testid="stSidebar"] {
#         font-family: 'Inter', sans-serif;
#     }
#     .stChatInput { 
#         position: sticky; 
#         bottom: 0; 
#         z-index: 100; 
#         padding-top: 10px;
#         background-color: transparent;
#     }
#     [data-testid="stChatMessage"] { 
#         border-radius: 16px !important; 
#         margin-bottom: 12px !important;
#         padding: 14px 18px !important;
#         border: 1px solid rgba(128, 128, 128, 0.1) !important;
#         box-shadow: 0 2px 6px rgba(0,0,0,0.02) !important;
#     }
#     [data-testid="stChatMessageUser"] {
#         background-color: rgba(43, 108, 176, 0.08) !important;
#         border-left: 4px solid #2b6cb0 !important;
#     }
#     [data-testid="stChatMessageAssistant"] {
#         background-color: rgba(128, 128, 128, 0.04) !important;
#         border-left: 4px solid #4a5568 !important;
#     }
#     .doc-card {
#         background-color: rgba(128, 128, 128, 0.05);
#         border: 1px solid rgba(128, 128, 128, 0.15);
#         padding: 10px 14px;
#         border-radius: 8px;
#         margin-bottom: 6px;
#         font-size: 0.85rem;
#         display: flex;
#         align-items: center;
#         gap: 8px;
#     }
#     .system-status {
#         font-family: monospace;
#         color: #718096 !important;
#         font-size: 0.8rem !important;
#         border-left: 2px solid #cbd5e0;
#         padding-left: 8px;
#         margin: 6px 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ─────────────────────────────────────────────────────────────────────────────
# # 2. LLM INIT
# # ─────────────────────────────────────────────────────────────────────────────
# @st.cache_resource
# def init_chat_llm():
#     return ChatOllama(model="llama3.2", temperature=0.3)

# chat_llm = init_chat_llm()

# SYSTEM_PROMPT = SystemMessage(content="""You are a friendly, knowledgeable AI assistant.
# - Answer factual, general-knowledge, and conversational questions directly and helpfully.
# - For maths, show the working steps clearly, then state the final answer.
# - Format all responses in clean markdown with headings and bullet points where helpful.
# - Never output raw JSON, tool call syntax, or function names in your replies.
# - If asked about any person, place, event, or concept, answer confidently from your training knowledge.""")

# def build_lc_messages():
#     msgs = [SYSTEM_PROMPT]
#     for m in st.session_state.chat_history:
#         msgs.append(HumanMessage(content=m["content"]) if m["role"] == "user" 
#                     else AIMessage(content=m["content"]))
#     return msgs

# # ─────────────────────────────────────────────────────────────────────────────
# # 3. VECTOR INDEX BUILDER (TIMESTAMP BASED SYSTEM)
# # ─────────────────────────────────────────────────────────────────────────────
# CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

# def build_vector_index(uploaded_file_objects: list) -> tuple:
#     try:
#         from langchain_community.document_loaders import PyPDFLoader, TextLoader
#         from langchain_text_splitters import RecursiveCharacterTextSplitter
#         from langchain_chroma import Chroma
#         from langchain_ollama import OllamaEmbeddings

#         docs = []
#         for uf in uploaded_file_objects:
#             suffix = ".pdf" if uf.name.lower().endswith(".pdf") else ".txt"
#             with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#                 tmp.write(uf.read())
#                 tmp_path = tmp.name
#             try:
#                 loader = PyPDFLoader(tmp_path) if suffix == ".pdf" else TextLoader(tmp_path)
#                 loaded = loader.load()
#                 for doc in loaded:
#                     doc.metadata["source_file"] = uf.name
#                 docs.extend(loaded)
#             finally:
#                 os.unlink(tmp_path)

#         if not docs:
#             return "⚠️ No readable content found in the uploaded files.", None

#         splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
#         chunks = splitter.split_documents(docs)

#         # Generate unique collection ID to eliminate Windows lock errors
#         collection_name = f"docs_{int(time.time())}"

#         embeddings = OllamaEmbeddings(model="nomic-embed-text")
#         Chroma.from_documents(
#             documents=chunks,
#             embedding=embeddings,
#             persist_directory=CHROMA_PATH,
#             collection_name=collection_name,
#         )
#         return f"✨ Engine Ready: Indexed {len(uploaded_file_objects)} file(s) into {len(chunks)} components.", collection_name
        
#     except Exception as e:
#         return f"⚠️ Indexing anomaly: {e}", None

# # ─────────────────────────────────────────────────────────────────────────────
# # 4. ACTIVE COLLECTION RETRIEVER
# # ─────────────────────────────────────────────────────────────────────────────
# def query_active_collection(query: str, collection_name: str) -> str:
#     try:
#         from langchain_chroma import Chroma
#         from langchain_ollama import OllamaEmbeddings

#         embeddings = OllamaEmbeddings(model="nomic-embed-text")
#         vectorstore = Chroma(
#             persist_directory=CHROMA_PATH,
#             embedding_function=embeddings,
#             collection_name=collection_name,
#         )
#         results = vectorstore.similarity_search(query, k=6)
#         if not results:
#             return ""
#         return "\n\n".join(doc.page_content for doc in results)
#     except Exception as e:
#         return f"failed: {e}"

# # ─────────────────────────────────────────────────────────────────────────────
# # 5. WEATHER ENGINE
# # ─────────────────────────────────────────────────────────────────────────────
# WMO_CODES = {
#     0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
#     45: "Fog 🌫️", 48: "Icy fog 🌫️", 51: "Light drizzle 🌦️", 53: "Moderate drizzle 🌦️",
#     55: "Dense drizzle 🌧️", 61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
#     71: "Slight snow 🌨️", 73: "Moderate snow 🌨️", 75: "Heavy snow ❄️",
#     80: "Rain showers 🌦️", 81: "Moderate showers 🌧️", 82: "Violent showers ⛈️",
#     95: "Thunderstorm ⛈️", 96: "Thunderstorm with hail ⛈️",
# }

# def _wind_label(deg: float) -> str:
#     return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][round(deg / 45) % 8]

# def _llm_correct_city(raw: str) -> str:
#     try:
#         prompt = (f"The user typed this city name (possibly misspelled): '{raw}'.\n"
#                   "Return ONLY the correctly spelled English city name, nothing else.\n"
#                   "For Indian cities include state if helpful (e.g. 'Faridkot, Punjab').\n"
#                   "Just the name — no explanation, no punctuation, no extra words.")
#         resp = chat_llm.invoke([HumanMessage(content=prompt)])
#         fixed = resp.content.strip().strip("'\"")
#         return " ".join(fixed.split()[:4]) if len(fixed.split()) > 4 else fixed or raw
#     except Exception:
#         return raw

# def _geocode(city: str):
#     url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
#     resp = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
#     if resp.status_code == 200:
#         results = resp.json().get("results", [])
#         if results:
#             r = results[0]
#             return r["latitude"], r["longitude"], r.get("name", city), r.get("country", "")
#     return None, None, city, ""

# def _open_meteo_weather(lat, lon):
#     url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
#            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
#            f"weather_code,wind_speed_10m,wind_direction_10m"
#            f"&daily=temperature_2m_max,temperature_2m_min"
#            f"&forecast_days=1&timezone=auto")
#     resp = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
#     resp.raise_for_status()
#     return resp.json()

# def get_weather(raw_city: str) -> str:
#     corrected = _llm_correct_city(raw_city)
#     try:
#         lat, lon, name, country = _geocode(corrected)
#         if lat is not None:
#             d = _open_meteo_weather(lat, lon)
#             cur = d["current"]; dy = d["daily"]
#             loc = f"{name}, {country}" if country else name
#             return (
#                 f"### 🌤️ Weather Matrix for {loc}\n\n"
#                 f"| Metric | Current Metric Reading |\n|---|---|\n"
#                 f"| 🌡️ Temperature | **{cur['temperature_2m']} °C** (Feels like {cur['apparent_temperature']} °C) |\n"
#                 f"| 🌤️ Current Condition | {WMO_CODES.get(cur['weather_code'], str(cur['weather_code']))} |\n"
#                 f"| 💧 Humidity Index | {cur['relative_humidity_2m']}% |\n"
#                 f"| 🌬️ Wind Activity | {cur['wind_speed_10m']} km/h Vector {_wind_label(cur['wind_direction_10m'])} |\n"
#                 f"| 🔼 High / 🔽 Low | {dy['temperature_2m_max'][0]} °C / {dy['temperature_2m_min'][0]} °C |\n\n"
#                 f"*Data Stream Engine · Open-Meteo API Verification*"
#             )
#     except Exception:
#         pass
#     try:
#         encoded = urllib.parse.quote(corrected)
#         r = requests.get(f"https://wttr.in/{encoded}?format=j1", timeout=7, headers={"User-Agent": "curl/7.68.0"})
#         r.raise_for_status()
#         d = r.json(); cur = d["current_condition"][0]; td = d["weather"][0]
#         return (
#             f"### 🌤️ Weather Matrix for {corrected}\n\n"
#             f"| Metric | Current Metric Reading |\n|---|---|\n"
#             f"| 🌡️ Temperature | **{cur['temp_C']} °C** (Feels like {cur['FeelsLikeC']} °C) |\n"
#             f"| 🌤️ Condition Status | {cur['weatherDesc'][0]['value']} |\n"
#             f"| 💧 Humidity Index | {cur['humidity']}% |\n"
#             f"| 🌬️ Wind Velocity | {cur['windspeedKmph']} km/h |\n"
#             f"| 🔼 High / 🔽 Low | {td['maxtempC']} °C / {td['mintempC']} °C |\n\n"
#             f"*Fallback Stream Engine · wttr.in Verification*"
#         )
#     except Exception as e:
#         return f"⚠️ **Unable to parse dynamic atmospheric telemetry for '{raw_city}'**"

# # ─────────────────────────────────────────────────────────────────────────────
# # 6. SESSION STATE
# # ─────────────────────────────────────────────────────────────────────────────
# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []
# if "indexed_filenames" not in st.session_state:
#     st.session_state.indexed_filenames = set()
# if "active_collection" not in st.session_state:
#     st.session_state.active_collection = None
# if "index_status" not in st.session_state:
#     st.session_state.index_status = ""

# # ─────────────────────────────────────────────────────────────────────────────
# # 7. SIDEBAR DESIGN
# # ─────────────────────────────────────────────────────────────────────────────
# with st.sidebar:
#     st.markdown("<h2 style='font-weight:700; color:#2b6cb0; margin-bottom:4px;'>📁 Data Repository</h2>", unsafe_allow_html=True)
#     st.markdown("<p style='font-size:0.85rem; color:#718096; margin-top:0px;'>Upload context files to bind to the AI workspace core.</p>", unsafe_allow_html=True)
    
#     uploaded_files = st.file_uploader(
#         "Supported extensions: PDF, TXT",
#         type=["pdf", "txt"],
#         accept_multiple_files=True,
#         key="file_uploader",
#         label_visibility="collapsed"
#     )
    
#     if uploaded_files:
#         current_names = {f.name for f in uploaded_files}
#         if current_names != st.session_state.indexed_filenames:
#             with st.spinner("Analyzing and parsing document matrix..."):
#                 status, collection_name = build_vector_index(uploaded_files)
#                 if collection_name:
#                     st.session_state.active_collection = collection_name
#                 st.session_state.indexed_filenames = current_names
#                 st.session_state.index_status = status
        
#         st.markdown("<div style='margin-top:10px; font-weight:600; font-size:0.85rem; color:#2d3748;'>Active Data Sources:</div>", unsafe_allow_html=True)
#         for name in current_names:
#             st.markdown(f"<div class='doc-card'>📄 {name}</div>", unsafe_allow_html=True)
        
#         if st.session_state.index_status:
#             st.markdown(f"<p style='font-size:0.75rem; color:#38a169; margin-top:4px;'>{st.session_state.index_status}</p>", unsafe_allow_html=True)
#     else:
#         if st.session_state.indexed_filenames:
#             st.session_state.indexed_filenames = set()
#             st.session_state.active_collection = None
#             st.session_state.index_status = ""
    
#     st.markdown("<br><br>", unsafe_allow_html=True)
#     st.markdown("<div style='font-weight:600; font-size:0.8rem; letter-spacing:0.5px; color:#a0aec0; text-transform:uppercase;'>System Diagnostics</div>", unsafe_allow_html=True)
#     st.caption("⚡ Model Engine: `llama3.2`")
#     st.caption("📡 Telemetry Layer: `Open-Meteo`")
#     st.caption("🗄️ Database Vector: `Chroma DB (Isolated)`")
    
#     st.markdown("<div style='position: fixed; bottom: 20px; width: 260px;'>", unsafe_allow_html=True)
#     if st.button("🗑️ Reset Application History", use_container_width=True):
#         st.session_state.chat_history = []
#         st.rerun()
#     st.markdown("</div>", unsafe_allow_html=True)

# # ─────────────────────────────────────────────────────────────────────────────
# # 8. MAIN PLATFORM HEADER
# # ─────────────────────────────────────────────────────────────────────────────
# st.markdown("<h1 style='font-weight:700; letter-spacing:-0.5px; margin-bottom:0px;'>🧠 Nexus Workspace</h1>", unsafe_allow_html=True)
# st.markdown("<p style='color:#4a5568; font-size:1.1rem; margin-top:4px;'>Advanced Multi-Agent Knowledge Engine & Dynamic Tool Suite.</p>", unsafe_allow_html=True)
# st.markdown("---")

# # ─────────────────────────────────────────────────────────────────────────────
# # 9. INTENT CLASSIFIER LOGIC
# # ─────────────────────────────────────────────────────────────────────────────
# _MATH_RE = re.compile(r"^[\d\s\+\-\*/\^\(\)\.%,=]+$")
# GREETING_EXACT = {"hi", "hello", "hey", "sup", "howdy", "hiya", "yo", "good morning", "good evening", "good night", "good afternoon", "what's up", "whats up", "bye", "goodbye", "see you", "take care", "thanks", "thank you", "thx", "ty", "help", "who are you", "what can you do"}
# WEATHER_TRIGGER = {"weather", "temperature", "temp", "forecast", "climate", "degrees", "celsius", "fahrenheit", "raining", "sunny", "humid"}
# SUMMARIZE_TRIGGER = {"summarize", "summary", "summarise", "overview", "brief", "tldr", "tl;dr", "condense", "shorten"}
# QUIZ_TRIGGER = {"quiz", "mcq", "questionnaire", "test me", "evaluate", "assess"}
# KEYPOINTS_TRIGGER = {"key points", "keypoints", "highlights", "takeaways", "key takeaways", "main points", "important points", "key findings"}
# DOC_TRIGGER = {"document", "pdf", "file", "uploaded", "explain this", "what does it say", "what is it about", "what is this about", "tell me about", "describe this", "content of", "topic of", "this doc", "the file", "the document", "the pdf", "in the doc", "in the file", "from the document", "what is this", "what are", "explain the", "about the", "slides", "lecture", "notes", "spectroscopy", "uv-visible", "uv", "visible", "light", "absorption"}
# NEW_DOC_PHRASES = {"new document", "new file", "new pdf", "another document", "uploaded new", "just uploaded", "i uploaded", "i have uploaded", "added a new", "another file"}

# def _has(text, ws): return any(w in text for w in ws)

# def extract_city(text: str) -> str:
#     for prep in ["in ", "of ", "for ", "at ", "about "]:
#         if prep in text:
#             after = text.split(prep, 1)[-1].strip()
#             cand = " ".join(after.split()[:2]).strip("?.!,")
#             if cand and len(cand) > 1: return cand
#     words = text.split()
#     return words[-1].strip("?.!,") if words else "unknown"

# def classify_intent(text: str):
#     t = text.strip().lower()
#     if _MATH_RE.fullmatch(t): return "math", None
#     if t in GREETING_EXACT: return "greeting", None
#     for gw in GREETING_EXACT:
#         if t.startswith(gw) and len(t) <= len(gw) + 12: return "greeting", None
#     if _has(t, NEW_DOC_PHRASES): return "new_doc", None
#     if _has(t, WEATHER_TRIGGER): return "weather", extract_city(t)
#     if _has(t, SUMMARIZE_TRIGGER): return "summarize", None
#     has_doc = _has(t, DOC_TRIGGER) or bool(st.session_state.active_collection)
#     if _has(t, QUIZ_TRIGGER) and has_doc: return "quiz", None
#     if _has(t, KEYPOINTS_TRIGGER) and has_doc: return "key_points", None
#     if has_doc and _has(t, DOC_TRIGGER): return "retrieve", None
#     return "chat", None

# def bullets_to_markdown(text: str) -> str:
#     if not text or "•" not in text: return text or ""
#     return "\n".join(f"- {p.strip()}" for p in text.split("•") if p.strip())

# # ─────────────────────────────────────────────────────────────────────────────
# # 10. DOCUMENT TOOL RUNNER (FIXED FOR WINDOWS BIN LOCKS)
# # ─────────────────────────────────────────────────────────────────────────────
# def run_doc_tool(intent: str, user_input: str) -> str:
#     collection = st.session_state.active_collection
#     if not collection:
#         return "⚠️ **Workspace Restriction:** No contextual documents are currently attached to the active database partition. Please upload a file via the repository side-panel to proceed."

#     st.markdown("<div class='system-status'>[SYSTEM LOG]: Retrieving operational vector fragments from active timestamp collection...</div>", unsafe_allow_html=True)
    
#     # CRITICAL FIX: Direct query to active timestamp collection to prevent pulling stale data
#     context = query_active_collection(user_input, collection)
    
#     if not context or len(context.strip()) < 20 or "failed" in context.lower():
#         return "⚠️ **Analysis Interrupted:** The retrieval model completed the scanning operation but found no relevant data overlaps inside the vector store. Rephrase your request or attach a contextually specific file."

#     if intent == "summarize":
#         st.markdown("<div class='system-status'>[SYSTEM LOG]: Mapping lexical dimensions and compressing document weight...</div>", unsafe_allow_html=True)
#         return f"### 📋 Executive Document Summary\n\n{bullets_to_markdown(summarize_text.invoke({'text': context}))}"
#     elif intent == "quiz":
#         st.markdown("<div class='system-status'>[SYSTEM LOG]: Executing evaluation synthesis protocols...</div>", unsafe_allow_html=True)
#         return f"### 🧪 Context Assessment Evaluation\n\n{generate_quiz.invoke({'text': context})}"
#     elif intent == "key_points":
#         st.markdown("<div class='system-status'>[SYSTEM LOG]: Segregating key thematic milestones...</div>", unsafe_allow_html=True)
#         return f"### 🔑 Critical Workspace Milestones\n\n{bullets_to_markdown(extract_key_points.invoke({'text': context}))}"
#     else:
#         return f"### 📄 Isolated Workspace Segment\n\n{bullets_to_markdown(context)}"

# # ─────────────────────────────────────────────────────────────────────────────
# # 11. RENDER ACTIVE DIALOGUE
# # ─────────────────────────────────────────────────────────────────────────────
# for msg in st.session_state.chat_history:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # ─────────────────────────────────────────────────────────────────────────────
# # 12. STREAMLIT CHAT WORKFLOW LOOP
# # ─────────────────────────────────────────────────────────────────────────────
# if user_input := st.chat_input("Query documents, fetch weather tracking metrics, solve equations..."):
    
#     with st.chat_message("user"):
#         st.markdown(user_input)
#     st.session_state.chat_history.append({"role": "user", "content": user_input})
    
#     with st.chat_message("assistant"):
#         with st.spinner("Processing workspace instructions..."):
#             final_text = ""
#             try:
#                 intent, extra = classify_intent(user_input)
                
#                 if intent in ("math", "greeting", "chat"):
#                     final_text = chat_llm.invoke(build_lc_messages()).content
                
#                 elif intent == "new_doc":
#                     if st.session_state.indexed_filenames:
#                         names = ", ".join(st.session_state.indexed_filenames)
#                         final_text = f"✅ **Sync Complete:** Core memory matrix has locked onto active records: **{names}**. State your next directive (e.g., summarize, extract milestones)."
#                     else:
#                         final_text = "The active database index remains clear. Load an uncorrupted PDF/TXT target file into the left repository tray to begin."
                
#                 elif intent == "weather":
#                     raw_city = extra or "unknown"
#                     st.markdown(f"<div class='system-status'>[SYSTEM LOG]: Resolving geographic spelling indices for '{raw_city}'...</div>", unsafe_allow_html=True)
#                     final_text = get_weather(raw_city)
                
#                 elif intent in ("summarize", "quiz", "key_points", "retrieve"):
#                     final_text = run_doc_tool(intent, user_input)
                
#                 else:
#                     final_text = chat_llm.invoke(build_lc_messages()).content
                    
#             except Exception as exc:
#                 final_text = f"❌ **Hardware Pipeline Interruption:**\n\n```\n{exc}\n```\n\nEnsure local Ollama instance orchestrations are sound."
            
#             st.markdown(final_text)
#             st.session_state.chat_history.append({"role": "assistant", "content": final_text})

import re
import os
import sys
import time
import tempfile
import requests
import urllib.parse
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Expert AI Assistant", page_icon="🧠", layout="wide")
st.markdown("""
<style>
.stChatInput { position: sticky; bottom: 0; z-index: 100; }
[data-testid="stChatMessage"] { border-radius: 12px; padding: 4px 8px; }
.element-container small { color: #888 !important; font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. ENVIRONMENT DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def _ollama_is_running() -> bool:
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

USE_OLLAMA = _ollama_is_running()

# ─────────────────────────────────────────────────────────────────────────────
# 3. LLM + EMBEDDINGS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def init_llm():
    if USE_OLLAMA:
        from langchain_ollama import ChatOllama
        return ChatOllama(model="llama3.2", temperature=0.3)
    else:
        from langchain_groq import ChatGroq
        groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
        if not groq_key:
            st.error("⚠️ No GROQ_API_KEY found. Add it in Streamlit Cloud → Settings → Secrets.")
            st.stop()
        # llama-3.1-8b-instant is the current free fast model on Groq
        return ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key, temperature=0.3)

@st.cache_resource
def init_embeddings():
    if USE_OLLAMA:
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text")
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

chat_llm   = init_llm()
embeddings = init_embeddings()

SYSTEM_PROMPT = SystemMessage(content="""You are a friendly, knowledgeable AI assistant.
- Answer factual, general-knowledge, and conversational questions directly.
- For maths, show working steps clearly then state the final answer.
- Format responses in clean markdown with headings and bullet points where helpful.
- Never output raw JSON, tool call syntax, or function names.
- Answer confidently about any person, place, event, or concept from your knowledge.""")

def build_lc_messages():
    msgs = [SYSTEM_PROMPT]
    for m in st.session_state.chat_history:
        msgs.append(HumanMessage(content=m["content"]) if m["role"] == "user"
                    else AIMessage(content=m["content"]))
    return msgs

# ─────────────────────────────────────────────────────────────────────────────
# 4. CLOUD-NATIVE DOCUMENT TOOLS
#    These call chat_llm directly — no Ollama dependency at all.
#    Used on cloud instead of core/tools.py which is hardcoded to localhost.
# ─────────────────────────────────────────────────────────────────────────────
def cloud_summarize(text: str) -> str:
    resp = chat_llm.invoke([HumanMessage(content=(
        "Summarize the following document clearly in markdown with headings and bullet points.\n"
        "Be thorough — cover all key topics, concepts, and details.\n\n"
        f"{text}"
    ))])
    return resp.content

def cloud_quiz(text: str) -> str:
    resp = chat_llm.invoke([HumanMessage(content=(
        "Create 5 multiple choice questions (A/B/C/D) based on this content.\n"
        "For each question, clearly mark the correct answer at the end.\n\n"
        f"{text}"
    ))])
    return resp.content

def cloud_key_points(text: str) -> str:
    resp = chat_llm.invoke([HumanMessage(content=(
        "Extract the key points from the following content.\n"
        "Format as a clean markdown bullet list with bold headings for each category.\n\n"
        f"{text}"
    ))])
    return resp.content

def cloud_answer(text: str, question: str) -> str:
    resp = chat_llm.invoke([HumanMessage(content=(
        f"Using the following document content, answer this question: {question}\n\n"
        f"Document content:\n{text}"
    ))])
    return resp.content

# ─────────────────────────────────────────────────────────────────────────────
# 5. CHROMA PATH
# ─────────────────────────────────────────────────────────────────────────────
if USE_OLLAMA:
    PROJECT_ROOT = r"C:\Users\Ranvijay Singh\OneDrive\Dokumen\ollama"
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    CHROMA_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
else:
    CHROMA_PATH = os.path.join(tempfile.gettempdir(), "ai_assistant_chroma")

# ─────────────────────────────────────────────────────────────────────────────
# 6. VECTOR INDEX BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_vector_index(uploaded_file_objects: list) -> tuple:
    try:
        from langchain_community.document_loaders import PyPDFLoader, TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma

        docs = []
        for uf in uploaded_file_objects:
            suffix = ".pdf" if uf.name.lower().endswith(".pdf") else ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uf.read())
                tmp_path = tmp.name
            try:
                loader = PyPDFLoader(tmp_path) if suffix == ".pdf" else TextLoader(tmp_path)
                loaded = loader.load()
                for doc in loaded:
                    doc.metadata["source_file"] = uf.name
                docs.extend(loaded)
            finally:
                os.unlink(tmp_path)

        if not docs:
            return "⚠️ No readable content found in the uploaded files.", None

        splitter        = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks          = splitter.split_documents(docs)
        collection_name = f"docs_{int(time.time())}"

        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH,
            collection_name=collection_name,
        )
        return (f"✅ {len(uploaded_file_objects)} file(s) indexed — {len(chunks)} chunks stored.",
                collection_name)

    except Exception as e:
        return f"⚠️ Indexing failed: {e}", None

# ─────────────────────────────────────────────────────────────────────────────
# 7. RETRIEVER
# ─────────────────────────────────────────────────────────────────────────────
def query_active_collection(query: str, collection_name: str) -> str:
    try:
        from langchain_chroma import Chroma
        vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings,
            collection_name=collection_name,
        )
        results = vectorstore.similarity_search(query, k=8)
        return "\n\n".join(doc.page_content for doc in results) if results else ""
    except Exception as e:
        return f"failed: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# 8. WEATHER
# ─────────────────────────────────────────────────────────────────────────────
WMO_CODES = {
    0:"Clear sky ☀️", 1:"Mainly clear 🌤️", 2:"Partly cloudy ⛅", 3:"Overcast ☁️",
    45:"Fog 🌫️", 48:"Icy fog 🌫️", 51:"Light drizzle 🌦️", 53:"Moderate drizzle 🌦️",
    55:"Dense drizzle 🌧️", 61:"Slight rain 🌧️", 63:"Moderate rain 🌧️", 65:"Heavy rain 🌧️",
    71:"Slight snow 🌨️", 73:"Moderate snow 🌨️", 75:"Heavy snow ❄️",
    80:"Rain showers 🌦️", 81:"Moderate showers 🌧️", 82:"Violent showers ⛈️",
    95:"Thunderstorm ⛈️", 96:"Thunderstorm with hail ⛈️",
}
def _wind_label(deg): return ["N","NE","E","SE","S","SW","W","NW"][round(deg/45)%8]

def _llm_correct_city(raw):
    try:
        resp = chat_llm.invoke([HumanMessage(content=(
            f"The user typed this city name (possibly misspelled): '{raw}'.\n"
            "Return ONLY the correctly spelled English city name, nothing else.\n"
            "For Indian cities include state e.g. 'Faridkot, Punjab'.\n"
            "Just the name — no explanation, no extra words."))])
        fixed = resp.content.strip().strip("'\"")
        return " ".join(fixed.split()[:4]) if len(fixed.split()) > 4 else fixed or raw
    except Exception:
        return raw

def _geocode(city):
    url  = (f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={urllib.parse.quote(city)}&count=1&language=en&format=json")
    resp = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            r = results[0]
            return r["latitude"], r["longitude"], r.get("name", city), r.get("country","")
    return None, None, city, ""

def get_weather(raw_city):
    corrected = _llm_correct_city(raw_city)
    try:
        lat, lon, name, country = _geocode(corrected)
        if lat is not None:
            url = (f"https://api.open-meteo.com/v1/forecast"
                   f"?latitude={lat}&longitude={lon}"
                   f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                   f"weather_code,wind_speed_10m,wind_direction_10m"
                   f"&daily=temperature_2m_max,temperature_2m_min"
                   f"&forecast_days=1&timezone=auto")
            d   = requests.get(url, timeout=7, headers={"User-Agent": "Mozilla/5.0"}).json()
            c   = d["current"]; dy = d["daily"]
            loc = f"{name}, {country}" if country else name
            return (
                f"**📍 {loc}**\n\n"
                f"| Detail | Value |\n|---|---|\n"
                f"| 🌡️ Temperature | **{c['temperature_2m']} °C** (feels like {c['apparent_temperature']} °C) |\n"
                f"| 🌤️ Condition | {WMO_CODES.get(c['weather_code'], '—')} |\n"
                f"| 💧 Humidity | {c['relative_humidity_2m']}% |\n"
                f"| 🌬️ Wind | {c['wind_speed_10m']} km/h {_wind_label(c['wind_direction_10m'])} |\n"
                f"| 🔼 High / 🔽 Low | {dy['temperature_2m_max'][0]} °C / {dy['temperature_2m_min'][0]} °C |\n\n"
                f"*Live data · Open-Meteo · {name}*"
            )
    except Exception:
        pass
    return (f"⚠️ Could not fetch weather for **'{raw_city}'**.\n"
            "Please check your internet connection.")

# ─────────────────────────────────────────────────────────────────────────────
# 9. SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [("chat_history", []), ("indexed_filenames", set()),
                     ("active_collection", None), ("index_status", "")]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# 10. SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📁 Document Management")
    uploaded_files = st.file_uploader(
        "Upload PDFs / Text files:",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="file_uploader",
    )

    if uploaded_files:
        current_names = {f.name for f in uploaded_files}
        if current_names != st.session_state.indexed_filenames:
            with st.spinner(f"Indexing {len(uploaded_files)} file(s)…"):
                status, col = build_vector_index(uploaded_files)
                if col:
                    st.session_state.active_collection = col
                st.session_state.indexed_filenames = current_names
                st.session_state.index_status      = status

        st.success(f"📄 {len(current_names)} file(s) active")
        if st.session_state.index_status:
            st.caption(st.session_state.index_status)
        for f in uploaded_files:
            st.caption(f"📎 {f.name}")
    else:
        if st.session_state.indexed_filenames:
            st.session_state.indexed_filenames = set()
            st.session_state.active_collection = None
            st.session_state.index_status      = ""

    st.divider()
    mode = "🖥️ Local (Ollama)" if USE_OLLAMA else "☁️ Cloud (Groq)"
    st.caption(f"**Runtime:** {mode}")
    st.caption("🌤️ Weather → Open-Meteo (live, free)")
    st.caption("📖 Docs → Chroma RAG")

    if st.button("🗑️ Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 11. PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.title("🧠 Expert AI Knowledge & Weather Assistant")
st.write("Upload PDFs or text files — ask anything about them, check live weather, or just chat!")

# ─────────────────────────────────────────────────────────────────────────────
# 12. INTENT CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────
_MATH_RE = re.compile(r"^[\d\s\+\-\*/\^\(\)\.%,=]+$")
GREETING_EXACT    = {"hi","hello","hey","sup","howdy","hiya","yo","good morning",
                     "good evening","good night","good afternoon","what's up","whats up",
                     "bye","goodbye","see you","take care","thanks","thank you","thx","ty",
                     "help","who are you","what can you do"}
WEATHER_TRIGGER   = {"weather","temperature","temp","forecast","climate",
                     "degrees","celsius","fahrenheit","raining","sunny","humid"}
SUMMARIZE_TRIGGER = {"summarize","summary","summarise","overview","brief","tldr","tl;dr","condense"}
QUIZ_TRIGGER      = {"quiz","mcq","questionnaire","test me","evaluate","assess"}
KEYPOINTS_TRIGGER = {"key points","keypoints","highlights","takeaways","key takeaways",
                     "main points","important points","key findings"}
DOC_TRIGGER       = {"document","pdf","file","uploaded","explain this","what does it say",
                     "what is it about","what is this about","tell me about","describe this",
                     "this doc","the file","the document","the pdf","slides","lecture","notes",
                     "polymer","chemistry","material","chapter","subject","course","unit",
                     "what are","explain the","about the","from the","content","fluid",
                     "dynamics","physics","theory","concept","define","definition"}
NEW_DOC_PHRASES   = {"new document","new file","new pdf","another document","uploaded new",
                     "just uploaded","i uploaded","i have uploaded","added a new","another file"}

def _has(text, ws): return any(w in text for w in ws)

def extract_city(text):
    for prep in ["in ","of ","for ","at ","about "]:
        if prep in text:
            after = text.split(prep,1)[-1].strip()
            cand  = " ".join(after.split()[:2]).strip("?.!,")
            if cand and len(cand) > 1: return cand
    words = text.split()
    return words[-1].strip("?.!,") if words else "unknown"

def classify_intent(text):
    t = text.strip().lower()
    if _MATH_RE.fullmatch(t):                                   return "math",       None
    if t in GREETING_EXACT:                                     return "greeting",   None
    for gw in GREETING_EXACT:
        if t.startswith(gw) and len(t) <= len(gw)+12:          return "greeting",   None
    if _has(t, NEW_DOC_PHRASES):                                return "new_doc",    None
    if _has(t, WEATHER_TRIGGER):                                return "weather",    extract_city(t)
    if _has(t, SUMMARIZE_TRIGGER):                              return "summarize",  None
    has_doc = _has(t, DOC_TRIGGER) or bool(st.session_state.active_collection)
    if _has(t, QUIZ_TRIGGER):                                   return "quiz",       None
    if _has(t, KEYPOINTS_TRIGGER):                              return "key_points", None
    if has_doc and _has(t, DOC_TRIGGER):                        return "retrieve",   None
    return "chat", None

def bullets_to_markdown(text):
    if not text or "•" not in text: return text or ""
    return "\n".join(f"- {p.strip()}" for p in text.split("•") if p.strip())

# ─────────────────────────────────────────────────────────────────────────────
# 13. DOCUMENT TOOL RUNNER — 100% cloud-native, no Ollama calls
# ─────────────────────────────────────────────────────────────────────────────
def run_doc_tool(intent, user_input):
    collection = st.session_state.active_collection
    if not collection:
        return ("⚠️ **No documents indexed yet.**\n\n"
                "Please upload a PDF or text file using the sidebar first.")

    st.caption("📂 *Fetching chunks from Chroma DB…*")
    context = query_active_collection(user_input, collection)

    if not context or len(context.strip()) < 20 or "failed" in context.lower():
        return ("⚠️ **No matching content found.**\n\n"
                "Try re-uploading the file or rephrasing your question.")

    if intent == "summarize":
        st.caption("✍️ *Summarizing…*")
        return f"### 📋 Document Summary\n\n{bullets_to_markdown(cloud_summarize(context))}"

    elif intent == "quiz":
        st.caption("🧪 *Generating quiz…*")
        return f"### 🧪 Quiz\n\n{cloud_quiz(context)}"

    elif intent == "key_points":
        st.caption("🔑 *Extracting key points…*")
        return f"### 🔑 Key Points\n\n{bullets_to_markdown(cloud_key_points(context))}"

    else:
        st.caption("🔍 *Searching document…*")
        return f"### 📄 From Your Document\n\n{cloud_answer(context, user_input)}"

# ─────────────────────────────────────────────────────────────────────────────
# 14. RENDER HISTORY
# ─────────────────────────────────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────────────────────────────────────
# 15. CORE LOOP
# ─────────────────────────────────────────────────────────────────────────────
if user_input := st.chat_input("Ask anything — documents, weather, maths, or just chat…"):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            final_text = ""
            try:
                intent, extra = classify_intent(user_input)

                if intent in ("math", "greeting", "chat"):
                    final_text = chat_llm.invoke(build_lc_messages()).content

                elif intent == "new_doc":
                    if st.session_state.indexed_filenames:
                        names = ", ".join(st.session_state.indexed_filenames)
                        final_text = (f"✅ **Indexed:** **{names}**\n\n"
                                      "Ask me to **summarize**, **quiz**, **extract key points**, "
                                      "or any question about the content!")
                    else:
                        final_text = "Please upload a PDF or text file using the sidebar first."

                elif intent == "weather":
                    st.caption("🌐 *Fetching live weather…*")
                    final_text = f"### 🌤️ Live Weather\n\n{get_weather(extra or 'unknown')}"

                elif intent in ("summarize", "quiz", "key_points", "retrieve"):
                    final_text = run_doc_tool(intent, user_input)

                else:
                    final_text = chat_llm.invoke(build_lc_messages()).content

            except Exception as exc:
                final_text = (f"❌ **Error:**\n\n```\n{exc}\n```\n\n"
                              "Check that Ollama is running and `llama3.2` is pulled.")

            st.markdown(final_text)
            st.session_state.chat_history.append({"role": "assistant", "content": final_text})