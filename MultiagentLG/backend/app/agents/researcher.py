"""
researcher.py — The Researcher Agent + Web Search Tool.

WHAT IT DOES:
  Each researcher receives one specific research task and gathers
  detailed information about it. It can optionally search the web
  using the Tavily search API when it needs current or external info.

HOW PARALLEL RESEARCH WORKS:
  The graph uses LangGraph's "Send" API to spawn one researcher per
  task from the planner. They all run independently and their results
  are merged into research_results via operator.add (see state.py).

HOW THE TOOL LOOP WORKS:
  1. Send the task to the LLM (which has web_search bound to it)
  2. If the LLM decides to call web_search → execute it, add results to messages
  3. Send the updated messages back to the LLM for a final answer
  4. Return the text content as a research finding
"""

from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch

from app.config import GOOGLE_API_KEY, TAVILY_API_KEY
from app.agents.state import ChatState


# ── Web Search Tool ───────────────────────────────────────────────────────────

class WebSearchInput(BaseModel):
    """Schema for the web_search tool's arguments."""
    queries: List[str] = Field(description="A list of web search queries to run.")


# The actual Tavily search client (max 5 results per query)
_tavily_client = TavilySearch(
    max_results=5,
    topic="general",
    tavily_api_key=TAVILY_API_KEY,
)


@tool(args_schema=WebSearchInput)
def web_search(queries: List[str]) -> str:
    """Search the web for current, missing, or detailed information."""
    all_results = []
    for query in queries:
        try:
            result = _tavily_client.invoke({"query": query})
            all_results.append(f"Query: {query}\nResult: {result}")
        except Exception as e:
            # Don't crash the whole agent if one query fails
            all_results.append(f"Query: {query}\nError: {e}")
    return "\n\n---\n\n".join(all_results)


# ── LLM setup ────────────────────────────────────────────────────────────────

_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    api_key=GOOGLE_API_KEY,
)

# Bind the web_search tool so the LLM can call it when needed
_research_llm = _llm.bind_tools([web_search])

# List of available tools — used for dispatching tool calls below
_TOOLS = {web_search.name: web_search}


# ── Helper ────────────────────────────────────────────────────────────────────

def _content_to_str(content) -> str:
    """
    Normalize LLM response content to a plain string.

    Gemini sometimes returns a list of content parts instead of a plain string.
    This function handles both cases so we always get a string.
    """
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


# ── Agent function ────────────────────────────────────────────────────────────

def researcher(state: ChatState) -> dict:
    """
    LangGraph node: Researcher Agent.

    This node is spawned in parallel for each research task.
    Each instance receives a different "task" in its state.

    Reads:  state["task"] (injected by assign_tasks via Send)
            OR state["question"] as fallback
    Writes: state["research_results"] (appended via operator.add)
            state["web_search_performed"] (merged via operator.or_)
    """
    # "task" is injected by the Send() call in graph.py
    # We fall back to the original question if needed
    task = state.get("task") or state.get("question") or "Research topic"

    messages = [
        SystemMessage(
            content=(
                "You are an expert research agent.\n"
                "Research ONLY the provided research task.\n"
                "Use web_search when current or external information is required.\n"
                "When enough information is available, provide a highly detailed, "
                "comprehensive, and lengthy research finding. Extract all key details, "
                "examples, and data. Do not summarize briefly."
            )
        ),
        HumanMessage(content=f"Research task:\n{task}"),
    ]

    # First LLM call — may return tool calls or a direct answer
    response = _research_llm.invoke(messages)
    web_search_performed = False

    # If the LLM wants to use tools, execute them and call the LLM again
    if response.tool_calls:
        web_search_performed = True
        messages.append(response)  # Add the LLM's tool-call request to history

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_fn = _TOOLS.get(tool_name)

            if tool_fn:
                try:
                    tool_output = tool_fn.invoke(tool_call["args"])
                except Exception as e:
                    tool_output = f"Tool error: {e}"
            else:
                tool_output = f"Unknown tool: {tool_name}"

            # Add the tool result to the message history
            messages.append(
                ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"],
                )
            )

        # Second LLM call — now has access to the web search results
        response = _research_llm.invoke(messages)

    content_str = _content_to_str(response.content)

    return {
        # operator.add in state.py means this gets APPENDED to the list
        "research_results": [content_str] if content_str else [],
        # operator.or_ means True if any researcher searched
        "web_search_performed": web_search_performed,
    }
