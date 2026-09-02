from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.graph.state import ChatState
from app.graph.nodes import (
    planner,
    assign_tasks,
    researcher,
    collector,
    critic,
    report_writer,
    file_saver
)
from app.graph.image_nodes import image_subgraph


def build_research_graph():
    g = StateGraph(ChatState)

    # Add Nodes
    g.add_node("planner", planner)
    g.add_node("researcher", researcher)
    g.add_node("collector", collector)
    g.add_node("critic", critic)
    g.add_node("report_writer", report_writer)
    g.add_node("image_subgraph", image_subgraph)
    g.add_node("file_saver", file_saver)

    # Edges
    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", assign_tasks, ["researcher"])
    g.add_edge("researcher", "collector")
    g.add_edge("collector", "critic")
    g.add_edge("critic", "report_writer")
    g.add_edge("report_writer", "image_subgraph")
    g.add_edge("image_subgraph", "file_saver")
    g.add_edge("file_saver", END)

    checkpointer = InMemorySaver()
    return g.compile(checkpointer=checkpointer)


# Compiled singleton instance
workflow = build_research_graph()
