from langchain_core.tools import tool
from core.rag import retrieve_context
from langchain_ollama import ChatOllama

_helper_llm = ChatOllama(model="llama3.2", temperature=0.2)


@tool
def retrieve_documents(question: str) -> str:
    """
    Retrieve relevant chunks from the user's uploaded PDFs (resume and business proposal)
    to answer questions about their content. Use this whenever the question is about
    facts, details, or specifics contained in those documents.
    """
    try:
        return retrieve_context(question)
    except Exception as e:
        return f"Retrieval failed: {e}"


@tool
def summarize_text(text: str) -> str:
    """
    Summarize a block of text into a short, clear summary.
    Use this when the user asks for a summary of document content you've already retrieved.
    """
    try:
        response = _helper_llm.invoke(f"Summarize this:\n\n{text}")
        return response.content
    except Exception as e:
        return f"Summarization failed: {e}"


@tool
def generate_quiz(text: str) -> str:
    """
    Generate 5 quiz questions based on a block of text.
    Use this when the user asks to be quizzed or tested on document content.
    """
    try:
        response = _helper_llm.invoke(f"Create 5 quiz questions from:\n\n{text}")
        return response.content
    except Exception as e:
        return f"Quiz generation failed: {e}"


@tool
def extract_key_points(text: str) -> str:
    """
    Given a block of already-retrieved text, produce a short bulleted list of its key points.
    Only call this AFTER retrieve_documents has already fetched the relevant text.
    """
    try:
        response = _helper_llm.invoke(f"Extract key points from:\n\n{text}")
        return response.content
    except Exception as e:
        return f"Key point extraction failed: {e}"