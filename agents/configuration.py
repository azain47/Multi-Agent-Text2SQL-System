import os
from pydantic import BaseModel, Field
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig

class Configuration(BaseModel):
    relevance_checker_model: str = Field(
        default='llama-3.1-8b-instant'
    )
    
    query_generator_model: str = Field(
        default='moonshotai/kimi-k2-instruct'
    )
    
    query_evaluator_model: str = Field(
        default='moonshotai/kimi-k2-instruct'
    )
    
    finalizing_model: str = Field(
        default='moonshotai/kimi-k2-instruct'
    )
    
    max_feedback_loops: int = Field(
        default=3
    )

    database_schema: dict = Field(
        description = "The Database Schema to write the SQL Query for."
    )
    
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        configurable = (
            config['configurable'] if config and "configurable" in config  else {}
        )
        
        raw_vals: dict[str, Any] = {
            name: configurable.get(name) for name in cls.model_fields.keys()
        }
        
        values = {k: v for k,v in raw_vals.items() if v is not None}
        
        return cls(**values)