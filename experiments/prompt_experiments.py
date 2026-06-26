from langchain_ollama import OllamaLLM

cold = OllamaLLM(
    model="gemma3:latest",
    temperature=0
)

creative = OllamaLLM(
    model="gemma3:latest",
    temperature=1.2
)

question = "Give me a startup idea."

print("=== Temperature 0 ===")
print(cold.invoke(question))

print("\n---\n")

print("=== Temperature 1.2 ===")
print(creative.invoke(question))