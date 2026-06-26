import concurrent.futures
import re


def _looks_like_unexecuted_tool_call(text: str) -> bool:
    """Detect if the model printed a tool call as text instead of actually invoking it."""
    if not isinstance(text, str):
        return False
    pattern = r'^\s*\w+\s*\(\s*\w+\s*=.*\)\s*$'
    return bool(re.match(pattern, text.strip()))

import concurrent.futures

def run_agent_safely(agent, messages, timeout_seconds=20):
    """
    Safely invokes our native tool-bound LLM runner.
    Since we are using native tool binding, we don't need a recursion_limit here
    (the execution loop is controlled in orchestration).
    """
    def invoke():
        return agent.invoke(messages)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(invoke)
        try:
            result = future.result(timeout=timeout_seconds)
            return result
        except concurrent.futures.TimeoutError:
            return "Agent timed out waiting for a response."
        except Exception as e:
            return f"Agent error: {e}"
# def run_agent_safely(agent, message, timeout_seconds=60, recursion_limit=8):
#     config = {"recursion_limit": recursion_limit}

#     def invoke():
#         return agent.invoke(
#             {"messages": [{"role": "user", "content": message}]},
#             config
#         )

#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future = executor.submit(invoke)
#         try:
#             result = future.result(timeout=timeout_seconds)
#             answer = result["messages"][-1].content

#             if _looks_like_unexecuted_tool_call(answer):
#                 return ("The model attempted to call a tool but didn't execute it correctly. "
#                         "Try rephrasing your question.")

#             return answer

#         except concurrent.futures.TimeoutError:
#             return "Agent timed out."
#         except Exception as e:
#             return f"Agent error: {e}"
