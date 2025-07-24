from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import add_messages
from agents.schemas import EvalEnum, FinalVerdictEnum
import operator


class FullState(TypedDict):
    messages: Annotated[list, add_messages]
    
    user_query: str
    optimized_query: str
    relevance_evaluation: EvalEnum
    
    generated_query: Optional[str]
    max_feedback_loops: Optional[int]
    current_loop_count: Optional[int]
    sql_validation_result: Optional[bool]
    sql_validator_feedback: Optional[List[str]]
    evaluator_result: Optional[EvalEnum]
    evaluator_feedback: Optional[str]
    previous_attempts: Annotated[list, operator.add]
    final_verdict: Optional[FinalVerdictEnum]
