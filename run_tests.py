import subprocess, sys
result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/test_content_store.py",
     "tests/test_content_queue.py", 
     "tests/test_briefs.py", 
     "-v"],
    capture_output=False
)
sys.exit(result.returncode)
