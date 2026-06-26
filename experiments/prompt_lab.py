from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

llm = OllamaLLM(model="gemma3:latest")

# Zero-shot
zero_shot = "Classify the sentiment: 'The food arrived cold and the staff was rude.'"

# Few-shot
few_shot = """
Classify the sentiment as Positive, Negative, or Neutral.

Review: "Amazing service, loved it!"
Sentiment: Positive

Review: "It was okay, nothing special."
Sentiment: Neutral

Review: "The food arrived cold and the staff was rude."
Sentiment:
"""

print("--- Zero-shot ---")
print(llm.invoke(zero_shot))

print("\n--- Few-shot ---")
print(llm.invoke(few_shot))

# System Prompt Example
template = ChatPromptTemplate.from_messages([
    ("system", "You are a terse assistant. Answer in one sentence only."),
    ("user", "{question}")
])

chain = template | llm

print("\n--- With System Prompt ---")
print(chain.invoke({"question": "Why is the sky blue?"}))