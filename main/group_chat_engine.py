# """
# group_chat_engine.py
# ====================
# Implements the Azure AI Agent Design Pattern: Group Chat Orchestration
# Reference: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns

# Architecture:
#     User Query
#         │
#         ▼
#   ┌─────────────────┐
#   │  GroupChatManager│  ◄── reads shared transcript, picks next speaker or FINISH
#   └────────┬────────┘
#            │
#   ┌────────┼────────┐
#   ▼        ▼        ▼
# Data    Weather  Generalist
# Analyst  Agent    Agent
#   │        │        │
#   └────────┼────────┘
#            ▼
#     Shared Transcript
# """

# import json
# import logging
# from typing import List, Dict

# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("GroupChatEngine")


# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 1 — AGENT REGISTRY
# # Defines what each specialist agent is capable of.
# # The Manager reads this to make routing decisions.
# # ─────────────────────────────────────────────────────────────────────────────
# AGENT_REGISTRY = {
#     "Data_Analyst": (
#         "Handles all requests about uploaded documents, PDFs, and text files. "
#         "Specializes in summarization, quiz generation, key point extraction, "
#         "and answering questions grounded in document content."
#     ),
#     "Weather_Agent": (
#         "Handles all weather-related queries: current temperature, forecasts, "
#         "humidity, wind, and climate for any city or region."
#     ),
#     "Generalist_Agent": (
#         "Handles general conversation, greetings, math problems, and any "
#         "question that does not involve documents or weather."
#     ),
# }

# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 2 — SPECIALIST SYSTEM PROMPTS
# # Each agent has a strict role definition so it stays focused.
# # ─────────────────────────────────────────────────────────────────────────────
# AGENT_SYSTEM_PROMPTS = {
#     "Data_Analyst": (
#         "You are the Data Analyst Agent. Your only job is to analyze document "
#         "content provided to you. Summarize clearly, generate quizzes with "
#         "correct answers marked, or extract key points as bullet lists. "
#         "Always base your answer strictly on the provided document context. "
#         "Never make up information not present in the context."
#     ),
#     "Weather_Agent": (
#         "You are the Weather Agent. Your job is to present weather data in a "
#         "clean markdown table format. Highlight temperature, humidity, wind "
#         "speed, and conditions clearly. If weather data is provided in the "
#         "conversation, format and present it professionally."
#     ),
#     "Generalist_Agent": (
#         "You are a friendly general-purpose assistant. Answer math questions "
#         "step by step. Respond to greetings warmly. Handle any topic not "
#         "covered by the other specialists. Be concise and helpful."
#     ),
# }


# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 3 — GROUP CHAT MANAGER
# # The orchestration heart. Reads the shared transcript after every turn
# # and autonomously decides which specialist speaks next.
# # ─────────────────────────────────────────────────────────────────────────────
# class GroupChatManager:
#     def __init__(self, llm):
#         self.llm = llm

#     def select_next_speaker(self, transcript: List[Dict[str, str]]) -> str:
#         """
#         Reads the shared group chat transcript and returns either:
#         - The name of the next agent to speak (Data_Analyst / Weather_Agent / Generalist_Agent)
#         - 'FINISH' if the task is complete
#         """
#         formatted = "\n".join(
#             f"[{msg['sender']}]: {msg['content']}" for msg in transcript
#         )

#         selector_prompt = f"""You are the Group Chat Manager. Your ONLY job is to read the conversation log below and decide which specialized agent should speak next.

# AVAILABLE AGENTS:
# {json.dumps(AGENT_REGISTRY, indent=2)}

# RULES:
# 1. If a specialist agent has already given a complete, final answer to the user's request, return exactly: FINISH
# 2. If the user asked about a document, PDF, file, summary, quiz, or key points → select: Data_Analyst
# 3. If the user asked about weather, temperature, forecast, or climate → select: Weather_Agent
# 4. For greetings, math, or any general question → select: Generalist_Agent
# 5. Return ONLY the agent name or FINISH. No explanation. No punctuation. No extra words.

# CONVERSATION LOG:
# {formatted}

# NEXT SPEAKER:"""

#         try:
#             response = self.llm.invoke([HumanMessage(content=selector_prompt)])
#             speaker = response.content.strip().strip("'\"").strip()

#             # Validate — only accept known agents or FINISH
#             valid = set(AGENT_REGISTRY.keys()) | {"FINISH"}
#             if speaker in valid:
#                 logger.info(f"[Manager] → Selected: {speaker}")
#                 return speaker

#             # If LLM drifted, try to find a valid name inside the response
#             for name in AGENT_REGISTRY:
#                 if name in speaker:
#                     logger.info(f"[Manager] → Extracted from response: {name}")
#                     return name

#             logger.warning(f"[Manager] → Unrecognised response '{speaker}', defaulting to Generalist_Agent")
#             return "Generalist_Agent"

#         except Exception as e:
#             logger.error(f"[Manager] Selection error: {e}")
#             return "Generalist_Agent"


# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 4 — GROUP CHAT ORCHESTRATOR
# # Runs the full dynamic loop:
# #   1. Manager picks speaker
# #   2. Specialist agent responds
# #   3. Response is appended to shared transcript
# #   4. Repeat until FINISH or max_rounds
# # ─────────────────────────────────────────────────────────────────────────────
# class GroupChatOrchestrator:
#     def __init__(self, llm, max_rounds: int = 4):
#         self.llm = llm
#         self.manager = GroupChatManager(llm)
#         self.max_rounds = max_rounds  # Termination safety boundary

#     def run(
#         self,
#         user_query: str,
#         doc_context: str = "",
#         weather_data: str = "",
#     ) -> List[Dict[str, str]]:
#         """
#         Executes the Group Chat loop.

#         Args:
#             user_query:   The raw user message
#             doc_context:  Retrieved RAG chunks (if any document is active)
#             weather_data: Pre-fetched weather string (if weather intent detected)

#         Returns:
#             shared_transcript: Full list of all turns including agent responses
#         """

#         # ── PILLAR 1: Initialise the Shared Workspace Transcript ──────────────
#         shared_transcript: List[Dict[str, str]] = []

#         # Inject document context into transcript if available
#         if doc_context:
#             shared_transcript.append({
#                 "sender": "System_RAG_Context",
#                 "content": f"Relevant document content retrieved:\n\n{doc_context}"
#             })

#         # Inject pre-fetched weather data if available
#         if weather_data:
#             shared_transcript.append({
#                 "sender": "System_Weather_Feed",
#                 "content": f"Live weather data retrieved:\n\n{weather_data}"
#             })

#         # Add the user's actual query
#         shared_transcript.append({
#             "sender": "User",
#             "content": user_query
#         })

#         # ── PILLAR 4: The Orchestration Loop ──────────────────────────────────
#         for round_num in range(self.max_rounds):
#             logger.info(f"\n{'='*50}\n[Round {round_num + 1}] Manager evaluating transcript...\n{'='*50}")

#             # Step 1 — Manager reads transcript and selects next speaker
#             next_speaker = self.manager.select_next_speaker(shared_transcript)

#             # Step 2 — TERMINATION: Manager flagged task complete
#             if next_speaker == "FINISH":
#                 logger.info("[Termination Engine] Manager signalled FINISH. Loop ended.")
#                 break

#             # Step 3 — Build the specialist agent's message context
#             system_role = AGENT_SYSTEM_PROMPTS.get(
#                 next_speaker,
#                 AGENT_SYSTEM_PROMPTS["Generalist_Agent"]
#             )
#             messages = [SystemMessage(content=system_role)]

#             # Feed the full shared transcript to the specialist
#             for turn in shared_transcript:
#                 if turn["sender"] == "User":
#                     messages.append(HumanMessage(content=turn["content"]))
#                 else:
#                     # All non-user turns become AI context
#                     messages.append(AIMessage(
#                         content=f"[{turn['sender']}]: {turn['content']}"
#                     ))

#             # Step 4 — Invoke the specialist agent
#             try:
#                 logger.info(f"[{next_speaker}] Generating response...")
#                 agent_response = self.llm.invoke(messages)
#                 output = agent_response.content.strip()

#                 # Step 5 — Append specialist's response to shared transcript
#                 shared_transcript.append({
#                     "sender": next_speaker,
#                     "content": output
#                 })

#                 logger.info(f"[{next_speaker}] Response added to transcript.")

#             except Exception as e:
#                 logger.error(f"[{next_speaker}] Execution error: {e}")
#                 shared_transcript.append({
#                     "sender": next_speaker,
#                     "content": f"⚠️ Agent encountered an error: {e}"
#                 })
#                 break
#         return shared_transcript








# """
# group_chat_engine.py
# ====================
# Implements the Azure AI Agent Design Pattern: Group Chat Orchestration
# Reference: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns

# Architecture:
#     User Query
#         │
#         ▼
#   ┌─────────────────┐
#   │  GroupChatManager│  ◄── reads shared transcript, picks next speaker or FINISH
#   └────────┬────────┘
#            │
#   ┌────────┼────────┐
#   ▼        ▼        ▼
# Data    Weather  Generalist
# Analyst  Agent    Agent
#   │        │        │
#   └────────┼────────┘
#            ▼
#     Shared Transcript
# """

# import json
# import logging
# from typing import List, Dict

# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("GroupChatEngine")


# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 1 — AGENT REGISTRY
# # ─────────────────────────────────────────────────────────────────────────────
# AGENT_REGISTRY = {
#     "Data_Analyst": (
#         "Handles all requests about uploaded documents, PDFs, and text files. "
#         "Specializes in summarization, quiz generation, key point extraction, "
#         "and answering questions grounded in document content."
#     ),
#     "Weather_Agent": (
#         "Handles all weather-related queries: current temperature, forecasts, "
#         "humidity, wind, and climate for any city or region."
#     ),
#     "Generalist_Agent": (
#         "Handles general conversation, greetings, math problems, and any "
#         "question that does not involve documents or weather."
#     ),
# }

# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 2 — SPECIALIST SYSTEM PROMPTS
# # ─────────────────────────────────────────────────────────────────────────────
# AGENT_SYSTEM_PROMPTS = {
#     "Data_Analyst": (
#         "You are the Data Analyst Agent. Your only job is to analyze document "
#         "content provided to you. Summarize clearly, generate quizzes with "
#         "correct answers marked, or extract key points as bullet lists. "
#         "Always base your answer strictly on the provided document context. "
#         "Never make up information not present in the context."
#     ),
#     "Weather_Agent": (
#         "You are the Weather Agent. Weather data has already been fetched and "
#         "is provided in the conversation. Present it in a clean markdown table "
#         "format with temperature, humidity, wind speed, and conditions clearly shown. "
#         "Do NOT say you cannot access the internet — the data is already in the transcript."
#     ),
#     "Generalist_Agent": (
#         "You are a friendly general-purpose assistant. Answer math questions "
#         "step by step. Respond to greetings warmly. Handle any topic not "
#         "covered by the other specialists. Be concise and helpful. "
#         "You have access to the full conversation history — use it to answer "
#         "follow-up questions and remember what was discussed earlier."
#     ),
# }


# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 3 — GROUP CHAT MANAGER
# # ─────────────────────────────────────────────────────────────────────────────
# class GroupChatManager:
#     def __init__(self, llm):
#         self.llm = llm

#     def select_next_speaker(self, transcript: List[Dict[str, str]]) -> str:
#         """
#         FIX 1 — TERMINATION BUG:
#         We now check if a specialist already responded BEFORE asking the LLM.
#         If any specialist agent already has a turn in the transcript, return FINISH immediately.
#         This prevents the manager from calling a second or third agent turn.
#         """
#         specialist_names = set(AGENT_REGISTRY.keys())
#         agents_who_spoke = [
#             t["sender"] for t in transcript
#             if t["sender"] in specialist_names
#         ]

#         # If any specialist has already responded → task is done → FINISH
#         if agents_who_spoke:
#             logger.info(f"[Manager] {agents_who_spoke[-1]} already responded → FINISH")
#             return "FINISH"

#         # No specialist has spoken yet — ask LLM to pick the right one
#         formatted = "\n".join(
#             f"[{msg['sender']}]: {msg['content'][:200]}" for msg in transcript
#         )

#         selector_prompt = f"""You are the Group Chat Manager. Read the conversation and select ONE agent.

# AVAILABLE AGENTS:
# {json.dumps(AGENT_REGISTRY, indent=2)}

# RULES:
# 1. If the user asked about a document, PDF, file, summary, quiz, or key points → select: Data_Analyst
# 2. If the user asked about weather, temperature, forecast, or climate → select: Weather_Agent
# 3. For greetings, math, general questions, or anything else → select: Generalist_Agent
# 4. Return ONLY the agent name. No explanation. No punctuation.

# CONVERSATION:
# {formatted}

# NEXT SPEAKER:"""

#         try:
#             response = self.llm.invoke([HumanMessage(content=selector_prompt)])
#             speaker = response.content.strip().strip("'\"").strip()

#             valid = set(AGENT_REGISTRY.keys())
#             if speaker in valid:
#                 logger.info(f"[Manager] → Selected: {speaker}")
#                 return speaker

#             for name in AGENT_REGISTRY:
#                 if name in speaker:
#                     logger.info(f"[Manager] → Extracted: {name}")
#                     return name

#             logger.warning(f"[Manager] → Unrecognised '{speaker}', defaulting to Generalist_Agent")
#             return "Generalist_Agent"

#         except Exception as e:
#             logger.error(f"[Manager] Selection error: {e}")
#             return "Generalist_Agent"


# # ─────────────────────────────────────────────────────────────────────────────
# # PILLAR 4 — GROUP CHAT ORCHESTRATOR
# # ─────────────────────────────────────────────────────────────────────────────
# class GroupChatOrchestrator:
#     def __init__(self, llm, max_rounds: int = 4):
#         self.llm = llm
#         self.manager = GroupChatManager(llm)
#         self.max_rounds = max_rounds

#     def run(
#         self,
#         user_query: str,
#         doc_context: str = "",
#         weather_data: str = "",
#         chat_history: list = None,   # FIX 2 — MEMORY: accepts session history
#     ) -> List[Dict[str, str]]:
#         """
#         FIX 2 — MEMORY BUG:
#         chat_history (from st.session_state.chat_history) is now prepended
#         to the shared transcript so agents can see prior conversation turns.
#         """

#         shared_transcript: List[Dict[str, str]] = []

#         # ── Inject prior conversation memory ──────────────────────────────────
#         if chat_history:
#             # Only include last 6 turns to keep context lean
#             recent = chat_history[-6:]
#             for turn in recent:
#                 role = "User" if turn["role"] == "user" else "Assistant"
#                 shared_transcript.append({
#                     "sender": role,
#                     "content": turn["content"]
#                 })

#         # ── Inject document context ───────────────────────────────────────────
#         if doc_context:
#             shared_transcript.append({
#                 "sender": "System_RAG_Context",
#                 "content": f"Relevant document content retrieved:\n\n{doc_context}"
#             })

#         # ── Inject pre-fetched weather data ───────────────────────────────────
#         if weather_data:
#             shared_transcript.append({
#                 "sender": "System_Weather_Feed",
#                 "content": f"Live weather data retrieved:\n\n{weather_data}"
#             })

#         # ── Add current user query ────────────────────────────────────────────
#         shared_transcript.append({
#             "sender": "User",
#             "content": user_query
#         })

#         # ── Orchestration Loop ────────────────────────────────────────────────
#         for round_num in range(self.max_rounds):
#             logger.info(f"\n{'='*50}\n[Round {round_num + 1}] Manager evaluating...\n{'='*50}")

#             next_speaker = self.manager.select_next_speaker(shared_transcript)

#             if next_speaker == "FINISH":
#                 logger.info("[Termination Engine] FINISH signalled.")
#                 break

#             system_role = AGENT_SYSTEM_PROMPTS.get(
#                 next_speaker,
#                 AGENT_SYSTEM_PROMPTS["Generalist_Agent"]
#             )
#             messages = [SystemMessage(content=system_role)]

#             for turn in shared_transcript:
#                 if turn["sender"] == "User":
#                     messages.append(HumanMessage(content=turn["content"]))
#                 else:
#                     messages.append(AIMessage(
#                         content=f"[{turn['sender']}]: {turn['content']}"
#                     ))

#             try:
#                 logger.info(f"[{next_speaker}] Generating response...")
#                 agent_response = self.llm.invoke(messages)
#                 output = agent_response.content.strip()

#                 shared_transcript.append({
#                     "sender": next_speaker,
#                     "content": output
#                 })
#                 logger.info(f"[{next_speaker}] Done.")

#             except Exception as e:
#                 logger.error(f"[{next_speaker}] Error: {e}")
#                 shared_transcript.append({
#                     "sender": next_speaker,
#                     "content": f"⚠️ Agent encountered an error: {e}"
#                 })
#                 break

#         return shared_transcript







"""
group_chat_engine.py
====================
Implements the Azure AI Agent Design Pattern: Group Chat Orchestration
Reference: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns

Architecture:
    User Query
        │
        ▼
  ┌─────────────────┐
  │  GroupChatManager│  ◄── reads shared transcript, picks next speaker or FINISH
  └────────┬────────┘
           │
  ┌────────┼────────┐
  ▼        ▼        ▼
Data    Weather  Generalist
Analyst  Agent    Agent
  │        │        │
  └────────┼────────┘
           ▼
    Shared Transcript
"""

import json
import logging
from typing import List, Dict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GroupChatEngine")


# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 1 — AGENT REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
AGENT_REGISTRY = {
    "Data_Analyst": (
        "Handles all requests about uploaded documents, PDFs, and text files. "
        "Specializes in summarization, quiz generation, key point extraction, "
        "and answering questions grounded in document content."
    ),
    "Weather_Agent": (
        "Handles all weather-related queries: current temperature, forecasts, "
        "humidity, wind, and climate for any city or region."
    ),
    "Generalist_Agent": (
        "Handles general conversation, greetings, math problems, and any "
        "question that does not involve documents or weather."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 2 — SPECIALIST SYSTEM PROMPTS
# ─────────────────────────────────────────────────────────────────────────────
AGENT_SYSTEM_PROMPTS = {
    "Data_Analyst": (
        "You are the Data Analyst Agent. Your only job is to analyze document "
        "content provided to you. Summarize clearly, generate quizzes with "
        "correct answers marked, or extract key points as bullet lists. "
        "Always base your answer strictly on the provided document context. "
        "Never make up information not present in the context."
    ),
    "Weather_Agent": (
        "You are the Weather Agent. Weather data has already been fetched and "
        "is provided in the conversation. Present it in a clean markdown table "
        "format with temperature, humidity, wind speed, and conditions clearly shown. "
        "Do NOT say you cannot access the internet — the data is already in the transcript."
    ),
    "Generalist_Agent": (
        "You are a friendly general-purpose assistant. Answer math questions "
        "step by step. Respond to greetings warmly. Handle any topic not "
        "covered by the other specialists. Be concise and helpful. "
        "You have access to the full conversation history — use it to answer "
        "follow-up questions and remember what was discussed earlier."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 3 — GROUP CHAT MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class GroupChatManager:
    def __init__(self, llm):
        self.llm = llm

    def select_next_speaker(self, transcript: List[Dict[str, str]]) -> str:
        """
        FIX 1 — TERMINATION BUG:
        We now check if a specialist already responded BEFORE asking the LLM.
        If any specialist agent already has a turn in the transcript, return FINISH immediately.
        This prevents the manager from calling a second or third agent turn.
        """
        specialist_names = set(AGENT_REGISTRY.keys())
        agents_who_spoke = [
            t["sender"] for t in transcript
            if t["sender"] in specialist_names
        ]

        # If any specialist has already responded → task is done → FINISH
        if agents_who_spoke:
            logger.info(f"[Manager] {agents_who_spoke[-1]} already responded → FINISH")
            return "FINISH"

        # No specialist has spoken yet — ask LLM to pick the right one
        formatted = "\n".join(
            f"[{msg['sender']}]: {msg['content'][:200]}" for msg in transcript
        )

        selector_prompt = f"""You are the Group Chat Manager. Read the conversation and select ONE agent.

AVAILABLE AGENTS:
{json.dumps(AGENT_REGISTRY, indent=2)}

RULES:
1. If the user asked about a document, PDF, file, summary, quiz, or key points → select: Data_Analyst
2. If the user asked about weather, temperature, forecast, or climate → select: Weather_Agent
3. For greetings, math, general questions, or anything else → select: Generalist_Agent
4. Return ONLY the agent name. No explanation. No punctuation.

CONVERSATION:
{formatted}

NEXT SPEAKER:"""

        try:
            response = self.llm.invoke([HumanMessage(content=selector_prompt)])
            speaker = response.content.strip().strip("'\"").strip()

            valid = set(AGENT_REGISTRY.keys())
            if speaker in valid:
                logger.info(f"[Manager] → Selected: {speaker}")
                return speaker

            for name in AGENT_REGISTRY:
                if name in speaker:
                    logger.info(f"[Manager] → Extracted: {name}")
                    return name

            logger.warning(f"[Manager] → Unrecognised '{speaker}', defaulting to Generalist_Agent")
            return "Generalist_Agent"

        except Exception as e:
            logger.error(f"[Manager] Selection error: {e}")
            return "Generalist_Agent"


# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 4 — GROUP CHAT ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
class GroupChatOrchestrator:
    def __init__(self, llm, max_rounds: int = 4):
        self.llm = llm
        self.manager = GroupChatManager(llm)
        self.max_rounds = max_rounds

    def run(
        self,
        user_query: str,
        doc_context: str = "",
        weather_data: str = "",
        chat_history: list = None,   # FIX 2 — MEMORY: accepts session history
    ) -> List[Dict[str, str]]:
        """
        FIX 2 — MEMORY BUG:
        chat_history (from st.session_state.chat_history) is now prepended
        to the shared transcript so agents can see prior conversation turns.
        """

        shared_transcript: List[Dict[str, str]] = []

        # ── Inject prior conversation memory as SYSTEM CONTEXT only ──────────
        # We do NOT add history as fake User/Assistant turns in the transcript.
        # Instead we summarise it into a single System context block so agents
        # can answer follow-up questions without replaying old answers.
        if chat_history:
            recent = chat_history[-8:]  # last 4 exchanges (user+assistant pairs)
            history_text = ""
            for turn in recent:
                role = "User" if turn["role"] == "user" else "Assistant"
                # Truncate long assistant responses to keep context lean
                content = turn["content"][:300] + "…" if len(turn["content"]) > 300 else turn["content"]
                history_text += f"{role}: {content}\n"

            if history_text.strip():
                shared_transcript.append({
                    "sender": "System_Conversation_Memory",
                    "content": (
                        "PRIOR CONVERSATION CONTEXT (for reference only — do NOT repeat these answers):\n\n"
                        + history_text
                    )
                })

        # ── Inject document context ───────────────────────────────────────────
        if doc_context:
            shared_transcript.append({
                "sender": "System_RAG_Context",
                "content": f"Relevant document content retrieved:\n\n{doc_context}"
            })

        # ── Inject pre-fetched weather data ───────────────────────────────────
        if weather_data:
            shared_transcript.append({
                "sender": "System_Weather_Feed",
                "content": f"Live weather data retrieved:\n\n{weather_data}"
            })

        # ── Add current user query ────────────────────────────────────────────
        shared_transcript.append({
            "sender": "User",
            "content": user_query
        })

        # ── Orchestration Loop ────────────────────────────────────────────────
        for round_num in range(self.max_rounds):
            logger.info(f"\n{'='*50}\n[Round {round_num + 1}] Manager evaluating...\n{'='*50}")

            next_speaker = self.manager.select_next_speaker(shared_transcript)

            if next_speaker == "FINISH":
                logger.info("[Termination Engine] FINISH signalled.")
                break

            system_role = AGENT_SYSTEM_PROMPTS.get(
                next_speaker,
                AGENT_SYSTEM_PROMPTS["Generalist_Agent"]
            )
            messages = [SystemMessage(content=system_role)]

            for turn in shared_transcript:
                if turn["sender"] == "User":
                    messages.append(HumanMessage(content=turn["content"]))
                else:
                    messages.append(AIMessage(
                        content=f"[{turn['sender']}]: {turn['content']}"
                    ))

            try:
                logger.info(f"[{next_speaker}] Generating response...")
                agent_response = self.llm.invoke(messages)
                output = agent_response.content.strip()

                shared_transcript.append({
                    "sender": next_speaker,
                    "content": output
                })
                logger.info(f"[{next_speaker}] Done.")

            except Exception as e:
                logger.error(f"[{next_speaker}] Error: {e}")
                shared_transcript.append({
                    "sender": next_speaker,
                    "content": f"⚠️ Agent encountered an error: {e}"
                })
                break

        return shared_transcript