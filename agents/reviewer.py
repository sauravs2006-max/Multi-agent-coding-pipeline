from .state import PipelineState
from .llm import ask_json
from pydantic import BaseModel
from typing import Optional


class Review(BaseModel):
    approved: bool
    review_feedback: Optional[str] = None


def reviewer_node(state: PipelineState) -> dict:
    prompt = f"""You are a code review agent. Review this code, its tests and the test results.

Task: {state.task_description}

Code (solution.py):
{state.code}

Tests (test_solution.py):
{state.test_code}

Test passed: {state.test_passed}
Stdout: {state.stdout}
Stderr: {state.stderr}

Approve only if the code does what the task asks and the tests actually check
the task, including edge cases. Tests that assert nothing meaningful are not enough.
If not approved, explain exactly what needs to be fixed in review_feedback."""

    review = ask_json(prompt, Review)

    # the rule lives in code, the LLM can't approve code that failed its tests
    approved = review.approved and state.test_passed
    feedback = review.review_feedback
    if review.approved and not state.test_passed:
        feedback = "The tests failed. Fix the code (or a wrong test) using the test stderr."

    if approved:
        status = "done"
    elif state.iteration_count >= state.max_iterations:
        status = "failed"
    else:
        status = "coding"

    return {
        "approved": approved,
        "review_feedback": feedback,
        "status": status,
    }
