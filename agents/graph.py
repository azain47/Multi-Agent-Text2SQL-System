from langgraph.graph import StateGraph, START, END
from agents.configuration import Configuration
from agents.states import FullState
from agents.agents import (relevance_checker, 
                    sql_generator, 
                    sql_validator, 
                    query_evaluator, 
                    feedback_formatter, 
                    finalize_answer, 
                    router_node, 
                    validation_router,
                    feedback_router,
                    evaluator_router) 

graph_builder = StateGraph(FullState, config_schema=Configuration)

graph_builder.add_node('relevance_checker', relevance_checker)
graph_builder.add_node('sql_generator', sql_generator)
graph_builder.add_node('sql_validator', sql_validator)
graph_builder.add_node('query_evaluator', query_evaluator)
graph_builder.add_node('feedback_formatter', feedback_formatter)
graph_builder.add_node('finalize_answer', finalize_answer)

graph_builder.add_edge(START, "relevance_checker")

graph_builder.add_conditional_edges(
    "relevance_checker",
    router_node,
    [        
        "sql_generator",
        "finalize_answer"
    ]
)

graph_builder.add_edge("sql_generator", "sql_validator")

graph_builder.add_conditional_edges(
    "sql_validator",
    validation_router,
    [        
        "query_evaluator",
        "feedback_formatter"
    ] 
)

graph_builder.add_conditional_edges(
    "query_evaluator",
    evaluator_router,
    [
        "finalize_answer",
        "feedback_formatter"
    ]
)

graph_builder.add_conditional_edges(
    "feedback_formatter",
    feedback_router,
    [ 
        "sql_generator",
        "finalize_answer"
    ]
)

graph_builder.add_edge("finalize_answer", END)

graph = graph_builder.compile()