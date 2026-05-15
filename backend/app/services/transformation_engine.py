import pandas as pd
from typing import List, Dict, Any, Union
from loguru import logger
import io

class TransformationEngine:
    """
    Local-first transformation engine supporting SQL and Python (Pandas).
    """
    def __init__(self, data: List[Dict[str, Any]]):
        self.df = pd.DataFrame(data)

    def apply_python(self, code: str) -> List[Dict[str, Any]]:
        """
        Executes arbitrary python code against the local dataframe.
        SAFE ONLY FOR TRUSTED ENVIRONMENTS.
        """
        try:
            # We use local context for the 'df' variable
            local_vars = {"df": self.df, "pd": pd}
            exec(code, {}, local_vars)
            self.df = local_vars["df"]
            return self.df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Python transformation failed: {str(e)}")
            raise ValueError(f"Transformation Error: {str(e)}")

    def filter_data(self, column: str, value: Any, operator: str = "==") -> List[Dict[str, Any]]:
        if operator == "==":
            self.df = self.df[self.df[column] == value]
        elif operator == ">":
            self.df = self.df[self.df[column] > value]
        # Add more operators
        return self.df.to_dict(orient="records")

    def aggregate(self, group_by: List[str], agg_func: Dict[str, str]) -> List[Dict[str, Any]]:
        self.df = self.df.groupby(group_by).agg(agg_func).reset_index()
        return self.df.to_dict(orient="records")

    def get_results(self) -> List[Dict[str, Any]]:
        return self.df.to_dict(orient="records")
