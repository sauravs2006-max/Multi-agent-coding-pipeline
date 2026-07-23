from .state import PipelineState
import subprocess
import tempfile
import os

def tester_node(state: PipelineState) -> dict:
    # Write the generated code to a temp file
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, state.file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(state.code)

        # Run it directly on your machine for now — NOT safe for real
        # untrusted code, but fine as a placeholder until Week 2's sandbox
        result = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

        test_passed = result.returncode == 0

        return {
            "test_passed": test_passed,
            "test_results": [{"passed": test_passed, "returncode": result.returncode}],
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "reviewing",
        }