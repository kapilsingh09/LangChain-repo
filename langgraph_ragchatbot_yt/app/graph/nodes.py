
from pydantic import BaseModel, Field
from typing import Literal

from langgraph_ragchatbot_yt.app.rag import retriever
from llm.models import groq_llm,google_llm
from graph.state import GraphState
from tavily import TavilyClient
import os

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

class RouteDecision(BaseModel):
    decision_route: Literal["chat", "go_for_rag"]

router_llm = groq_llm.with_structured_output(RouteDecision)

def make_decision_route(state: GraphState):

    question = state["messages"][-1].content

    prompt = f"""
You are a routing agent for a YouTube RAG chatbot.

Your job is to decide whether the user's message should be handled as normal conversation or answered using information from the YouTube video/transcript.

Return ONLY one of these two values:

chat
go_for_rag

### Use "chat" when:

The user is having normal conversation or casual interaction that does not require information from the video.

Examples:

* "Hi"
* "Hello"
* "How are you?"
* "Thanks"
* "Okay"
* "Bye"
* "What can you do?"

### Use "go_for_rag" when:

The user asks anything that is related to, based on, or could be answered using information from the YouTube video/transcript.

This includes:

* Asking about a concept or topic explained in the video
* Asking for an explanation of something discussed in the video
* Asking what the speaker said or explained
* Asking for a summary of the video or a part of it
* Asking about examples mentioned in the video
* Asking why or how something works when it is discussed in the video
* Asking about specific people, technologies, ideas, terms, or topics mentioned in the video
* Asking follow-up questions about something previously discussed from the video
* Asking questions that require understanding the video's content

Examples:
"What is self-supervised learning?"
→ go_for_rag

"Explain what the video says about LLMs."
→ go_for_rag

"What examples of self-supervised learning were mentioned?"
→ go_for_rag

"Why is self-supervised learning useful?"
→ go_for_rag

"Can you summarize this video?"
→ go_for_rag

"What did the speaker say about transformers?"
→ go_for_rag

"If the video discusses RAG, explain how it works."
→ go_for_rag

### Important:

If the question could reasonably require information from the YouTube video, choose "go_for_rag".

When you are unsure whether the question is casual conversation or requires video information, choose "go_for_rag".

Do not answer the user's question. Only classify it.

User message:
{state["messages"][-1].content}

Return ONLY:
chat
OR
go_for_rag

"""

    response = groq_llm.invoke(prompt)

    decision = response.content.strip().lower()

    if decision not in ["chat", "go_for_rag"]:
        decision = "go_for_rag"

    return {"decision_route": decision}


def chat_node(state: GraphState):

    response = google_llm.invoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }


class ContextGrade(BaseModel):

    relevance: int = Field(
        description="How relevant the retrieved context is to the question. Score 0-10."
    )

    completeness: int = Field(
        description="How completely the context answers the question. Score 0-10."
    )

    specificity: int = Field(
        description="How specifically the context addresses the exact question. Score 0-10."
    )

    confidence: int = Field(
        description="How confident we can be that the context supports a correct answer. Score 0-10."
    )

    action: Literal[
        "generate",
        "rewrite_query",
        "web_search"
    ] = Field(
        description="Corrective action to take based on the retrieved context."
    )

    reason: str = Field(
        description="Short explanation for the grading decision."
    )


grader_llm = google_llm.with_structured_output(ContextGrade)

def grade_documents(state: GraphState):

    question = state["messages"][-1].content

    documents = state.get("documents", [])

    context = "\n\n".join(
        doc.page_content
        for doc in documents
    )

    prompt = f"""
You are the corrective grading agent in a YouTube C-RAG system.

Your job is to evaluate whether the retrieved YouTube transcript
is good enough to answer the user's question.

Score:

1. relevance: 0-10
2. completeness: 0-10
3. specificity: 0-10
4. confidence: 0-10

Then choose exactly ONE action:

generate
rewrite_query
web_search


Use "generate" when:
- The transcript is relevant.
- The transcript contains enough information.
- The answer can be safely generated from the transcript.

Use "rewrite_query" when:
- The retrieved documents are poorly relevant.
- The retrieval query appears to have missed the correct part of the transcript.
- A better query could reasonably retrieve better information from the YouTube transcript.

Use "web_search" when:
- The transcript does not contain the required information.
- The user explicitly asks for internet/web research.
- The question requires current/latest information.
- The required information is outside the video's scope.

Important:
Do NOT choose rewrite_query just because the answer is not in the transcript.
If the information genuinely does not exist in the transcript,
choose web_search.

User Question:
{question}

Retrieved YouTube Context:
{context}
"""

    result = grader_llm.invoke(prompt)

    overall_score = (
        result.relevance
        + result.completeness
        + result.specificity
        + result.confidence
    ) / 4

    grade = {
        "relevance": result.relevance,
        "completeness": result.completeness,
        "specificity": result.specificity,
        "confidence": result.confidence,
        "overall_score": overall_score,
        "action": result.action,
        "reason": result.reason
    }

    return {
        "grade": grade,
        "web_search_needed": result.action == "web_search"
    }


rewrite_prompt = """
You are a query rewriting agent for a YouTube RAG system.

Rewrite the user's question into a concise search query
that is more likely to retrieve the correct information
from the YouTube transcript.

Do not answer the question.

Return only the rewritten search query.

Original question:
{question}

Previous retrieved context:
{context}
"""


def rewrite_query_node(state: GraphState):

    question = state["messages"][-1].content

    documents = state.get("documents", [])

    context = "\n\n".join(
        doc.page_content
        for doc in documents
    )

    prompt = rewrite_prompt.format(
        question=question,
        context=context
    )

    response = google_llm.invoke(prompt)

    rewritten_query = response.content.strip()

    return {
        "rewritten_query": rewritten_query,
        "retry_count": state.get("retry_count", 0) + 1
    }

def retrieve_node(state: GraphState):

    if state.get("rewritten_query"):
        query = state["rewritten_query"]
    else:
        query = state["messages"][-1].content

    documents = retriever.invoke(query)

    return {
        "documents": documents
    }

from langchain_core.tools import tool


@tool
def tavily_search(query: str):
    """
    Search the internet for additional information
    when the YouTube transcript does not contain enough information.
    """

    response = tavily_client.search(
        query=query,
        search_depth="basic",
        max_results=5
    )

    return response["results"]

def web_search_node(state: GraphState):

    question = state["messages"][-1].content

    results = tavily_search.invoke(question)

    return {
        "web_results": results
    }

def context_fusion_node(state: GraphState):

    youtube_context = "\n\n".join(
        doc.page_content
        for doc in state.get("documents", [])
    )

    web_context = "\n\n".join(
        f"""
Title: {result.get("title", "")}
Source: {result.get("url", "")}
Content:
{result.get("content", "")}
"""
        for result in state.get("web_results", [])
    )

    final_context = f"""
===== YOUTUBE TRANSCRIPT =====

{youtube_context}

===== WEB SEARCH RESULTS =====

{web_context}
"""

    return {
        "context": final_context
    }

from langchain_core.prompts import ChatPromptTemplate


generate_prompt = ChatPromptTemplate.from_template("""
You are an AI assistant answering questions about a YouTube video.

Use the provided context to answer the user's question.

Rules:
- Use only information supported by the provided context.
- Do not invent information.
- If web search results are provided, they are additional information.
- Clearly distinguish information from the YouTube transcript and web sources when useful.
- If the available context does not contain enough information, say so honestly.
- Keep the answer clear and relevant.

Context:
{context}

Question:
{question}
""")


def generate_node(state: GraphState):

    question = state["messages"][-1].content

    # If context fusion already created context
    if state.get("context"):
        context = state["context"]

    else:
        # Use YouTube documents directly
        context = "\n\n".join(
            doc.page_content
            for doc in state.get("documents", [])
        )

    chain = generate_prompt | google_llm

    response = chain.invoke({
        "context": context,
        "question": question
    })

    return {
        "messages": [response]
    }

def reset_request_state(state: GraphState):
    return {
        "retry_count": 0,
        "rewritten_query": "",
        "context": "",
        "web_results": [],
        "documents": [],
        "grade": {},
    }

