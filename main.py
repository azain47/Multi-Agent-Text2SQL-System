import argparse
from langchain_core.messages import HumanMessage
from agents.graph import graph
from agents.configuration import Configuration
import json

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph Text2SQL Agent")
    parser.add_argument(
        "--query",
        type=str, 
        required=True,
        help="Natural Language Query"
    )
    
    parser.add_argument(
        "--database-schema-json-path",
        type=str,
        required=True,
        help="Path to Database Schema JSON",
    )
    
    parser.add_argument(
        "--max-feedback-loops",
        type=int,
        default=3,
        help="Maximum number of feedback loops",
    )
    
    parser.add_argument(
        '--relevance-checker-model', 
        type=str, 
        default='llama-3.1-8b-instant',
        help='Model for relevance checking.'
    )
    
    parser.add_argument(
        '--query-generator-model', 
        type=str, 
        default='moonshotai/kimi-k2-instruct',
        help='Model for query generation.'
    )
    
    parser.add_argument(
        '--query-evaluator-model', 
        type=str, 
        default='moonshotai/kimi-k2-instruct',
        help='Model for query evaluation.'
    )
    
    parser.add_argument(
        '--finalizing-model', 
        type=str, 
        default='moonshotai/kimi-k2-instruct',
        help='Model for finalizing SQL.'
    )

    args = parser.parse_args()

    try:
        with open(args.database_schema_json_path,'r') as f:
            db_schema = json.load(f)
    
    except Exception as e:
        print(f"Error occured while parsing arguments: {e}")
        return

    state = {
        "messages": [HumanMessage(content=args.query)],
    }
    
    config = Configuration(
        database_schema=db_schema,
        relevance_checker_model=args.relevance_checker_model,
        query_generator_model=args.query_generator_model,
        query_evaluator_model=args.query_evaluator_model,
        finalizing_model=args.finalizing_model,
        max_feedback_loops=args.max_feedback_loops
    )
    
    result = graph.invoke(state, {"configurable": config.model_dump()})
    
    messages = result.get("messages", [])
    
    if messages:
        print(messages[-1].content)


if __name__ == "__main__":
    main()