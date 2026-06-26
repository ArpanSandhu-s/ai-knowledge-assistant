from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

# =========================
# Model
# =========================

model = ChatOllama(
    model="llama3.2",
    temperature=0
)

# =========================
# Tool
# =========================

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    weather_data = {
        "mumbai": "32°C",
        "delhi": "38°C",
        "ludhiana": "34°C"
    }

    return weather_data.get(city.lower(), "Weather not found")


# =========================
# Memory
# =========================

checkpointer = InMemorySaver()

# =========================
# Agent
# =========================

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant. Use tools when necessary.",
    checkpointer=checkpointer
)

config = {
    "configurable": {
        "thread_id": "session-1"
    }
}

# =========================
# Turn 1
# =========================

r1 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What's the weather in Mumbai?"
            }
        ]
    },
    config=config
)

print("\nTURN 1")
print(r1["messages"][-1].content)

# =========================
# Turn 2
# =========================

r2 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Is that hotter than Delhi?"
            }
        ]
    },
    config=config
)

print("\nTURN 2")
print(r2["messages"][-1].content)