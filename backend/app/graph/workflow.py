"""LangGraph workflow — assembles all nodes into a compiled StateGraph.

The graph follows a linear pipeline:
  code_parser → rag_retrieval → review_writer
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.code_parser.code_parser import code_parser_node
from app.agents.rag_retrieval.rag_retrieval import rag_retrieval_node
from app.agents.review_writer.review_writer import review_writer_node
from app.graph.state import ReviewState


def create_workflow():
    """Build and compile the LangGraph StateGraph with in-memory checkpointing."""
    graph = StateGraph(ReviewState)

    graph.add_node("code_parser", code_parser_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("review_writer", review_writer_node)

    graph.add_edge(START, "code_parser")
    graph.add_edge("code_parser", "rag_retrieval")
    graph.add_edge("rag_retrieval", "review_writer")
    graph.add_edge("review_writer", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


workflow = create_workflow()
