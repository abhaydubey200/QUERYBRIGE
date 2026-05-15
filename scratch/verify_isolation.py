import asyncio
import os
import sys

# Mocking the environment to test the process isolation kernel
# We will simulate a segfault in the subprocess and see if the main process survives.

def crashing_function():
    print("Subprocess: I'm about to crash (segfault)...")
    import ctypes
    # This will cause a real segfault
    ctypes.string_at(0)

async def test_isolation():
    # Adding the project to sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(project_root, 'backend'))
    
    from app.core.process_isolation import run_in_subprocess
    
    print("Main Process: Starting isolated test...")
    try:
        # We run the crashing function in a subprocess
        result = run_in_subprocess(crashing_function, timeout=5.0)
        print(f"Main Process: Unexpected success? {result}")
    except Exception as e:
        print(f"Main Process: Successfully caught failure from subprocess: {type(e).__name__}")
        print(f"Error details: {str(e)[:100]}...")
    
    print("Main Process: I am still alive! The kernel works.")

if __name__ == "__main__":
    asyncio.run(test_isolation())
