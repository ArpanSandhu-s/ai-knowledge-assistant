from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

vectorstore = Chroma(
    persist_directory="db",
    embedding_function=embeddings
)

def retrieve_context(query):

    docs = vectorstore.similarity_search(
        query,
        k=3
    )

    return "\n\n".join(
        doc.page_content
        for doc in docs
    )