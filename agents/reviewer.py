from .state import PipelineState
from .llm import ask_json
from pydantic import BaseModel
from typing import Optional


class Review(BaseModel):
    approved: bool
    review_feedback: Optional[str] = None


def reviewer_node(state: PipelineState) -> dict:
    prompt = f"""You are a code review agent. Review this code and its test results.

Code:
{state.code}

Test passed: {state.test_passed}
Stdout: {state.stdout}
Stderr: {state.stderr}

If the code is correct and tests passed, approve it.
If not, explain exactly what needs to be fixed in review_feedback."""

    review = ask_json(prompt, Review)

    if review.approved:
        status = "done"
    elif state.iteration_count >= state.max_iterations:
        status = "failed"
    else:
        status = "coding"

    return {
        "approved": review.approved,
        "review_feedback": review.review_feedback,
        "status": status,
    }
