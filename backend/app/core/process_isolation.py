import multiprocessing
import queue
import time
import traceback
from typing import Any, Callable, Dict, Optional, Tuple
from loguru import logger

def _worker(func: Callable, args: Tuple, kwargs: Dict, result_queue: multiprocessing.Queue):
    """
    Worker process entry point.
    """
    try:
        result = func(*args, **kwargs)
        result_queue.put({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Isolated process failed: {str(e)}")
        result_queue.put({
            "success": False, 
            "error": str(e), 
            "traceback": traceback.format_exc(),
            "exception_type": type(e).__name__
        })

def run_in_subprocess(func: Callable, args: Tuple = (), kwargs: Dict = None, timeout: float = 30.0) -> Any:
    """
    Runs a function in a separate process to isolate C-level crashes or infinite loops.
    """
    if kwargs is None:
        kwargs = {}
        
    result_queue = multiprocessing.get_context("spawn").Queue()
    process = multiprocessing.get_context("spawn").Process(
        target=_worker, 
        args=(func, args, kwargs, result_queue)
    )
    
    process.start()
    
    try:
        # Wait for result with timeout
        result = result_queue.get(timeout=timeout)
        process.join(timeout=1.0)
        
        if result["success"]:
            return result["data"]
        else:
            raise RuntimeError(f"Isolated execution failed: {result['error']}\n{result['traceback']}")
            
    except queue.Empty:
        logger.error(f"Isolated process timed out after {timeout}s")
        process.terminate()
        process.join()
        raise TimeoutError(f"Isolated process timed out after {timeout}s")
    except Exception as e:
        if process.is_alive():
            process.terminate()
            process.join()
        raise e
    finally:
        # Ensure process is cleaned up
        if process.is_alive():
            process.kill()
            process.join()
