from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from app.config import settings
from app.graph.llms import google_llm


class WebSearchInput(BaseModel):
    queries: List[str] = Field(
        description="A list of web search queries to run."
    )


tavily_search = TavilySearch(
    max_results=5,
    topic="general",
    tavily_api_key=settings.TAVILY_API_KEY
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
