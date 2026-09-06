"""
critic.py — The Critic (QA) Agent.

WHAT IT DOES:
  Evaluates the quality of the collected research evidence
  against the original user question. Scores it 0-10 and
  identifies what's strong and what's missing.

WHY THIS STEP EXISTS:
  Without a quality check, the report writer might produce a report
  based on weak or incomplete evidence. The critic's feedback tells
  the writer where to add more depth and what gaps to acknowledge.

SCORING:
  0-2  = Very poor
  3-4  = Major gaps
  5-6  = Moderate quality
  7-8  = Strong evidence
  9-10 = Comprehensive

  is_sufficient=True only if score >= 7 and main question is answered.
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GOOGLE_API_KEY
from app.agents.state import ChatState


# ── LLM setup ────────────────────────────────────────────────────────────────

_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=GOOGLE_API_KEY,
)


# ── Structured output schema ──────────────────────────────────────────────────

class CriticOutput(BaseModel):
    """Structured response from the critic LLM."""

    is_sufficient: bool = Field(
        description="True if the evidence sufficiently answers the question (score >= 7)."
    )
    key_strengths: list[str] = Field(
        description="List of what the evidence does well."
    )
    missing_gaps: list[str] = Field(
        description="List of important missing information or weaknesses."
    )
    feedback_for_writer: str = Field(
        description="Specific guidance for the report writer to improve the final report."
    )
    overall_score: int = Field(
        ge=0,   # must be >= 0
        le=10,  # must be <= 10
        description="Quality score from 0 (very poor) to 10 (comprehensive).",
    )


# ── Prompt ───────────────────────────────────────────────────────────────────

_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a QA critic for a deep research system.

Evaluate the evidence ONLY against the user's question.
Do not add facts or use outside knowledge.

Check:
- Relevance
- Completeness
- Quality
- Consistency
- Clarity

Score 0-10:
0-2 = very poor
3-4 = major gaps
5-6 = moderate
7-8 = strong
9-10 = comprehensive

Set is_sufficient=True only if the main question
is answered and there are no major gaps.

Generally, this requires a score >= 7.

Be critical and concise.
Do not invent information.""",
    ),
    (
        "human",
        "Question:\n\n{question}\n\nEvidence:\n\n{evidence}",
    ),
])


# ── Agent function ────────────────────────────────────────────────────────────

def critic(state: ChatState) -> dict:
    """
    LangGraph node: Critic Agent.

    Reads:  state["question"]
            state["collected_researchs"]
    Writes: state["critique"]
    """
    question = state["question"]

    # Pull the organized evidence text from the collector's output
    evidence_items = state["collected_researchs"]
    evidence_text = "\n\n".join(item["text"] for item in evidence_items)

    chain = _PROMPT | _llm.with_structured_output(CriticOutput)
    response: CriticOutput = chain.invoke({
        "question": question,
        "evidence": evidence_text,
    })

    # Format strengths and gaps as bullet lists (or "None" if empty)
    key_strengths = (
        "\n- ".join(response.key_strengths)
        if response.key_strengths
        else "None"
    )
    missing_gaps = (
        "\n- ".join(response.missing_gaps)
        if response.missing_gaps
        else "None"
    )

    # Build a human-readable critique string for the report writer
    formatted_critique = f"""Sufficient Evidence: {response.is_sufficient}

Overall Score: {response.overall_score}/10

Key Strengths:
- {key_strengths}

Missing Gaps:
- {missing_gaps}

Feedback for Report Writer:
{response.feedback_for_writer}""".strip()

    return {"critique": formatted_critique}
