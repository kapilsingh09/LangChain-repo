"""
Tavily Internet Search Integration Module for YouTube Researcher.

Provides intelligent, controlled web search to augment video transcript analysis
with real-world developer documentation, project repositories, and technical guides.
"""

import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from .prompts import TAVILY_QUERY_GENERATOR_PROMPT

logger = logging.getLogger("youtube_researcher.search")


def get_tavily_api_key() -> str:
    """
    Fetch TAVILY_API_KEY from environment or backend/.env file.
    Reloads .env dynamically to support runtime key configuration.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    key = os.getenv("TAVILY_API_KEY", "")
    return key.strip("'\" \t\r\n") if key else ""


def is_tavily_configured() -> bool:
    """Check if a non-empty Tavily API key is currently configured."""
    return bool(get_tavily_api_key())


def generate_search_query(llm, user_question: str, video_title: str = "") -> str:
    """
    Use LLM to generate an optimized, focused 3-6 word search query for Tavily
    based on the user's question and video title.
    """
    try:
        context_hint = f"Video Title: {video_title}\n" if video_title else ""
        prompt_text = f"{context_hint}User Request: {user_question}"
        
        response = llm.invoke(
            [
                SystemMessage(content=TAVILY_QUERY_GENERATOR_PROMPT),
                HumanMessage(content=prompt_text),
            ]
        )
        query = response.content.strip().strip('"\'`\n\r')
        # Sanity check: keep reasonable length
        if len(query.split()) > 10 or not query:
            return " ".join(user_question.split()[:7])
        return query
    except Exception as e:
        logger.warning(f"Failed to generate optimized Tavily query: {e}. Falling back to user question snippet.")
        return " ".join(user_question.split()[:7])


def search_tavily(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """
    Execute a web search using the Tavily Python client.
    Handles errors gracefully so search failures never crash the workflow.
    """
    api_key = get_tavily_api_key()
    if not api_key:
        logger.info("Tavily search skipped: TAVILY_API_KEY not configured in .env.")
        return []

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
            include_answer=False,
        )
        
        raw_results = response.get("results", [])
        formatted_results = []
        for r in raw_results:
            formatted_results.append(
                {
                    "title": r.get("title", "Reference"),
                    "url": r.get("url", ""),
                    "content": r.get("content", "").strip(),
                }
            )
        return formatted_results

    except Exception as e:
        logger.error(f"Tavily search error for query '{query}': {e}")
        return []


def format_web_context(results: List[Dict[str, str]], query_used: Optional[str] = None) -> str:
    """
    Format Tavily search results into a clean text block for injection into the prompt.
    """
    if not results:
        api_key = get_tavily_api_key()
        if not api_key:
            return (
                "Web search is currently disabled (TAVILY_API_KEY is not set in backend/.env).\n"
                "Synthesizing complete technical architecture and plan using video transcript and expert software knowledge."
            )
        return (
            f"Web search for '{query_used or 'query'}' returned no external hits.\n"
            "Synthesizing complete technical architecture and plan using video transcript and expert software knowledge."
        )

    lines = [f"### Web Search Results (Tavily Query: '{query_used}'):"]
    for idx, item in enumerate(results, start=1):
        lines.append(f"{idx}. **{item['title']}**")
        if item.get("url"):
            lines.append(f"   URL: {item['url']}")
        if item.get("content"):
            # Limit snippet size to avoid context bloat
            snippet = item['content'][:400].replace("\n", " ")
            lines.append(f"   Summary: {snippet}...")
        lines.append("")

    return "\n".join(lines)
