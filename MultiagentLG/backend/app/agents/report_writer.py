"""
report_writer.py — The Report Writer Agent.

WHAT IT DOES:
  Takes the collected research evidence and the critic's feedback,
  then writes a detailed, professional markdown research report
  (approx. 1000-1500 words).

REPORT STRUCTURE:
  # Title
  ## Executive Summary
  ## 1. Introduction
  ## 2. Core Concepts
  ## 3. Detailed Analysis
  ## 4. Technical Workflow / Architecture
  ## 5. Practical Examples
  ## 6. Advantages and Limitations
  ## 7. Key Findings
  ## 8. Conclusion

WHY GROQ?
  The report writer uses Groq (fast inference) because writing a
  1000-1500 word report takes more tokens and we want it to be fast.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY
from app.agents.state import ChatState
from app.agents.researcher import _content_to_str  # reuse helper


# ── LLM setup ────────────────────────────────────────────────────────────────

_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    max_retries=2,
    api_key=GROQ_API_KEY,
)


# ── Prompt ───────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a Senior Technical Research Writer and Research Analyst.

Your job is to transform the provided research evidence and critic feedback
into a detailed, authoritative, well-structured Markdown research report.

IMPORTANT REPORT REQUIREMENTS:

1. LENGTH AND DEPTH
- Write a detailed report, not a short summary.
- Aim for approximately 1000-1500 words when sufficient evidence is available.
- Do not artificially repeat information just to increase length.
- Every section should provide useful technical information.
- Explain important concepts instead of merely mentioning them.

2. STRUCTURE
Use this structure when appropriate:

# [Clear Report Title]

## Executive Summary
Provide a concise overview of the main findings.

## 1. Introduction
Explain the topic and why it matters in the context of the user's question.

## 2. Core Concepts
Explain the fundamental concepts required to understand the topic.
Define important technical terms clearly.

## 3. Detailed Analysis
Break the main topic into logical subsections.
Explain each part thoroughly.

## 4. Technical Workflow / Architecture
If the topic involves a system, pipeline, architecture, or process,
explain the flow step-by-step.

## 5. Practical Examples
Give concrete examples wherever they improve understanding.

## 6. Advantages and Limitations
Discuss both strengths and weaknesses.

## 7. Key Findings
Summarize the most important findings from the research evidence.

## 8. Conclusion
Provide a clear conclusion directly answering the user's original question.

3. EVIDENCE USAGE
- Use the provided research evidence as the primary source.
- Do not invent research findings not supported by the evidence.
- If evidence is incomplete, explicitly state the limitation.

4. CRITIC FEEDBACK
- Carefully examine the critic feedback and fix identified gaps.
- Do not blindly copy the critique into the report.

5. WRITING STYLE
- Professional, technical, and clear.
- Use Markdown headings, bullets, numbered lists, tables, and bold text where useful.

6. FINAL ANSWER
The final output must contain ONLY the Markdown research report.
Do not include meta-commentary like "Here is your report" or "I hope this helps"."""


_HUMAN_PROMPT = """Original Research Question:
{question}

Quality Assurance Critique:
{critique}

Collected Research Evidence:
{evidence}

Now write the final detailed research report. Make sure it:
- Directly answers the original question.
- Is approximately 1000-1500 words when enough evidence is available.
- Incorporates the critic's feedback.
- Ends with a clear conclusion."""


_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("human", _HUMAN_PROMPT),
])


# ── Agent function ────────────────────────────────────────────────────────────

def report_writer(state: dict) -> dict:
    """
    LangGraph node: Report Writer Agent.

    Reads:  state["question"]
            state["collected_researchs"]
            state["critique"]
    Writes: state["final_report"]
    """
    question = state.get("question", "")
    critique = state.get("critique", "No critique provided.")

    # Get the most recent collected evidence
    evidence = (
        state.get("collected_researchs", [{}])[-1].get("text")
        or state.get("research_results", [""])[-1]
        or "No research evidence gathered."
    )

    # Normalize evidence to a string (could be list or dict in edge cases)
    if isinstance(evidence, list):
        formatted_evidence = "\n\n---\n\n".join(map(str, evidence))
    else:
        formatted_evidence = str(evidence)

    chain = _PROMPT | _llm
    response = chain.invoke({
        "question": question,
        "critique": critique,
        "evidence": formatted_evidence,
    })

    return {"final_report": _content_to_str(response.content)}
