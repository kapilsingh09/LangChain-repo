import os
import re
import operator
from io import BytesIO
from pathlib import Path
from typing import List, TypedDict, Annotated, Literal, Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# LangChain / LangGraph imports
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver
from huggingface_hub import InferenceClient

# Base directories
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Environment variable extraction
HF_TOKEN = os.getenv("HF_TOKEN", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_API_KEY2 = os.getenv("GOOGLE_API_KEY2") or GOOGLE_API_KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")

IMAGES_DIR = BASE_DIR / "images"
REPORTS_DIR = BASE_DIR / "reports"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Helper function to normalize message content
def _content_to_str(content: Any) -> str:
    """Normalize LLM response.content (str or list of parts) to a plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", str(part)))
            else:
                parts.append(str(part))
        return " ".join(parts)
    return str(content)

# Initialize LLMs
def get_google_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=GOOGLE_API_KEY,
    )

def get_google_llm_secondary():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=GOOGLE_API_KEY2,
    )

def get_groq_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.2,
        max_retries=2,
        api_key=GROQ_API_KEY,
    )

google_llm = get_google_llm()
google_llm_secondary = get_google_llm_secondary()
groq_llm = get_groq_llm()

# Tavily Web Search Tool Setup
class WebSearchInput(BaseModel):
    queries: List[str] = Field(
        description="A list of web search queries to run."
    )

tavily_search = TavilySearch(
    max_results=5,
    topic="general",
    tavily_api_key=TAVILY_API_KEY
)

@tool(args_schema=WebSearchInput)
def web_search(queries: List[str]) -> str:
    """Search the web for current, missing, or detailed information."""
    all_results = []
    for query in queries:
        try:
            result = tavily_search.invoke({"query": query})
            all_results.append(f"Query: {query}\nResult: {result}")
        except Exception as e:
            all_results.append(f"Query: {query}\nError during search: {e}")
    return "\n\n---\n\n".join(all_results)

tools = [web_search]
research_llm = google_llm.bind_tools(tools)


# Graph State Definitions
class ChatState(TypedDict, total=False):
    question: str
    task: Optional[str]
    research_tropics_planned: List[str]
    research_results: Annotated[List[str], operator.add]
    collected_researchs: List[dict]
    critique: str
    final_report: str
    saved_file_path: str
    messages: Annotated[List[BaseMessage], operator.add]
    web_search_performed: Annotated[bool, operator.or_]
    md_with_placeholders: str
    image_specs: List[dict]


class PlannerState(TypedDict):
    research_tasks: List[str]


class CriticState(BaseModel):
    is_sufficient: bool
    key_strengths: list[str]
    missing_gaps: list[str]
    feedback_for_writer: str
    overall_score: int = Field(ge=0, le=10)


class ImageSpec(BaseModel):
    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Save under images/, e.g. qkv_flow.png")
    alt: str
    caption: str
    prompt: str = Field(..., description="Prompt to send to the image model.")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"


class GlobalImagePlan(BaseModel):
    md_with_placeholders: str
    images: List[ImageSpec] = Field(default_factory=list)


class ImageSubgraphState(TypedDict, total=False):
    question: str
    final_report: str
    md_with_placeholders: str
    image_specs: List[dict]


# Node Implementations
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

    content_str = _content_to_str(response.content)
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
        "collected_researchs": [{"text": _content_to_str(response.content)}]
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
        "final_report": _content_to_str(response.content)
    }


# Image Subgraph Nodes
DECIDE_IMAGES_SYSTEM = """You are an expert technical editor.

Decide whether images or diagrams are needed for THIS report.

Rules:
- Maximum 3 images.
- Only create images that materially improve understanding.
- Prefer technical diagrams, workflows, architecture diagrams, pipelines, comparisons, or conceptual visuals.
- Do NOT create decorative images.

Insert placeholders exactly:
[[IMAGE_1]]
[[IMAGE_2]]
[[IMAGE_3]]

If no images are needed:
md_with_placeholders must equal the input report and images must be [].

Return strictly GlobalImagePlan."""


def decide_images(state: ChatState) -> dict:
    planner_model = google_llm.with_structured_output(GlobalImagePlan)
    report = state["final_report"]

    image_plan = planner_model.invoke([
        SystemMessage(content=DECIDE_IMAGES_SYSTEM),
        HumanMessage(content=(
            f"Research question:\n{state['question']}\n\n"
            f"Final report:\n{report}\n\n"
            "Decide whether useful images are needed."
        ))
    ])

    return {
        "md_with_placeholders": image_plan.md_with_placeholders,
        "image_specs": [img.model_dump() for img in image_plan.images],
    }


IMAGE_SYSTEM_PROMPT = """You are an expert technical diagram and architecture illustrator.

Your job is to create accurate, professional, easy-to-read technical diagrams.

Rules:
- Follow the requested architecture exactly.
- Show clear relationships and data flow between components.
- Use short, readable labels.
- Keep the layout clean and logically organized.
- Use arrows to show direction of data or control flow.
- Use a professional documentation/technical-architecture style.
- Avoid unnecessary decorative elements.
- Do not invent components that were not requested.
- Do not change technical terminology.
- Prioritize technical accuracy and readability over artistic decoration."""


def generate_image_bytes(prompt: str) -> bytes:
    client = InferenceClient(api_key=HF_TOKEN, provider="auto")
    final_prompt = f"{IMAGE_SYSTEM_PROMPT}\n\nUSER IMAGE REQUEST:\n{prompt}\n"
    image = client.text_to_image(prompt=final_prompt, model="Qwen/Qwen-Image")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_and_place_images(state: ChatState) -> dict:
    md = state.get("md_with_placeholders") or state.get("final_report", "")
    image_specs = state.get("image_specs") or []

    if not image_specs:
        return {"final_report": md}

    for spec in image_specs:
        placeholder = spec["placeholder"]
        filename = spec["filename"]
        out_path = IMAGES_DIR / filename

        try:
            if not out_path.exists():
                if HF_TOKEN:
                    image_bytes = generate_image_bytes(spec["prompt"])
                    out_path.write_bytes(image_bytes)
                else:
                    raise ValueError("HF_TOKEN is missing, unable to generate image.")

            image_markdown = (
                f"![{spec['alt']}](/images/{filename})\n\n"
                f"*{spec['caption']}*"
            )
            md = md.replace(placeholder, image_markdown)

        except Exception as e:
            fallback = (
                f"\n\n> **Image generation failed for {filename}**\n"
                f"> Caption: {spec.get('caption', '')}\n"
                f"> Error: {e}\n"
            )
            md = md.replace(placeholder, fallback)

    return {"final_report": md}


def build_image_subgraph():
    image_graph = StateGraph(ImageSubgraphState)
    image_graph.add_node("decide_images", decide_images)
    image_graph.add_node("generate_images", generate_and_place_images)
    image_graph.add_edge(START, "decide_images")
    image_graph.add_edge("decide_images", "generate_images")
    image_graph.add_edge("generate_images", END)
    return image_graph.compile()


image_subgraph = build_image_subgraph()


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

    output_path = REPORTS_DIR / f"{safe_title}_report.md"
    output_path.write_text(final_saved_content, encoding="utf-8")

    return {
        "saved_file_path": str(output_path)
    }


# Assemble Main StateGraph
def build_research_graph():
    g = StateGraph(ChatState)

    # Nodes
    g.add_node("planner", planner)
    g.add_node("researcher", researcher)
    g.add_node("collector", collector)
    g.add_node("critic", critic)
    g.add_node("report_writer", report_writer)
    g.add_node("image_subgraph", image_subgraph)
    g.add_node("file_saver", file_saver)

    # Edges
    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", assign_tasks, ["researcher"])
    g.add_edge("researcher", "collector")
    g.add_edge("collector", "critic")
    g.add_edge("critic", "report_writer")
    g.add_edge("report_writer", "image_subgraph")
    g.add_edge("image_subgraph", "file_saver")
    g.add_edge("file_saver", END)

    checkpointer = InMemorySaver()
    return g.compile(checkpointer=checkpointer)


# Pre-compiled graph instance
workflow = build_research_graph()
