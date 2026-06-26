
# import requests
# from langchain_core.tools import tool
# from core.rag import retrieve_context


# @tool
# def get_weather(city: str) -> str:
#     """
#     Get the current real weather for any city in the world.
#     Use this whenever the user asks about weather, temperature,
#     rain, humidity, or climate conditions for any location.
#     """
#     try:
#         url = f"https://wttr.in/{city}?format=3"
#         response = requests.get(url, timeout=10)
#         if response.status_code == 200:
#             return response.text.strip()
#         return f"Could not fetch weather for {city}."
#     except Exception as e:
#         return f"Weather tool error: {e}"


# @tool
# def calculate(expression: str) -> str:
#     """
#     Evaluate a mathematical expression and return the result.
#     Use this for any arithmetic, percentages, or numeric calculations.
#     Examples: "12 * 7 + 3", "150 / 4", "2 ** 10"
#     """
#     try:
#         result = eval(expression, {"__builtins__": {}})
#         return str(result)
#     except Exception as e:
#         return f"Calculation error: {e}"


# @tool
# def search_documents(question: str) -> str:
#     """
#     Search the user's personal uploaded documents (resume and business proposal)
#     for relevant information. Use this only when the user asks something specifically
#     about their own documents, resume, skills, experience, or business proposal.
#     Do NOT use this for general knowledge questions.
#     """
#     try:
#         return retrieve_context(question)
#     except Exception as e:
#         return f"Document search failed: {e}"



"""
core/tools.py
-------------
LangChain @tool functions for the multi-agent RAG application.
Each tool wraps its logic in a try/except block so that agent execution
never crashes – it always returns a human-readable error string instead.
"""

from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

# ──────────────────────────────────────────────
# Shared singletons (created once at import time)
# ──────────────────────────────────────────────

OLLAMA_MODEL = "llama3"
EMBED_MODEL  = "nomic-embed-text"
CHROMA_PATH  = "./chroma_db"
COLLECTION   = "knowledge_base"

def _get_vectorstore() -> Chroma:
    """Return a Chroma vectorstore backed by the local Ollama embedding model."""
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )

def _get_llm() -> ChatOllama:
    """Return a lightweight ChatOllama instance for helper calls inside tools."""
    return ChatOllama(model=OLLAMA_MODEL, temperature=0.3)


# ──────────────────────────────────────────────
# Tool 1 – Retrieve Documents
# ──────────────────────────────────────────────
from langchain_core.tools import tool
from core.rag import retrieve_context

@tool
def retrieve_documents(query: str) -> str:
    """Retrieves relevant chunks of text from the uploaded internship documents and PDFs. 
    Use this whenever the user asks about rules, policies, dates, or company specific data."""
    try:
        return retrieve_context(query)
    except Exception as e:
        return f"Error retrieving documents: {e}"

# @tool
# def retrieve_documents(query: str) -> str:
#     """
#     Search the ChromaDB vector store and return the top-5 most relevant
#     document chunks for the given query.

#     Args:
#         query: The search query string.

#     Returns:
#         A formatted string containing the retrieved document chunks,
#         or an error message if retrieval fails.
#     """
#     try:
#         vs = _get_vectorstore()
#         results = vs.similarity_search(query, k=5)

#         if not results:
#             return "No relevant documents found in the knowledge base for this query."

#         parts = []
#         for i, doc in enumerate(results, start=1):
#             source = doc.metadata.get("source", "unknown")
#             parts.append(f"[{i}] Source: {source}\n{doc.page_content.strip()}")

#         return "\n\n---\n\n".join(parts)

#     except Exception as exc:
#         return (
#             f"ERROR in retrieve_documents: {type(exc).__name__}: {exc}. "
#             "Ensure ChromaDB is persisted at ./chroma_db and nomic-embed-text is pulled in Ollama."
#         )


# ──────────────────────────────────────────────
# Tool 2 – Summarize Text
# ──────────────────────────────────────────────

@tool
def summarize_text(text: str) -> str:
    """
    Produce a concise, structured summary of the supplied text using the
    local Llama 3 model.

    Args:
        text: The raw text to summarize (e.g. retrieved document chunks).

    Returns:
        A bullet-point summary string, or an error message if the LLM call fails.
    """
    try:
        if not text or not text.strip():
            return "ERROR in summarize_text: Received empty text. Nothing to summarize."

        llm = _get_llm()
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    "You are a precise summarization assistant. "
                    "When given text, return a concise summary using 3-7 bullet points. "
                    "Each bullet must start with '•'. Do not add any preamble."
                ),
            ),
            ("human", "Summarize the following text:\n\n{text}"),
        ])
        chain = prompt | llm
        response = chain.invoke({"text": text})
        return response.content.strip()

    except Exception as exc:
        return (
            f"ERROR in summarize_text: {type(exc).__name__}: {exc}. "
            "Ensure Ollama is running and llama3.2 is available (`ollama pull llama3.2`)."
        )


# ──────────────────────────────────────────────
# Tool 3 – Generate Quiz
# ──────────────────────────────────────────────

@tool
def generate_quiz(text: str) -> str:
    """
    Generate a short multiple-choice quiz (3 questions) based on the
    provided text, using the local Llama 3.2 model.

    Args:
        text: The source text from which quiz questions should be generated.

    Returns:
        A formatted quiz string with questions and answer choices,
        or an error message if generation fails.
    """
    try:
        if not text or not text.strip():
            return "ERROR in generate_quiz: Received empty text. Cannot generate a quiz."

        llm = _get_llm()
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    "You are an expert quiz creator. Given source text, generate exactly "
                    "3 multiple-choice questions. Format strictly as:\n"
                    "Q1. <question>\n"
                    "  A) <option>\n  B) <option>\n  C) <option>\n  D) <option>\n"
                    "Answer: <letter>\n\n"
                    "Repeat for Q2 and Q3. Output nothing else."
                ),
            ),
            ("human", "Generate a quiz from this text:\n\n{text}"),
        ])
        chain = prompt | llm
        response = chain.invoke({"text": text})
        return response.content.strip()

    except Exception as exc:
        return (
            f"ERROR in generate_quiz: {type(exc).__name__}: {exc}. "
            "Ensure Ollama is running and llama3.2 is available."
        )


# ──────────────────────────────────────────────
# Tool 4 – Extract Key Points
# ──────────────────────────────────────────────

@tool
def extract_key_points(text: str) -> str:
    """
    Extract the most important concepts, entities, and facts from the
    provided text using the local Llama 3.2 model.

    Args:
        text: The text from which key points should be extracted.

    Returns:
        A numbered list of key points, or an error message if extraction fails.
    """
    try:
        if not text or not text.strip():
            return "ERROR in extract_key_points: Received empty text. Nothing to extract."

        llm = _get_llm()
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    "You are an expert at distilling information. "
                    "Given text, extract the 5-10 most important key points, concepts, "
                    "entities, or facts. Format as a numbered list: '1. <point>'. "
                    "Be specific and factual. Output nothing else."
                ),
            ),
            ("human", "Extract key points from this text:\n\n{text}"),
        ])
        chain = prompt | llm
        response = chain.invoke({"text": text})
        return response.content.strip()

    except Exception as exc:
        return (
            f"ERROR in extract_key_points: {type(exc).__name__}: {exc}. "
            "Ensure Ollama is running and llama3.2 is available."
        )