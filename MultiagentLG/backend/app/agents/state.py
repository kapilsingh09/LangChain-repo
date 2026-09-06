"""
state.py — The shared "memory" that all agents read from and write to.

In LangGraph, every node (agent) receives the current state as input
and returns a dict of updates to that state.

Think of ChatState like a whiteboard in a team meeting —
everyone can read what's on it, and each person can add their part.
"""

import operator
from typing import List, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class ChatState(TypedDict):
    """
    The full state passed between all agents in the research graph.

    Each field is written by a specific agent:
      - question          → set by the user (API input)
      - research_tropics_planned → planner agent
      - research_results  → researcher agents (parallel, merged with operator.add)
      - collected_researchs → collector agent
      - critique          → critic agent
      - final_report      → report_writer agent, then image_agent
      - saved_file_path   → file_saver agent
      - messages          → researcher agents (tool call logs)
      - web_search_performed → researcher agents (merged with operator.or_)
      - md_with_placeholders → image_agent (report with [[IMAGE_N]] slots)
      - image_specs       → image_agent (list of image generation instructions)
    """

    # The original user question — never changes after being set.
    question: str

    # The 3 research tasks the planner breaks the question into.
    research_tropics_planned: List[str]

    # Research findings from each parallel researcher.
    # operator.add merges lists — so all researchers' findings accumulate here.
    research_results: Annotated[List[str], operator.add]

    # Organized and deduplicated findings from the collector agent.
    collected_researchs: List[dict]

    # Quality assessment from the critic agent (score + feedback).
    critique: str

    # The final markdown research report.
    final_report: str

    # Path to the saved .md file on disk.
    saved_file_path: str

    # LangChain message history (used by the researcher's tool calls).
    # operator.add means each researcher appends their messages.
    messages: Annotated[List[BaseMessage], operator.add]

    # Did any researcher perform a live web search?
    # operator.or_ means: True if ANY researcher searched the web.
    web_search_performed: Annotated[bool, operator.or_]

    # The final report with [[IMAGE_1]], [[IMAGE_2]] placeholders inserted.
    md_with_placeholders: str

    # List of dicts describing each image to generate and where to insert it.
    image_specs: List[dict]
