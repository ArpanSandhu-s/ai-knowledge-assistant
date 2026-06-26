from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

# =====================================
# MODEL
# =====================================

model = ChatOllama(
    model="llama3.2",
    temperature=0
)

# =====================================
# TOOL 1 - TODO MANAGER
# =====================================

todo_list = []

@tool
def add_todo(task: str) -> str:
    """Add a task to the todo list."""
    todo_list.append(task)
    return f"Added task: {task}"

# =====================================
# TOOL 2 - LIST TODOS
# =====================================

@tool
def list_todos() -> str:
    """Show all todo items."""
    
    if not todo_list:
        return "No tasks found."

    return "\n".join(todo_list)

# =====================================
# TOOL 3 - UNIT CONVERTER
# =====================================

@tool
def km_to_miles(km: float) -> str:
    """Convert kilometers to miles."""
    
    miles = km * 0.621371

    return f"{km} km = {miles:.2f} miles"

# =====================================
# MEMORY
# =====================================

checkpointer = InMemorySaver()

# =====================================
# AGENT
# =====================================

agent = create_agent(
    model=model,
    tools=[
        add_todo,
        list_todos,
        km_to_miles
    ],
    system_prompt="""
You are a productivity assistant.

You have access to tools.

Use tools whenever necessary.

Capabilities:
- Add tasks
- View tasks
- Convert kilometers to miles

Remember previous conversation context.
""",
    checkpointer=checkpointer
)

# =====================================
# SESSION CONFIG
# =====================================

config = {
    "configurable": {
        "thread_id": "user-session"
    }
}

# =====================================
# TURN 1
# =====================================

r1 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Add Study Azure AI Agents to my todo list."
            }
        ]
    },
    config=config
)

print("\n" + "=" * 60)
print("TURN 1")
print("=" * 60)
print(r1["messages"][-1].content)

# =====================================
# TURN 2
# =====================================

r2 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Convert 15 km to miles."
            }
        ]
    },
    config=config
)

print("\n" + "=" * 60)
print("TURN 2")
print("=" * 60)
print(r2["messages"][-1].content)

# =====================================
# TURN 3
# =====================================

r3 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What task did I ask you to remember earlier?"
            }
        ]
    },
    config=config
)

print("\n" + "=" * 60)
print("TURN 3")
print("=" * 60)
print(r3["messages"][-1].content)

# =====================================
# FULL TRACE
# =====================================

print("\n")
print("=" * 60)
print("FULL MESSAGE TRACE")
print("=" * 60)

for msg in r3["messages"]:

    print("\n------------------------------")
    print("TYPE:", type(msg).__name__)
    print("------------------------------")
    print(msg)