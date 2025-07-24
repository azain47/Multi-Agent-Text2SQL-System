from datetime import datetime

def get_current_date():
    return datetime.now().strftime("%B %d, %Y")

# ---- PROMPTS -----
relevance_prompt = """You are a senior Database Administrator, and you have access to the database schema. The user will ask you a query, and your task
is to:
1. Check if the query is relevant to the given database schema.
2. Replace relative terms like 'today', 'yesterday', 'prev week' with absolute values using the given date and time.
3. Rephrase and optimize the user's query into an informative llm prompt.

You should respond in JSON format with ALL of these keys:
- "thoughts" : your thinking process
- "evaluation" : Final Evaluation, MUST BE either "PASS" or "FAIL"
- "optimized_query" : user's query optimized for llm

Current Date and Time:
{curr_date_time}

Database Schema:
{db_schema}

User's Query:
{query}

"""

generator_prompt = """You are a senior Database Administrator, and you have access to the database schema. The user will give you a prompt and your
task is to write an SQL Query that fulfills the user's request. 
An Evaluator will evaluate your query and check if it is syntactically, semantically correct and satisfies the user's query. 
You can perform this task in multiple attempts, and after each attempt you will be given a feedback if your query fails.
Use the feedback to enhance and write the correct SQL query.

You should respond in JSON format with ALL of these keys:
- "thoughts" : your thinking process
- "sql" : The Final SQL Query

Current Date and Time:
{curr_date_time}

Database Schema:
{db_schema}

User's Query:
{query}

"""  
    
evaluator_prompt = """You are a senior Database Administrator, and you have access to the database schema. Evaluate the SQL Query and the user's prompt,
to understand if the given SQL Query satisfies the user's request.
Give your answer in the following format:

You should respond in JSON format with ALL of these keys:
- "thoughts" : your thinking process
- "evaluation" : Final Evaluation, MUST BE either "PASS" or "FAIL"
- "feedback" : What should be changed or improved?

Current Date and Time:
{curr_date_time}

Database Schema:
{db_schema}

User's Query:
{query}

Generated SQL:
{generated_query}

"""

finalize_prompt = """Generate a high quality answer to the user's question based on the provided instructions.
Instructions:
- You are the final step of multi-step Natural Language to SQL Generator, dont mention you are the final step.
- You have access to user's original query and the query optimized for SQL Generation.
- You have access to the Previous Attempts at generating SQL Query by the Generator LLM, which will also be paired with its feedback; which can be either by an programmatic
SQL validator, or an LLM Evaluator for semantic evaluation.
- You have access to the Database Schema for which the query was to be written.
- You have access to the Final Verdict, which defines what the Final Answer should be.

# Data
User's Query:
{query}

Optimized Query:
{optimized_query}

Previous Attempts:
{prev_attempts}

Database Schema:
{db_schema}

Current Date:
{curr_date_time}

Final Verdict:
{final_verdict}

"""