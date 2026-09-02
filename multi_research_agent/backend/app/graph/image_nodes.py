from io import BytesIO
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from app.config import settings
from app.graph.state import (
    ChatState,
    GlobalImagePlan,
    ImageSubgraphState
)
from app.graph.llms import (
    google_llm,
    get_hf_client
)

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
    report = state.get("final_report", "")

    image_plan = planner_model.invoke([
        SystemMessage(content=DECIDE_IMAGES_SYSTEM),
        HumanMessage(content=(
            f"Research question:\n{state.get('question', '')}\n\n"
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
    client = get_hf_client()
    if not client:
        raise ValueError("HF_TOKEN is missing, cannot instantiate InferenceClient.")

    final_prompt = f"{IMAGE_SYSTEM_PROMPT}\n\nUSER IMAGE REQUEST:\n{prompt}\n"
    image = client.text_to_image(prompt=final_prompt, model=settings.IMAGE_MODEL)
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
        out_path = settings.IMAGES_DIR / filename

        try:
            if not out_path.exists():
                image_bytes = generate_image_bytes(spec["prompt"])
                out_path.write_bytes(image_bytes)

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
