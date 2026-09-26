from typing import Annotated, TypedDict, Literal
import operator
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document


class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

    # The YouTube video ID — set at the start of each request
    video_id: str

    decision_route: Literal["chat", "go_for_rag"]

    documents: list[Document]

    grade: dict

    web_search_needed: bool

    web_results: list[dict]

    context: str

    rewritten_query: str

    retry_count: int