"""
graph.py — Build and compile the full LangGraph research workflow.

PIPELINE (matches the notebook exactly):

    START
      │
      ▼
   planner          ← Breaks question into 3 tasks
      │
      ▼  (conditional fan-out via assign_tasks)
  researcher ×3     ← Runs in parallel, one per task
      │
      ▼  (all merge back here via operator.add)
   collector         ← Organizes findings
      │
      ▼
    critic           ← Quality check (score 0-10)
      │
      ▼
  report_writer      ← Writes the markdown report
      │
      ▼
  image_subgraph     ← Decides on + generates images
      │
      ▼
  file_saver         ← Saves report to disk
      │
      ▼
     END

HOW PARALLEL RESEARCHERS WORK:
  assign_tasks() uses LangGraph's Send() API to dispatch one researcher
  node per planned topic. They all run concurrently and their results
  are automatically merged into research_results via operator.add.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.state import ChatState
from app.agents.planner import planner
from app.agents.researcher import researcher
from app.agents.collector import collector
from app.agents.critic import critic
from app.agents.report_writer import report_writer
from app.agents.image_agent import image_subgraph
from app.agents.file_saver import file_saver


# ── Task dispatcher ───────────────────────────────────────────────────────────

def assign_tasks(state: ChatState):
    """
    Routes the planner's output to individual researcher nodes.

    For each planned research topic, this creates a Send() that
    launches a separate researcher node with {"task": topic} injected
    into its state.

    This is how LangGraph does parallel fan-out.
    """
    topics = state.get("research_tropics_planned") or []

    return [
        Send("researcher", {"task": topic, "question": state["question"]})
        for topic in topics
    ]


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph():
    """
    Construct and compile the full research workflow.

    Returns a compiled LangGraph that can be invoked like:
        graph.invoke({"question": "..."}, config={"configurable": {"thread_id": "..."}})
    """
    g = StateGraph(ChatState)

    # ── Add nodes (one per agent) ─────────────────────────────────────────────
    g.add_node("planner", planner)
    g.add_node("researcher", researcher)
    g.add_node("collector", collector)
    g.add_node("critic", critic)
    g.add_node("report_writer", report_writer)
    g.add_node("image_subgraph", image_subgraph)
    g.add_node("file_saver", file_saver)

    # ── Add edges (define the flow) ───────────────────────────────────────────

    # Start with the planner
    g.add_edge(START, "planner")

    # Planner → parallel researchers (conditional fan-out)
    g.add_conditional_edges(
        "planner",
        assign_tasks,
        ["researcher"],   # The possible target nodes from this fan-out
    )

    # All researchers → collector (they automatically merge via operator.add)
    g.add_edge("researcher", "collector")

    # Linear flow for the rest of the pipeline
    g.add_edge("collector", "critic")
    g.add_edge("critic", "report_writer")
    g.add_edge("report_writer", "image_subgraph")
    g.add_edge("image_subgraph", "file_saver")
    g.add_edge("file_saver", END)

    # ── Compile with in-memory checkpointing ─────────────────────────────────
    # InMemorySaver allows the graph to pause and resume (e.g., for human-in-the-loop).
    # Each run is identified by a thread_id in the config.
    checkpointer = InMemorySaver()
    return g.compile(checkpointer=checkpointer)


# The compiled graph — imported and used by the API route
workflow = build_graph()
