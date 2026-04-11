from typing import Annotated, List, Optional, TypedDict
import operator

from langgraph.graph import END, START, StateGraph

from nodes.database_storage import database_storage
from nodes.llm_extractor import llm_extractor
from nodes.parser import parser


class CVState(TypedDict):
    pdf_path: str
    raw_texts: Annotated[List[tuple], operator.add]
    all_results: Annotated[List[dict], operator.add]
    error: Optional[str]


g = StateGraph(CVState)
g.add_node("parser", parser)
g.add_node("llm_extractor", llm_extractor)
g.add_node("database_storage", database_storage)

g.add_edge(START, "parser")
g.add_edge("parser", "llm_extractor")
g.add_edge("llm_extractor", "database_storage")
g.add_edge("database_storage", END)

app = g.compile()
