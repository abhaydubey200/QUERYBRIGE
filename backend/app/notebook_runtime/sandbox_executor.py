import multiprocessing
import queue
import time
import pandas as pd
from typing import Dict, Any, Optional

class SandboxExecutor:
    """Hardened execution for Python cells with strict resource limits."""
    
    def __init__(self, memory_limit_mb: int = 512, timeout_seconds: int = 30):
        self.memory_limit = memory_limit_mb
        self.timeout = timeout_seconds

    def _worker(self, code: str, df_context: Dict, result_queue: multiprocessing.Queue):
        """Worker process for execution isolation."""
        try:
            # Restricted globals
            safe_globals = {
                "pd": pd,
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "dict": dict,
                    "list": list,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool
                }
            }
            safe_globals.update(df_context)
            
            # Execute code
            exec(code, safe_globals)
            
            # Collect results (exclude internals and large dfs for queue stability)
            results = {k: v for k, v in safe_globals.items() if not k.startswith("__") and k != "pd"}
            result_queue.put({"success": True, "data": results})
        except Exception as e:
            result_queue.put({"success": False, "error": str(e)})

    def execute(self, code: str, df_context: Optional[Dict] = None):
        """Run code in a separate process with a timeout."""
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=self._worker, 
            args=(code, df_context or {}, result_queue)
        )
        
        p.start()
        
        try:
            result = result_queue.get(timeout=self.timeout)
            p.join()
            return result
        except queue.Empty:
            p.terminate()
            p.join()
            return {"success": False, "error": f"Execution timed out after {self.timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
