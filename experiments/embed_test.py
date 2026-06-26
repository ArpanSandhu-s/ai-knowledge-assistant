from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

result = embeddings.embed_query(
    "Hello world"
)

print(len(result))