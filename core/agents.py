# """
# core/agents.py
# --------------
# Defines the knowledge_agent using LangGraph's create_react_agent.

# FIX: Neither `prompt=` (old) nor `system_prompt=` (mid) work universally
# across all langgraph versions. The safest cross-version approach is to pass
# the system message via the `messages` key in a `state_modifier` callable,
# OR to pass a pre-built ChatPromptTemplate as `prompt=`.

# This file detects which signature your installed langgraph supports and uses
# the correct one automatically — so it works on ANY langgraph version.
# """

# import inspect

# from langchain_ollama import ChatOllama
# from langchain_core.messages import SystemMessage
# from langgraph.prebuilt import create_react_agent

# from .tools import (
#     retrieve_documents,
#     summarize_text,
#     generate_quiz,
#     extract_key_points,
# )

# # ──────────────────────────────────────────────
# # Model
# # ──────────────────────────────────────────────

# OLLAMA_MODEL = "llama3.2"

# def _build_llm() -> ChatOllama:
#     return ChatOllama(
#         model=OLLAMA_MODEL,
#         temperature=0.2,
#         num_predict=2048,
#     )


# # ──────────────────────────────────────────────
# # System Prompt text
# # ──────────────────────────────────────────────

# SYSTEM_TEXT = """You are a knowledgeable AI research assistant with access to a local knowledge base.

# You have four tools available:

# 1. retrieve_documents  – Search the knowledge base for relevant documents.
# 2. summarize_text      – Produce a concise bullet-point summary of any text.
# 3. generate_quiz       – Create a 3-question multiple-choice quiz from text.
# 4. extract_key_points  – Pull out the most important facts and concepts from text.

# Guidelines:
# - Always start by calling `retrieve_documents` with the user's query to ground your answer in retrieved context.
# - Use `summarize_text` when the user asks for a summary or overview.
# - Use `generate_quiz` when the user wants to test their knowledge or requests a quiz.
# - Use `extract_key_points` when the user wants key facts, concepts, or takeaways.
# - You may chain multiple tools in sequence when it improves the answer quality.
# - If a tool returns an error string (starting with 'ERROR'), report it clearly to the user and suggest corrective actions.
# - Never fabricate document contents. If the knowledge base has no relevant information, say so honestly.
# - Be concise, structured, and accurate in every response.""".strip()


# # ──────────────────────────────────────────────
# # Tools list
# # ──────────────────────────────────────────────

# TOOLS = [
#     retrieve_documents,
#     summarize_text,
#     generate_quiz,
#     extract_key_points,
# ]


# # ──────────────────────────────────────────────
# # Version-safe agent factory
# # ──────────────────────────────────────────────

# def _detect_langgraph_signature() -> str:
#     """
#     Inspect the installed create_react_agent signature and return
#     which approach to use:
#       'state_modifier'  → modern langgraph (≥ 0.2)
#       'system_prompt'   → mid langgraph (0.1.x)
#       'prompt'          → old langgraph (< 0.1)
#       'messages_modifier' → some 0.1 builds
#     """
#     sig = inspect.signature(create_react_agent)
#     params = set(sig.parameters.keys())

#     if "state_modifier" in params:
#         return "state_modifier"
#     if "system_prompt" in params:
#         return "system_prompt"
#     if "messages_modifier" in params:
#         return "messages_modifier"
#     if "prompt" in params:
#         return "prompt"
#     # Absolute fallback: try state_modifier
#     return "state_modifier"


# def create_knowledge_agent():
#     """
#     Build and return the compiled knowledge_agent graph.
#     Automatically selects the correct keyword argument for the installed
#     version of langgraph so this never raises TypeError.
#     """
#     llm      = _build_llm()
#     approach = _detect_langgraph_signature()
#     system_msg = SystemMessage(content=SYSTEM_TEXT)

#     if approach == "state_modifier":
#         # langgraph ≥ 0.2.x — state_modifier receives the full state dict
#         # and returns a modified messages list
#         def add_system_message(state):
#             messages = state["messages"]
#             # Prepend system message if not already present
#             if not messages or not isinstance(messages[0], SystemMessage):
#                 return [system_msg] + list(messages)
#             return messages

#         agent = create_react_agent(
#             model=llm,
#             tools=TOOLS,
#             state_modifier=add_system_message,
#         )

#     elif approach == "system_prompt":
#         agent = create_react_agent(
#             model=llm,
#             tools=TOOLS,
#             system_prompt=SYSTEM_TEXT,
#         )

#     elif approach == "messages_modifier":
#         def add_system_message_list(messages):
#             if not messages or not isinstance(messages[0], SystemMessage):
#                 return [system_msg] + list(messages)
#             return messages

#         agent = create_react_agent(
#             model=llm,
#             tools=TOOLS,
#             messages_modifier=add_system_message_list,
#         )

#     else:
#         # Oldest langgraph: prompt= accepted a list of BaseMessages or a string
#         from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", SYSTEM_TEXT),
#             MessagesPlaceholder(variable_name="messages"),
#         ])
#         agent = create_react_agent(
#             model=llm,
#             tools=TOOLS,
#             prompt=prompt,
#         )

#     return agent


# # ──────────────────────────────────────────────
# # Module-level singleton
# # ──────────────────────────────────────────────

# _agent_instance = None

# def get_agent():
#     global _agent_instance
#     if _agent_instance is None:
#         _agent_instance = create_knowledge_agent()
#     return _agent_instance




# from langchain_ollama import ChatOllama
# from core.tools import (
#     retrieve_documents,
#     summarize_text,
#     generate_quiz,
#     extract_key_points,
# )

# llm = ChatOllama(model="llama3.2", temperature=0.2)

# knowledge_agent = llm.bind_tools([
#     retrieve_documents,
#     summarize_text,
#     generate_quiz,
#     extract_key_points,
# ])













from langchain_ollama import ChatOllama
from core.tools import (
    retrieve_documents,
    summarize_text,
    generate_quiz,
    extract_key_points,
)

# Initialize our local LLM
llm = ChatOllama(model="llama3.2", temperature=0.2)

# Bind all 4 of your project tools natively to the model
knowledge_agent = llm.bind_tools([
    retrieve_documents,
    summarize_text,
    generate_quiz,
    extract_key_points
])