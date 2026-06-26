from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from tools import get_weather




model = ChatOllama(model="llama3.2", temperature=0)

agent = create_agent(
    model=model,
    tools=[get_weather],
    
)

config = {
    "recursion_limit": 1
}
try:
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Get weather for Delhi, Mumbai and Ludhiana and compare them."
                }
            ]
        },
        {"recursion_limit": 1}
    )

    print(response["messages"][-1].content)

except Exception as e:
    print(f"Agent stopped safely: {e}")


# from safe_runner import run_agent_safely

# answer = run_agent_safely(
#     agent,
#     "What is weather in Delhi?"
# )

# print(answer)

# response = agent.invoke(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "Get weather for Delhi, Mumbai and Ludhiana and compare them."
#             }
#         ]
#     },
#     config
# )

# print(response["messages"][-1].content)



# response = agent.invoke({
#     "messages": [
#         {"role": "user", "content": "What is weather in Delhi?"}
#     ]
# })

# print(response["messages"][-1].content)
