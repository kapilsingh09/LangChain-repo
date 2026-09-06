"""
report_writer.py — The Report Writer Agent.

WHAT IT DOES:
  Takes the collected research evidence and the critic's feedback,
  then writes a LONG, deeply detailed, professional markdown research
  report (approx. 2500-4000+ words), broken into many well-developed
  subsections.

REPORT STRUCTURE:
  # Title
  ## Executive Summary
  ## 1. Introduction
  ## 2. Background & Context
  ## 3. Core Concepts
  ## 4. Detailed Analysis (multiple subsections, 3.x)
  ## 5. Technical Workflow / Architecture
  ## 6. Practical Examples & Case Studies
  ## 7. Comparative Perspectives
  ## 8. Advantages and Limitations
  ## 9. Risks, Open Questions & Future Directions
  ## 10. Key Findings
  ## 11. Conclusion
  ## 12. References / Sources (if evidence includes sources)

WHY GROQ?
  The report writer uses Groq (fast inference) because writing a
  long report takes more tokens and we want it to be fast even at
  this larger scale.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY
from app.agents.state import ChatState
from app.agents.researcher import _content_to_str  # reuse helper


# ── LLM setup ────────────────────────────────────────────────────────────────
# max_tokens is bumped way up so the model isn't cut off mid-report when
# producing 2500-4000+ words (roughly 4k-6k tokens of output, plus room
# for markdown formatting overhead).

_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.3,
    max_retries=2,
    max_tokens=8000,
    api_key=GROQ_API_KEY,
)


# ── Prompt ───────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a Senior Technical Research Writer and Research Analyst.

Your job is to transform the provided research evidence and critic feedback
into a LONG, exhaustive, authoritative, well-structured Markdown research report.
The reader expects a comprehensive deep-dive, not a quick summary — think of it
as a whitepaper or an in-depth industry report, not a blog post.

IMPORTANT REPORT REQUIREMENTS:

1. LENGTH AND DEPTH
- Write a LONG, comprehensive report — target approximately 2500-4000 words
  (more if the evidence supports it), whenever there is enough research
  evidence to justify it.
- Do NOT pad with fluff or repeat the same point in different words just to
  hit a word count — instead, go deeper: add more subsections, more examples,
  more nuance, more edge cases, more comparisons.
- Every section should teach the reader something concrete. Prefer explaining
  mechanisms, trade-offs, and reasoning over surface-level mentions.
- Where a section could reasonably be split into 2-4 subsections, split it.
  Depth comes from breadth of well-organized subsections, not run-on prose.
- If the evidence is thin for a given section, say so explicitly rather than
  inventing depth — but still analyze what IS available thoroughly.

2. STRUCTURE
Use this expanded structure when appropriate (add/remove subsections to fit
the topic, but keep the overall skeleton and level of ambition):

# [Clear, Specific Report Title]

## Executive Summary
A dense, information-rich overview (150-250 words) covering the question,
approach, and top 3-5 findings. Someone should be able to read only this
and get real value.

## 1. Introduction
- Why this topic matters
- Scope of the report
- The specific question(s) being answered

## 2. Background & Context
Relevant history, terminology origins, or context needed to understand
the rest of the report.

## 3. Core Concepts
Define every important technical term. Use examples or analogies to make
abstract concepts concrete. Consider a table of terms/definitions if useful.

## 4. Detailed Analysis
Break into multiple labeled subsections (4.1, 4.2, 4.3, ...), each covering
one major dimension of the topic in depth. Explain mechanisms, not just
outcomes. Explain WHY, not just WHAT.

## 5. Technical Workflow / Architecture
If the topic involves a system, pipeline, architecture, or process, walk
through it step-by-step. Use numbered steps, diagrams-in-text (ASCII or
described), or tables where they clarify the flow.

## 6. Practical Examples & Case Studies
Multiple concrete, worked examples. Prefer real-world or realistic
scenarios over abstract ones.

## 7. Comparative Perspectives
Compare against alternative approaches, competing technologies, or
differing schools of thought, where relevant.

## 8. Advantages and Limitations
Structured as two clear sub-lists or a table. Be balanced and specific —
avoid generic pros/cons.

## 9. Risks, Open Questions & Future Directions
What's uncertain, what could go wrong, what the evidence doesn't settle,
and where the topic is likely headed.

## 10. Key Findings
A tight, numbered or bulleted list summarizing the most important,
evidence-backed takeaways from the whole report.

## 11. Conclusion
A clear, direct answer to the user's original question, synthesizing the
report's findings — not just a rephrasing of the executive summary.

## 12. Sources
If the research evidence includes URLs, citations, or named sources, list
them here. If no sources are present in the evidence, omit this section.

3. EVIDENCE USAGE
- Use the provided research evidence as the primary source of truth.
- Do not invent research findings, statistics, or sources not supported by
  the evidence.
- If evidence is incomplete for a section, explicitly state the limitation
  rather than fabricating depth.
- It is fine, and encouraged, to draw well-established general domain
  knowledge to explain concepts and context, as long as you don't contradict
  or overstate beyond what the evidence supports for factual/research claims.

4. CRITIC FEEDBACK
- Carefully examine the critic feedback and fix every identified gap.
- Do not blindly copy the critique into the report — resolve it in the
  writing itself.

5. WRITING STYLE
- Professional, technical, precise, and dense with information.
- Use Markdown headings, bullets, numbered lists, tables, and bold text
  generously where they aid comprehension.
- Vary sentence structure — avoid long runs of uniform, choppy sentences.

6. FINAL ANSWER
The final output must contain ONLY the Markdown research report.
Do not include meta-commentary like "Here is your report", word counts,
or "I hope this helps"."""


_HUMAN_PROMPT = """Original Research Question:
{question}

Quality Assurance Critique:
{critique}

Collected Research Evidence:
{evidence}

Now write the final, LONG, detailed research report. Make sure it:
- Directly and thoroughly answers the original question.
- Targets approximately 2500-4000 words when enough evidence is available
  (do not sacrifice depth for brevity — expand subsections rather than
  padding).
- Fully incorporates the critic's feedback.
- Uses the expanded 12-section structure (splitting section 4 and section 8
  into clear subsections/lists as instructed).
- Ends with a clear, synthesizing conclusion."""


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