"""
collector.py — The Collector Agent.

WHAT IT DOES:
  After all parallel researchers finish, the collector reads ALL their
  raw findings and organizes them into a clean, structured summary.

  Specifically it:
    1. Deduplicates repeated information across the 3 researcher outputs
    2. Groups related facts into logical categories
    3. Keeps all key details intact (numbers, facts, references)

WHY THIS STEP EXISTS:
  3 parallel researchers often find overlapping information.
  The collector produces a clean, non-redundant body of evidence
  that the critic and report writer can then work with effectively.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GOOGLE_API_KEY2
from app.agents.state import ChatState
from app.agents.researcher import _content_to_str  # reuse the helper


# ── LLM setup ────────────────────────────────────────────────────────────────

# We use the secondary Google API key for the collector
# so it doesn't compete with the planner/researcher for rate limits.
_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=GOOGLE_API_KEY2,
)


# ── Prompt ───────────────────────────────────────────────────────────────────

_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an Evidence Collector agent.
Your job is to read all raw research findings gathered by multiple researchers and organize them.

Tasks:
1. Deduplicate repeating information across findings.
2. Group related facts into clear, logical categories.
3. Keep all key details, facts, numbers, and references intact.
4. Do NOT attempt to answer the user's original question directly or write the final report yet.

Focus purely on structuring and consolidating the evidence clearly.""",
    ),
    (
        "human",
        "User Question: {question}\n\nRaw Findings:\n{findings}",
    ),
])


# ── Agent function ────────────────────────────────────────────────────────────

def collector(state: ChatState) -> dict:
    """
    LangGraph node: Collector Agent.

    Reads:  state["research_results"]  (list of strings from all researchers)
            state["question"]
    Writes: state["collected_researchs"]  (list with one organized dict)
    """
    raw_results = state["research_results"]
    question = state["question"]

    # Format all findings with numbered labels for the LLM
    formatted_findings = "\n\n---\n\n".join(
        f"Finding {idx + 1}:\n{result}"
        for idx, result in enumerate(raw_results)
    )

    chain = _PROMPT | _llm
    response = chain.invoke({
        "question": question,
        "findings": formatted_findings,
    })

    # Wrap in a dict so the critic can access it by key
    return {
        "collected_researchs": [{"text": _content_to_str(response.content)}]
    }
