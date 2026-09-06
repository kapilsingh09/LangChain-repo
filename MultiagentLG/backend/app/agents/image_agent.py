"""
image_agent.py — Image Decision + Image Generation Agents (as a subgraph).

WHAT IT DOES:
  This module contains two agents and builds them into a mini subgraph:

  1. decide_images  — Reads the final report and decides if images would help.
                      Inserts [[IMAGE_1]], [[IMAGE_2]], [[IMAGE_3]] placeholders.

  2. generate_and_place_images — Actually generates each image using HuggingFace
                                  and replaces the placeholders with markdown image tags.

WHY A SUBGRAPH?
  The image pipeline has its own internal state (ImageSubgraphState) that is
  isolated from ChatState. This keeps the main graph clean and lets us test
  the image pipeline independently.

IMAGE RULES:
  - Maximum 3 images per report.
  - Only create images that materially improve understanding.
  - Prefer technical diagrams, workflows, and architecture diagrams.
  - No decorative images.
"""

import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from huggingface_hub import InferenceClient
from langgraph.graph import StateGraph, START, END

from app.config import GOOGLE_API_KEY, HF_TOKEN
from app.agents.state import ChatState


# ── Subgraph State ────────────────────────────────────────────────────────────

class ImageSubgraphState(TypedDict):
    """
    Isolated state for the image subgraph.
    Only the fields the image pipeline needs — no overlap with ChatState clutter.
    """
    question: str
    final_report: str
    md_with_placeholders: str
    image_specs: List[dict]


# ── Structured output schemas ─────────────────────────────────────────────────

class ImageSpec(BaseModel):
    """Describes a single image to be generated."""

    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Save under images/, e.g. architecture.png")
    alt: str = Field(description="Alt text for the markdown image tag.")
    caption: str = Field(description="Caption displayed below the image.")
    prompt: str = Field(..., description="Prompt to send to the image generation model.")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"


class GlobalImagePlan(BaseModel):
    """The full image plan for the report."""
    md_with_placeholders: str = Field(description="Report with [[IMAGE_N]] placeholders inserted.")
    images: List[ImageSpec] = Field(default_factory=list)


# ── LLM setup ────────────────────────────────────────────────────────────────

_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=GOOGLE_API_KEY,
)

_DECIDE_SYSTEM = """You are an expert technical editor.

Decide whether images or diagrams are needed for THIS report.

Rules:
- Maximum 3 images.
- Only create images that materially improve understanding.
- Prefer technical diagrams, workflows, architecture diagrams,
  pipelines, comparisons, or conceptual visuals.
- Do NOT create decorative images.

Insert placeholders exactly:
[[IMAGE_1]]
[[IMAGE_2]]
[[IMAGE_3]]

If no images are needed:
md_with_placeholders must equal the input report
and images must be [].

Return strictly GlobalImagePlan."""


# ── Image generation helper ───────────────────────────────────────────────────

_IMAGE_STYLE_PREFIX = """You are an expert technical diagram and architecture illustrator.
Create accurate, professional, easy-to-read technical diagrams.
Use clear labels, arrows for data flow, and a clean layout.
Use a professional documentation/technical-architecture style.
Do not add unnecessary decorative elements.

USER IMAGE REQUEST:
"""


def _generate_image_bytes(prompt: str) -> bytes:
    """
    Call the HuggingFace Inference API to generate an image from a text prompt.
    Returns the raw PNG bytes.
    """
    client = InferenceClient(api_key=HF_TOKEN, provider="auto")
    full_prompt = _IMAGE_STYLE_PREFIX + prompt

    image = client.text_to_image(
        prompt=full_prompt,
        model="Qwen/Qwen-Image",
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


# ── Subgraph Node 1: decide_images ────────────────────────────────────────────

def decide_images(state: ImageSubgraphState) -> dict:
    """
    LangGraph node: Decide whether images are needed for this report.

    Reads:  state["final_report"], state["question"]
    Writes: state["md_with_placeholders"], state["image_specs"]
    """
    planner_llm = _llm.with_structured_output(GlobalImagePlan)
    report = state["final_report"]

    image_plan: GlobalImagePlan = planner_llm.invoke([
        SystemMessage(content=_DECIDE_SYSTEM),
        HumanMessage(
            content=(
                f"Research question:\n{state['question']}\n\n"
                f"Final report:\n{report}\n\n"
                "Decide whether useful images are needed."
            )
        ),
    ])

    return {
        "md_with_placeholders": image_plan.md_with_placeholders,
        "image_specs": [img.model_dump() for img in image_plan.images],
    }


# ── Subgraph Node 2: generate_and_place_images ────────────────────────────────

def generate_and_place_images(state: ImageSubgraphState) -> dict:
    """
    LangGraph node: Generate images and replace placeholders in the markdown.

    Reads:  state["md_with_placeholders"], state["image_specs"]
    Writes: state["final_report"]  (the final markdown with real image tags)
    """
    md = state.get("md_with_placeholders") or state["final_report"]
    image_specs = state.get("image_specs") or []

    # If no images were requested, just pass the report through unchanged
    if not image_specs:
        return {"final_report": md}

    # Create the images directory if it doesn't exist
    images_dir = Path("images").resolve()
    images_dir.mkdir(parents=True, exist_ok=True)

    for spec in image_specs:
        placeholder = spec["placeholder"]
        raw_name = Path(spec.get("filename", "")).name
        # Sanitize filename: alphanumeric, underscores, hyphens only
        base_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_name.rsplit(".", 1)[0]).strip("_")
        if not base_name:
            base_name = f"diag_{uuid.uuid4().hex[:8]}"
        safe_filename = f"{base_name}.png"

        out_path = (images_dir / safe_filename).resolve()
        # Enforce security invariant: out_path must stay strictly within images_dir
        if not str(out_path).startswith(str(images_dir)):
            print(f"⚠️ Security warning: rejected path traversal in image filename: {raw_name}")
            continue

        try:
            # Only generate if the file doesn't already exist
            if not out_path.exists():
                image_bytes = _generate_image_bytes(spec["prompt"])
                out_path.write_bytes(image_bytes)

            # Replace the [[IMAGE_N]] placeholder with a real markdown image tag pointing to /images/
            image_markdown = (
                f"![{spec.get('alt', 'Technical Diagram')}](/images/{safe_filename})\n\n"
                f"*{spec.get('caption', '')}*"
            )
            md = md.replace(placeholder, image_markdown)

        except Exception as e:
            # If generation fails, insert a visible warning instead of crashing
            print(f"⚠️  Image generation failed for {safe_filename}: {e}")
            fallback = (
                f"\n\n> **Image generation failed**\n"
                f"> {spec.get('caption', '')}\n"
                f"> Error: {e}\n"
            )
            md = md.replace(placeholder, fallback)

    return {"final_report": md}


# ── Build the image subgraph ──────────────────────────────────────────────────

def build_image_subgraph():
    """
    Compile the image pipeline into a reusable LangGraph subgraph.

    Flow: decide_images → generate_and_place_images
    """
    graph = StateGraph(ImageSubgraphState)
    graph.add_node("decide_images", decide_images)
    graph.add_node("generate_images", generate_and_place_images)
    graph.add_edge(START, "decide_images")
    graph.add_edge("decide_images", "generate_images")
    graph.add_edge("generate_images", END)
    return graph.compile()


# Compiled subgraph — imported by graph.py
image_subgraph = build_image_subgraph()
