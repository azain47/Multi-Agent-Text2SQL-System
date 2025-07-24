import json
from sqlglot import parse, exp

class SQLValidator:
    """
    A class to validate SQL queries against a predefined schema.

    The validation process includes:
    1.  Safety Check: Ensures the query is read-only (no DELETE, UPDATE, etc.).
    2.  Syntax Check: Verifies the SQL is syntactically correct.
    3.  Schema Check: Confirms all tables and columns exist in the schema.
    """
    UNSAFE_COMMANDS = {"DELETE", "UPDATE", "INSERT", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE"}

    def __init__(self, schema_json: dict):
        """
        Initializes the validator with a database schema.

        Args:
            schema_json_path (str): The file path to the JSON schema.
        """

        # Pre-process the schema for efficient lookups
        self.tables = {table['table_name'] for table in schema_json['tables']}
        self.columns = {
            table['table_name']: set(table['columns'].keys())
            for table in schema_json['tables']
        }
        print("Validator initialized. Known tables:", self.tables)

    def validate(self, sql_query: str) -> dict:
        """
        Validates a single SQL query through a multi-step process.

        Args:
            sql_query (str): The SQL query string to validate.

        Returns:
            dict: A dictionary containing a boolean 'is_valid' and a list of 'errors'.
        """
        errors = []

        try:
            # sqlglot.parse returns a list of parsed expressions.
            parsed_expressions = parse(sql_query)
            if len(parsed_expressions) > 1:
                errors.append("Multiple SQL statements are not allowed.")
                return {"is_valid": False, "errors": errors}

            parsed = parsed_expressions[0]

            # 1. Safety Check: We only allow SELECT statements.
            if not isinstance(parsed, exp.Select):
                command_name = type(parsed).__name__.upper()
                if command_name in self.UNSAFE_COMMANDS:
                    errors.append(f"Unsafe command '{command_name}' is not allowed.")
                else:
                    errors.append(f"Only SELECT statements are allowed. Found '{command_name}'.")
                return {"is_valid": False, "errors": errors}

            # 2. Schema Check using the parsed expression
            # Build a map of all aliases to their real table names for context
            table_context = self._get_table_context(parsed)

            # 2a. Validate tables
            for table in parsed.find_all(exp.Table):
                table_name = table.this.name
                if table_name not in self.tables:
                    errors.append(f"Table '{table_name}' does not exist.")
            
            if errors: # Don't check columns if tables are invalid
                return {"is_valid": False, "errors": errors}

            # 2b. Validate columns
            for column in parsed.find_all(exp.Column):
                if column.this.name == '*': # Ignore '*' wildcard
                    continue

                col_name = column.this.name
                table_alias = column.table # The alias or table name used, e.g., 'u' in 'u.name'

                if table_alias:
                    # Column is qualified (e.g., users.name)
                    real_table = table_context.get(table_alias)
                    if not real_table:
                         # This case is rare as sqlglot would likely fail parsing if the alias doesn't exist
                         errors.append(f"Table alias or name '{table_alias}' not found in query context.")
                         continue
                    if col_name not in self.columns.get(real_table, set()):
                        errors.append(f"Column '{col_name}' does not exist in table '{real_table}'.")
                else:
                    # Column is unqualified (e.g., name). Check if it exists in any table in the query.
                    found = False
                    for table_name in table_context.values():
                        if col_name in self.columns.get(table_name, set()):
                            found = True
                            break
                    if not found:
                        errors.append(f"Unqualified column '{col_name}' could not be found in any of the query's tables.")

        except Exception as e:
            # Catches syntax errors from sqlglot during parsing
            errors.append(f"Invalid SQL syntax: {e}")
            return {"is_valid": False, "errors": errors}

        if errors:
            return {"is_valid": False, "errors": errors}
        
        return {"is_valid": True, "errors": []}

    def _get_table_context(self, parsed_query: exp.Expression) -> dict:
        """Helper to create a mapping from table aliases to real table names."""
        context = {}
        from_clause = parsed_query.args.get('from')
        if from_clause:
            for table in from_clause.find_all(exp.Table):
                table_name = table.this.name
                alias = table.alias or table_name
                context[alias] = table_name
        
        # Get tables from JOIN clauses
        for join in parsed_query.args.get('joins', []):
            # The table being joined is in join.this
            table = join.this
            table_name = table.this.name
            alias = table.alias or table_name
            context[alias] = table_name

        return context