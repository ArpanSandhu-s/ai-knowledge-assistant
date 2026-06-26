from core.orchestration import run_query

print("Internship Knowledge Bot")
print("Type 'exit' to quit")

while True:
    query = input("\nYou: ").strip()
    if query.lower() == "exit":
        print("Goodbye!")
        break
    response = run_query(query)
    print("\nBot:")
    print(response)