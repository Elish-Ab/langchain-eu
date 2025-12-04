# app/normalizer/graph.py
from langgraph.graph import StateGraph, END

from app.normalizer.state import JobState
from app.normalizer.nodes.preprocess import node_preprocess
from app.normalizer.nodes.llm_extract import node_llm_extract
from app.normalizer.nodes.validate_normalize import node_validate_normalize
from app.normalizer.nodes.derive_experience import node_derive_experience
from app.normalizer.nodes.enrich_company_website import node_company_website_lookup
from app.normalizer.nodes.finalize import node_finalize

graph = StateGraph(JobState)

graph.add_node("preprocess", node_preprocess)
graph.add_node("llm_extract", node_llm_extract)
graph.add_node("validate_normalize", node_validate_normalize)
graph.add_node("derive_experience", node_derive_experience)
graph.add_node("website_lookup", node_company_website_lookup)
graph.add_node("finalize", node_finalize)

graph.set_entry_point("preprocess")
graph.add_edge("preprocess", "llm_extract")
graph.add_edge("llm_extract", "validate_normalize")
graph.add_edge("validate_normalize", "derive_experience")

def website_router(state: JobState):
    return "website_lookup" if state.get("needs_company_website_lookup") else "finalize"

graph.add_conditional_edges(
    "derive_experience",
    website_router,
    {"website_lookup": "website_lookup", "finalize": "finalize"}
)

graph.add_edge("website_lookup", "finalize")
graph.add_edge("finalize", END)

job_graph = graph.compile()
