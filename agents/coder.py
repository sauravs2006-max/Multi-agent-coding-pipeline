from .state import PipelineState
from .llm import ask_json
from pydantic import BaseModel


class CodeResult(BaseModel):
    code: str
    test_code: str
    explanation: str


def coder_node(state: PipelineState) -> dict:
    retry_context = ""
    if state.review_feedback:
        # give it the failing code and traceback too, not just the feedback
        retry_context = f"""

Your previous attempt was rejected.
Feedback: {state.review_feedback}

Previous code:
{state.code}

Previous tests:
{state.test_code}

Test stderr:
{state.stderr}

Fix the problems in your new version."""

    prompt = f"""You are a coding agent. Implement the following task in Python.

Task: {state.task_description}
Subtasks: {state.subtasks}

Use only the Python standard library. The code runs in a sandbox with no
network and no third-party packages installed.

Your code is saved as solution.py. Keep it to the implementation, with no
top-level tests or demo prints.

Also write test_code: a separate script saved as test_solution.py that imports
from solution (for example `from solution import my_function`) and checks the
behaviour with plain assert statements, including edge cases. It is run with
`python test_solution.py`, so don't use pytest or unittest.{retry_context}"""

    result = ask_json(prompt, CodeResult)

    return {
        "code": result.code,
        "code_history": state.code_history + [result.code],
        "test_code": result.test_code,
        "explanation": result.explanation,
        "status": "testing",
        "iteration_count": state.iteration_count + 1,
    }
