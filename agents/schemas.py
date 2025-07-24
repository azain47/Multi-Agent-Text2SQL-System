from pydantic import BaseModel, Field
from typing import TypedDict, Annotated
from enum import Enum

class EvalEnum(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"

class FinalVerdictEnum(str, Enum):
    QUERY_IRRELEVANT = "Query is irrelevant"
    PASSED_EVALUATOR = "Final and Correct SQL Query has been generated."
    MAX_ATTEMPTS = "Query could not be generated after multiple attempts."
    
class RelevanceCheckerSchema(BaseModel):
    thoughts: str = Field(
        description = 'Reasoning behind the decision'
    )
    evaluation: EvalEnum = Field(
        description = 'Final Evaluation, MUST BE either "PASS" or "FAIL"'
    )
    optimized_query: str = Field(
        description = "User's query optimized for LLM."
    )

class GeneratorSchema(BaseModel):
    thoughts: str = Field(
        description = 'Reasoning behind the decision'
    )
    sql: str = Field(
        description = 'The Final SQL Query.' 
    )
    
class EvaluatorSchema(BaseModel):
    thoughts: str = Field(
        description = 'Reasoning behind the decision'
    )
    evaluation: EvalEnum = Field(
        description = 'Final Evaluation, MUST BE either "PASS" or "FAIL"'
    )
    feedback: str = Field(
        description = "What should be changed or improved? None if evaluation is PASS"
    )
