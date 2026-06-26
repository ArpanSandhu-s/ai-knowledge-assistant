from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma3:latest"
)

messages = []

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    messages.append(
        ("human", user_input)
    )

    response = llm.invoke(messages)

    print("\nGemma:")
    print(response.content)
    print()

    messages.append(
        ("ai", response.content)
    )