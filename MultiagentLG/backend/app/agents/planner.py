"""
planner.py — The Planner Agent.

WHAT IT DOES:
  Takes the user's research question and breaks it into exactly 3
  clear, specific, independent research sub-tasks.

WHY IT EXISTS:
  A single LLM call on a complex question often gives shallow results.
  By breaking the question into 3 focused tasks, we can run 3 specialized
  researchers in parallel — each going deep on one aspect.

HOW IT WORKS:
  1. Receives the full ChatState (reads: question)
  2. Sends the question to Gemini with a structured output schema
  3. Gets back a dict with {"research_tasks": ["task1", "task2", "task3"]}
  4. Returns {"research_tropics_planned": [...]} to update the state
"""

from typing import List
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GOOGLE_API_KEY
from app.agents.state import ChatState


# ── LLM setup ────────────────────────────────────────────────────────────────

# We use Google Gemini as the planner LLM.
# "with_structured_output" tells the LLM to return JSON matching PlannerOutput.
_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=GOOGLE_API_KEY,
)


# ── Structured output schema ──────────────────────────────────────────────────

class PlannerOutput(TypedDict):
    """The structured JSON the LLM must return."""
    research_tasks: List[str]


# ── Prompt ───────────────────────────────────────────────────────────────────

_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert research planning agent.

Break the user's research question into exactly 3 clear,
specific, independent research tasks.

Rules:
- Each task must investigate a different aspect of the question.
- Tasks must be specific enough for a researcher to execute.
- Avoid overlapping tasks.
- Do not answer the user's question.
- Return only the research tasks.""",
    ),
    ("human", "{question}"),
])


# ── Agent function ────────────────────────────────────────────────────────────

def planner(state: ChatState) -> dict:
    """
    LangGraph node: Planner Agent.

    Reads:  state["question"]
    Writes: state["research_tropics_planned"]
    """
    question = state["question"]

    # Chain: prompt → LLM → structured JSON output
    chain = _PROMPT | _llm.with_structured_output(PlannerOutput)

    response = chain.invoke({"question": question})

    tasks = response.get("research_tasks", [])

    # Safety check: if the LLM returns nothing, fail loudly
    if not tasks:
        raise ValueError(
            "Planner returned no research tasks. "
            "Check your GOOGLE_API_KEY and model name."
        )

    # Return only the first 3 tasks (in case LLM returns more)
    return {"research_tropics_planned": tasks[:3]}
