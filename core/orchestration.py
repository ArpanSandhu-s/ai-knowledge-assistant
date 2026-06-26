# # from core.agent import knowledge_agent
# # from core.safe_runner import run_agent_safely


# # def run_query(query: str) -> str:
# #     return run_agent_safely(
# #         knowledge_agent,
# #         query,
# #         timeout_seconds=60,
# #         recursion_limit=8,
# #     )



# # """
# # core/orchestration.py
# # ---------------------
# # Provides `run_query(query)` — the single public entry point for running
# # a user query through the knowledge_agent.

# # FIX: Uses relative import `from .agents import get_agent` instead of
# # `from core.agents import get_agent` — this works correctly whether the
# # package is imported as `core.orchestration` or from any working directory.
# # """

# # from __future__ import annotations

# # import traceback
# # from typing import TypedDict

# # from langchain_core.messages import HumanMessage
# # from langchain_core.runnables import RunnableConfig

# # from .agents import get_agent          # ← relative import (the real fix)

# # # ──────────────────────────────────────────────
# # # Configuration
# # # ──────────────────────────────────────────────

# # MAX_RECURSION = 25
# # MAX_ITERATIONS = 10


# # class QueryResult(TypedDict):
# #     success: bool
# #     answer: str
# #     steps: int
# #     error: str | None


# # # ──────────────────────────────────────────────
# # # Internal helpers
# # # ──────────────────────────────────────────────

# # def _extract_final_answer(agent_output: dict) -> tuple[str, int]:
# #     messages = agent_output.get("messages", [])
# #     step_count = max(0, len(messages) - 1)

# #     for msg in reversed(messages):
# #         msg_type  = getattr(msg, "type", None) or type(msg).__name__.lower()
# #         tool_calls = getattr(msg, "tool_calls", None) or []

# #         if msg_type in ("ai", "aimessage") and not tool_calls:
# #             content = getattr(msg, "content", "")
# #             if isinstance(content, list):
# #                 content = " ".join(
# #                     c.get("text", "") if isinstance(c, dict) else str(c)
# #                     for c in content
# #                 )
# #             return str(content).strip(), step_count

# #     if messages:
# #         last = messages[-1]
# #         return str(getattr(last, "content", last)).strip(), step_count

# #     return "No response generated.", 0


# # # ──────────────────────────────────────────────
# # # Public API
# # # ──────────────────────────────────────────────

# # def run_query(query: str) -> QueryResult:
# #     """
# #     Execute the user query through the knowledge_agent with safety guards.
# #     """
# #     if not query or not query.strip():
# #         return QueryResult(
# #             success=False,
# #             answer="",
# #             steps=0,
# #             error="Empty query received. Please provide a non-empty question.",
# #         )

# #     agent = get_agent()

# #     config = RunnableConfig(
# #         recursion_limit=MAX_RECURSION,
# #         configurable={"thread_id": "knowledge-session"},
# #     )

# #     try:
# #         output = agent.invoke(
# #             {"messages": [HumanMessage(content=query)]},
# #             config=config,
# #         )

# #         answer, steps = _extract_final_answer(output)

# #         return QueryResult(
# #             success=True,
# #             answer=answer,
# #             steps=steps,
# #             error=None,
# #         )

# #     except RecursionError as exc:
# #         return QueryResult(
# #             success=False,
# #             answer=(
# #                 f"The agent exceeded the maximum recursion limit ({MAX_RECURSION} steps). "
# #                 "Try a more specific question."
# #             ),
# #             steps=MAX_RECURSION,
# #             error=f"RecursionError: {exc}",
# #         )

# #     except Exception as exc:
# #         tb = traceback.format_exc()
# #         return QueryResult(
# #             success=False,
# #             answer=(
# #                 "An unexpected error occurred. "
# #                 "Check that Ollama is running and ChromaDB is accessible."
# #             ),
# #             steps=0,
# #             error=f"{type(exc).__name__}: {exc}\n\nTraceback:\n{tb}",
# #         )


# # def stream_query(query: str):
# #     """Generator that streams agent events for the given query."""
# #     if not query or not query.strip():
# #         yield {"error": "Empty query."}
# #         return

# #     agent = get_agent()
# #     config = RunnableConfig(recursion_limit=MAX_RECURSION)

# #     try:
# #         for event in agent.stream(
# #             {"messages": [HumanMessage(content=query)]},
# #             config=config,
# #             stream_mode="values",
# #         ):
# #             yield event
# #     except Exception as exc:
# #         yield {"error": f"{type(exc).__name__}: {exc}"}




# from langchain_ollama import ChatOllama

# # Update this to llama3 as well for unified power!
# basic_llm = ChatOllama(model="llama3", temperature=0.5)
# from core.agents import knowledge_agent
# from core.safe_runner import run_agent_safely

# def run_query(query: str) -> str:
#     messages = [
#         {
#             "role": "system",
#             "content": """You are an internship knowledge assistant. You have access to the user's uploaded documents.
# Always call the 'retrieve_documents' tool first if the question relates to those documents."""
#         },
#         {"role": "user", "content": query}
#     ]
    
#     # Pass the messages array straight to the safety runner
#     response = run_agent_safely(knowledge_agent, messages, timeout_seconds=20)
    
#     if isinstance(response, str):
#         return response
        
#     if hasattr(response, "tool_calls") and response.tool_calls:
#         tool_call = response.tool_calls[0]
#         return f"Agent decided to call tool: {tool_call['name']} with args {tool_call['args']}"
        
#     return response.content









from langchain_core import messages

from core.agents import knowledge_agent
from core.safe_runner import run_agent_safely
from core.tools import retrieve_documents, summarize_text, generate_quiz, extract_key_points
from langchain_ollama import ChatOllama

# Plain LLM wrapper for casual chat/greetings
basic_llm = ChatOllama(model="llama3", temperature=0.5)

def run_query(query: str) -> str:
    cleaned_query = query.strip().lower()
    
    # Guardrail 1: Handle plain greetings instantly
    if cleaned_query in ["hi", "hello", "hey", "greetings"]:
        response = basic_llm.invoke("The user just said hello. Give a friendly, 1-sentence welcome greeting as an internship knowledge assistant.")
        return response.content

    print("[System: Automatically pulling relevant document context...]")
    # Force step 1: Always grab the actual context from your Chroma DB first!
    context_text = retrieve_documents.invoke({"query": query})
    
    if not context_text or "failed" in context_text.lower():
        return "I couldn't find or read any relevant documents in the database."

    # Build the conversation history with instructions + the REAL document content loaded
    messages = [
        {
            "role": "system",
            "content": f"""You are an internship knowledge assistant. 
Here is the actual content retrieved from the user's uploaded documents:
---
{context_text}
---
Review the user's request. If they want a summary, call 'summarize_text'. If they want a quiz, call 'generate_quiz'. If they want key points, call 'extract_key_points'. If they just asked a normal question, answer it directly using the context provided above."""
        },
        {"role": "user", "content": query}
    ]
    
    # Send it to our tool-bound agent
    response = run_agent_safely(knowledge_agent, messages, timeout_seconds=20)
    
    if isinstance(response, str):
        return response
        
    # Guardrail 2: Handle the tool calls explicitly with the real data
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        print(f"\n[Agent decided to execute tool: {tool_name}]")
        
        # Branch 1: Summarize Text
        if tool_name == "summarize_text":
            return summarize_text.invoke({"text": context_text})
            
        # Branch 2: Generate Quiz
        elif tool_name == "generate_quiz":
            print("[System: Formatting document content into an interactive evaluation...]")
            return generate_quiz.invoke({"text": context_text})
            
        # Branch 3: Extract Key Points
        elif tool_name == "extract_key_points":
            print("[System: Isolating crucial takeaways and technical high-points...]")
            return extract_key_points.invoke({"text": context_text})
            
    return response.content