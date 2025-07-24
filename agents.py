from langchain_core.runnables import RunnableConfig
from langchain_groq.chat_models import ChatGroq

from langchain_core.messages import AnyMessage, AIMessage, HumanMessage

from configuration import Configuration
from prompts import relevance_prompt, generator_prompt, evaluator_prompt, finalize_prompt, get_current_date
from schemas import RelevanceCheckerSchema, GeneratorSchema, EvaluatorSchema, EvalEnum, FinalVerdictEnum
from states import FullState

import os
from dotenv import load_dotenv
from sqlvalidator import SQLValidator

load_dotenv()

def relevance_checker(state: FullState, config: RunnableConfig) -> FullState:
    configurable = Configuration.from_runnable_config(config)
    
    llm = ChatGroq(
        api_key=os.environ.get('GROQ_API_KEY'),
        model=configurable.relevance_checker_model,
        temperature=0.3
    )
    
    llm = llm.with_structured_output(RelevanceCheckerSchema)
    
    curr_date_time = get_current_date()
    
    user_query = state['messages'][-1].content
    
    formatted_prompt = relevance_prompt.format(
        curr_date_time=curr_date_time,
        db_schema=configurable.database_schema,
        query=user_query
    )
    output: RelevanceCheckerSchema = llm.invoke(formatted_prompt)
    
    print('----Relevance----')
    print(output.thoughts)
    print(f"Evaluation: {output.evaluation.value}")
    
    return {
        'user_query': user_query,
        'relevance_evaluation': output.evaluation,
        'optimized_query': output.optimized_query
    }

def router_node(state: FullState, config: RunnableConfig):
    print('----Router----')
    print(f"Evaluation: {state.get('relevance_evaluation').value}")
    
    if state.get('relevance_evaluation') == EvalEnum.PASS:
        return "sql_generator"
    else:
        return "finalize_answer"

def sql_generator(state: FullState, config: RunnableConfig) -> FullState:
    prev_attempts = state.get('previous_attempts', [])
    
    configurable = Configuration.from_runnable_config(config)
    
    llm = ChatGroq(
        api_key=os.environ.get('GROQ_API_KEY'),
        model=configurable.query_generator_model
    )
    
    formatted_prompt = generator_prompt.format(
        curr_date_time=get_current_date(),
        db_schema=configurable.database_schema,
        query=state.get('optimized_query')
    )
    if len(prev_attempts) > 0:
        formatted_prompt += f"\nPrevious Attempts:\n{chr(10).join([f'- {a}' for a in prev_attempts])}"
    
    llm = llm.with_structured_output(GeneratorSchema, method='json_mode')
    
    output: GeneratorSchema = llm.invoke(formatted_prompt)
    print('----Generator----')
    print(output.thoughts)
    print(f"Generated SQL: {output.sql}")
    
    current_loop = state.get('current_loop_count', 0)
    max_loops = state.get('max_feedback_loops', configurable.max_feedback_loops)
    
    return {
        'generated_query': output.sql,
        'current_loop_count': current_loop,
        'max_feedback_loops': max_loops
    }

def sql_validator(state: FullState, config: RunnableConfig) -> FullState:
    configurable = Configuration.from_runnable_config(config)
    validator = SQLValidator(configurable.database_schema)
    
    generated_sql = state.get('generated_query')
    
    output = validator.validate(generated_sql)
    
    print('----Validator----')
    print(f"SQL Valid: {output.get('is_valid')}")
    if not output.get('is_valid'):
        print(f"Validation Errors: {output.get('errors')}")
    
    return {
        'sql_validation_result': output.get('is_valid'),
        'sql_validator_feedback': output.get('errors', [])
    }

def validation_router(state: FullState, config: RunnableConfig):
    """Router to decide if SQL goes to evaluator or feedback formatter"""
    if state.get('sql_validation_result'):
        return "query_evaluator"
    else:
        return "feedback_formatter"

def query_evaluator(state: FullState, config: RunnableConfig) -> FullState:
    configurable = Configuration.from_runnable_config(config)
    
    llm = ChatGroq(
        api_key=os.environ.get('GROQ_API_KEY'),
        model=configurable.query_evaluator_model
    )
    
    formatted_prompt = evaluator_prompt.format(
        curr_date_time=get_current_date(),
        db_schema=configurable.database_schema,
        query=state.get('user_query'),
        generated_query=state.get('generated_query')
    )
    
    llm = llm.with_structured_output(EvaluatorSchema, method='json_mode')
    
    output: EvaluatorSchema = llm.invoke(formatted_prompt)
    
    print('----Evaluator----')
    print(output.thoughts)
    print(f"Evaluation: {output.evaluation.value}")
    
    return {
        'evaluator_result': output.evaluation,
        'evaluator_feedback': output.feedback if output.evaluation == EvalEnum.FAIL else ''
    }

def evaluator_router(state: FullState, config: RunnableConfig):
    """Router to decide if query passes evaluation or needs feedback"""
    if state.get('evaluator_result') == EvalEnum.PASS:
        return "finalize_answer"
    else:
        return "feedback_formatter"

def feedback_formatter(state: FullState, config: RunnableConfig) -> FullState:
    configurable = Configuration.from_runnable_config(config)
    
    feedback_parts = []
    feedback_parts.append(f"# Generated SQL Query\n{state.get('generated_query', '')}")
    
    validator_feedback = state.get('sql_validator_feedback', [])
    if validator_feedback:
        feedback_parts.append(f"# SQL Validator Feedback\n{chr(10).join(validator_feedback)}")
    
    evaluator_feedback = state.get('evaluator_feedback', '')
    if evaluator_feedback:
        feedback_parts.append(f"# Query Evaluator Feedback\n{evaluator_feedback}")
    
    feedback = '\n\n'.join(feedback_parts)
    
    current_loop = state.get('current_loop_count', 0) + 1
    
    print('----Feedback Formatter----')
    print(f"Loop count: {current_loop}/{state.get('max_feedback_loops', 3)}")
    print(f"Feedback: {feedback}")
    
    return {
        'previous_attempts': [feedback],  
        'current_loop_count': current_loop,
        'sql_validator_feedback': [],
        'evaluator_feedback': '',
        'generated_query': ''
    }

def feedback_router(state: FullState, config: RunnableConfig):
    """Router to decide if we continue the loop or finalize"""
    current_loop = state.get('current_loop_count', 0)
    max_loops = state.get('max_feedback_loops', 3)
    
    if current_loop >= max_loops:
        return "finalize_answer"
    else:
        return "sql_generator"

def finalize_answer(state: FullState, config: RunnableConfig) -> FullState:
    configurable = Configuration.from_runnable_config(config)
    
    llm = ChatGroq(
        api_key=os.environ.get('GROQ_API_KEY'),
        model=configurable.finalizing_model
    )
    
    if state.get('relevance_evaluation') != EvalEnum.PASS:
        final_verdict = FinalVerdictEnum.QUERY_IRRELEVANT
    elif state.get('evaluator_result') == EvalEnum.PASS:
        final_verdict = FinalVerdictEnum.PASSED_EVALUATOR
    else:
        final_verdict = FinalVerdictEnum.MAX_ATTEMPTS
    
    formatted_prompt = finalize_prompt.format(
        query=state.get('user_query', ''),
        optimized_query=state.get('optimized_query', ''),
        prev_attempts=state.get('previous_attempts', []),
        db_schema=configurable.database_schema,
        curr_date_time=get_current_date(),
        final_verdict=final_verdict.value
    )
    
    output = llm.invoke(formatted_prompt)
    print('----Finalize----')
    print(f"Final verdict: {final_verdict.value}")
    
    return {
        'messages': [AIMessage(content=output.content)],  
        'final_verdict': final_verdict.value
    }
