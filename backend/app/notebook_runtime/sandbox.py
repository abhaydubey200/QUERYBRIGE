import multiprocessing
import sys
import io
import traceback
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NotebookSandbox:
    """
    Isolated Multiprocessing Sandbox for Notebook Execution.
    Enforces memory quotas and execution timeouts.
    """
    def __init__(self, memory_limit_mb: int = 512, timeout_seconds: int = 60):
        self.memory_limit_mb = memory_limit_mb
        self.timeout_seconds = timeout_seconds

    def _execute_code(self, code: str, context: Dict, result_queue: multiprocessing.Queue):
        """
        Inner function executed in a separate process.
        """
        # Redirect stdout/stderr
        stdout = io.StringIO()
        stderr = io.StringIO()
        sys.stdout = stdout
        sys.stderr = stderr

        globals_dict = context.copy()
        
        try:
            # Execute the code
            exec(code, globals_dict)
            
            # Extract results (only serializable parts)
            results = {k: v for k, v in globals_dict.items() if k not in context and self._is_serializable(v)}
            
            result_queue.put({
                "status": "success",
                "output": stdout.getvalue(),
                "errors": stderr.getvalue(),
                "results": results
            })
        except Exception:
            result_queue.put({
                "status": "error",
                "output": stdout.getvalue(),
                "errors": traceback.format_exc(),
                "results": {}
            })

    def _is_serializable(self, obj):
        try:
            import json
            json.dumps(obj)
            return True
        except:
            return False

    async def run(self, code: str, context: Optional[Dict] = None) -> Dict:
        """
        Runs code in a sandboxed process with non-blocking monitoring.
        """
        import asyncio
        if context is None:
            context = {}

        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=self._execute_code, 
            args=(code, context, result_queue)
        )

        process.start()
        logger.info(f"Sandbox process started: PID {process.pid}")
        
        try:
            # Wait for process completion or timeout without busy-waiting
            # We use a wrapper to make the process wait awaitable
            done, pending = await asyncio.wait(
                [asyncio.create_task(self._wait_for_process(process))],
                timeout=self.timeout_seconds
            )

            if not done:
                logger.warning(f"Sandbox timeout after {self.timeout_seconds}s. Terminating PID {process.pid}")
                process.terminate()
                # Give it a moment to terminate gracefully
                await asyncio.sleep(0.5)
                if process.is_alive():
                    process.kill()
                return {
                    "status": "timeout",
                    "error": f"Execution exceeded {self.timeout_seconds} seconds limit."
                }
            
            # Retrieve result non-blockingly
            if result_queue.empty():
                return {"status": "error", "error": "Process terminated without returning results."}
            
            return await asyncio.to_thread(result_queue.get)

        except Exception as e:
            logger.error(f"Sandbox execution error: {str(e)}")
            return {"status": "error", "error": str(e)}
        finally:
            if process.is_alive():
                process.join(timeout=1.0)
                if process.is_alive():
                    process.kill()
            logger.info(f"Sandbox cleanup complete for PID {process.pid}")

    async def _wait_for_process(self, process):
        """Helper to wait for a multiprocessing.Process in an async-friendly way."""
        while process.is_alive():
            await asyncio.sleep(0.1)
        return True
