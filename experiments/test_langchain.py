from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma3:latest"
)

response = llm.invoke(
    "Tell me a one-sentence programming joke."
)

print(response.content)