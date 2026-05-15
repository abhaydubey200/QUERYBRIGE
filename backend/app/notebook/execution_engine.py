import pandas as pd
import duckdb
import io
import contextlib
import json

class NotebookExecutionEngine:
    def __init__(self):
        self.con = duckdb.connect(database=':memory:')

    def execute_sql(self, sql: str, df_context: dict = None):
        """Execute SQL using DuckDB, optionally with Pandas DataFrames in context."""
        if df_context:
            for name, df in df_context.items():
                self.con.register(name, df)
        
        try:
            result_df = self.con.execute(sql).df()
            return result_df.to_dict(orient='records'), None
        except Exception as e:
            return None, str(e)

    def execute_python(self, code: str, df_context: dict = None):
        """Execute Python code in a restricted scope with Pandas available."""
        # Note: In a true production environment, this should be in a separate process or container.
        # For this implementation, we use a local exec with restricted globals.
        
        output = io.StringIO()
        local_vars = {"pd": pd, "np": pd.np if hasattr(pd, "np") else None}
        if df_context:
            local_vars.update(df_context)

        try:
            with contextlib.redirect_stdout(output):
                exec(code, {"__builtins__": {}}, local_vars)
            
            # Extract any new/modified DataFrames from local_vars
            results = {}
            for k, v in local_vars.items():
                if isinstance(v, pd.DataFrame):
                    results[k] = v.to_dict(orient='records')
                elif isinstance(v, (list, dict, str, int, float, bool)) and k != "__builtins__":
                    results[k] = v

            return {
                "stdout": output.getvalue(),
                "variables": results
            }, None
        except Exception as e:
            return None, str(e)
