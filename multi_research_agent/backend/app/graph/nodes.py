import re
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Send

from app.config import settings
from app.graph.state import (
    ChatState,
    PlannerState,
    CriticState
)
from app.graph.llms import (
    google_llm,
    google_llm_secondary,
    groq_llm,
    content_to_str
)
from app.graph.tools import (
    research_llm,
    web_search
)


def planner(state: ChatState) -> dict:
    question = state["question"]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert research planning agent.

Break the user's research question into exactly 3 clear, specific, independent research tasks.

Rules:
- Each task must investigate a different aspect of the question.
- Tasks must be specific enough for a researcher to execute.
- Avoid overlapping tasks.
- Do not answer the user's question.
- Return only the research tasks."""
        ),
        (
            "human",
            "{question}"
        )
    ])

    planner_chain = prompt | google_llm.with_structured_output(PlannerState)
    response = planner_chain.invoke({"question": question})
    tasks = response.get("research_tasks", [])

    if not tasks:
        raise ValueError("Planner returned no research tasks.")

    return {
        "research_tropics_planned": tasks[:3]
    }


def assign_tasks(state: ChatState):
    topics = state.get("research_tropics_planned") or []
    return [
        Send("researcher", {"task": topic, "question": state.get("question")})
        for topic in topics
    ]


def researcher(state: ChatState) -> dict:
    task = state.get("task") or state.get("question") or "Research topic"

    messages = [
        SystemMessage(
            content=(
                "You are an expert research agent.\n"
                "Research ONLY the provided research task.\n"
                "Use web_search when current or external information is required.\n"
                "When enough information is available, provide a highly detailed, comprehensive, and lengthy research finding. Extract all key details, examples, and data. Do not summarize briefly."
            )
        ),
        HumanMessage(content=f"Research task:\n{task}")
    ]

    response = research_llm.invoke(messages)
    web_search_performed = False

    if response.tool_calls:
        web_search_performed = True
        messages.append(response)

        for tool_call in response.tool_calls:
            if tool_call["name"] == "web_search":
                tool_output = web_search.invoke(tool_call["args"])
                messages.append(ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"]
                ))

        response = research_llm.invoke(messages)

    content_str = content_to_str(response.content)
    return {
        "research_results": [content_str] if content_str else [],
        "web_search_performed": web_search_performed,
    }


def collector(state: ChatState) -> dict:
    raw_results = state.get("research_results", [])
    question = state["question"]

    formatted_findings = "\n\n---\n\n".join(
        f"Finding {idx + 1}:\n{result}"
        for idx, result in enumerate(raw_results)
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an Evidence Collector agent.
Your job is to read all raw research findings gathered by multiple researchers and organize them.

Tasks:
1. Deduplicate repeating information across findings.
2. Group related facts into clear, logical categories.
3. Keep all key details, facts, numbers, and references intact.
4. Do NOT attempt to answer the user's original question directly or write the final report yet.

Focus purely on structuring and consolidating the evidence clearly."""
        ),
        (
            "human",
            "User Question: {question}\n\nRaw Findings:\n{findings}"
        )
    ])

    collector_chain = prompt | google_llm_secondary
    response = collector_chain.invoke({
        "question": question,
        "findings": formatted_findings
    })

    return {
        "collected_researchs": [{"text": content_to_str(response.content)}]
    }


def critic(state: ChatState) -> dict:
    question = state["question"]
    evidence = state.get("collected_researchs", [])
    evidence_text = "\n\n".join(item.get("text", "") for item in evidence)

    prompt = ChatPromptTemplate.from_messages([
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

Set is_sufficient=True only if the main question is answered and there are no major gaps.
Generally, this requires a score >= 7.

Be critical and concise.
Do not invent information."""
        ),
        (
            "human",
            "Question:\n\n{question}\n\nEvidence:\n\n{evidence}"
        )
    ])

    critic_chain = prompt | google_llm.with_structured_output(CriticState)
    response = critic_chain.invoke({
        "question": question,
        "evidence": evidence_text
    })

    key_strengths = "\n- ".join(response.key_strengths) if response.key_strengths else "None"
    missing_gaps = "\n- ".join(response.missing_gaps) if response.missing_gaps else "None"

    formatted_critique = f"""Sufficient Evidence: {response.is_sufficient}

Overall Score: {response.overall_score}/10

Key Strengths:
- {key_strengths}

Missing Gaps:
- {missing_gaps}

Feedback for Report Writer:
{response.feedback_for_writer}""".strip()

    return {
        "critique": formatted_critique
    }


def report_writer(state: dict) -> dict:
    question = state.get("question", "")

    evidence = (
        state.get("collected_researchs", [{}])[-1].get("text")
        or (state.get("research_results", [""])[-1] if state.get("research_results") else "")
        or "No research evidence gathered."
    )

    critique = state.get("critique", "No critique provided.")

    if isinstance(evidence, list):
        formatted_evidence = "\n\n---\n\n".join(map(str, evidence))
    else:
        formatted_evidence = str(evidence)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a Senior Technical Research Writer and Research Analyst.

Your job is to transform the provided research evidence and critic feedback into a detailed, authoritative, well-structured Markdown research report.

IMPORTANT REPORT REQUIREMENTS:
1. LENGTH AND DEPTH: Write a detailed report (~1000–1500 words when sufficient evidence is available).
2. STRUCTURE: Include Title, Executive Summary, Introduction, Core Concepts, Detailed Analysis, Technical Workflow / Architecture, Practical Examples, Advantages and Limitations, Key Findings, and Conclusion.
3. EVIDENCE USAGE: Use the provided evidence thoroughly and accurately.
4. CRITIC FEEDBACK: Fix gaps identified by the critic.
5. WRITING STYLE: Technical, professional, clear.
6. FINAL ANSWER: Return ONLY the Markdown report without meta commentary."""
        ),
        (
            "human",
            """Original Research Question:
{question}

Quality Assurance Critique:
{critique}

Collected Research Evidence:
{evidence}

Now write the final detailed research report."""
        )
    ])

    writer_chain = prompt | groq_llm
    response = writer_chain.invoke({
        "question": question,
        "critique": critique,
        "evidence": formatted_evidence
    })

    return {
        "final_report": content_to_str(response.content)
    }


def file_saver(state: ChatState) -> dict:
    report_content = state.get("final_report", "")
    question = state.get("question", "research_report")

    if isinstance(question, dict):
        question = question.get("question") or question.get("text") or str(question)
    question = str(question)

    if isinstance(report_content, list):
        report_content = "\n\n".join(
            str(item.get("text", item) if isinstance(item, dict) else item)
            for item in report_content
        )
    elif isinstance(report_content, dict):
        report_content = report_content.get("text", str(report_content))
    else:
        report_content = str(report_content)

    warning_banner = (
        "> ⚠️ **AI Disclaimer & Warning:**\n"
        "> This report was autonomously generated by an AI research assistant. "
        "AI models can make mistakes, hallucinate details, or generate inaccurate, "
        "outdated, or unnecessary content. Please independently verify critical facts, "
        "citations, and technical claims before relying on this document.\n\n---\n\n"
    )

    final_saved_content = warning_banner + report_content

    safe_title = re.sub(r"[^a-zA-Z0-9]+", "_", question.strip().lower())
    safe_title = re.sub(r"_+", "_", safe_title).strip("_")
    safe_title = safe_title[:50].rstrip("_")

    if not safe_title:
        safe_title = "research_report"

    output_path = settings.REPORTS_DIR / f"{safe_title}_report.md"
    output_path.write_text(final_saved_content, encoding="utf-8")

    return {
        "saved_file_path": str(output_path)
    }
