"""
models.py — Pydantic models for API request and response bodies.

Pydantic automatically:
  - Validates incoming JSON (type checking, required fields)
  - Converts Python objects to JSON for responses
  - Generates the OpenAPI docs at /docs

Think of these as "contracts" for what the API accepts and returns.
"""

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """
    What the user sends to the POST /research endpoint.

    Example JSON body:
        { "question": "How does transformer attention work?" }
    """

    question: str = Field(
        ...,                                    # "..." means this field is required
        min_length=10,                          # Security: reject empty/tiny queries
        max_length=1000,                        # Security: reject absurdly long input
        description="The research question you want the agents to investigate.",
        examples=["How does transformer attention work?"],
    )


class ResearchResponse(BaseModel):
    """
    What the API returns after completing the research pipeline.
    """

    question: str = Field(description="The original research question.")
    final_report: str = Field(description="The full markdown research report.")
    saved_file_path: str = Field(description="Path to the saved .md report file.")
    web_search_performed: bool = Field(
        description="Whether the agents used live web search."
    )
    critique: str = Field(
        description="The QA critic's evaluation of the research evidence."
    )
