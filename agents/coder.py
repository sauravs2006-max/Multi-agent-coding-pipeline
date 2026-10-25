from .state import PipelineState
from .llm import ask_json
from pydantic import BaseModel


class CodeResult(BaseModel):
    code: str
    file_name: str
    explanation: str


def coder_node(state: PipelineState) -> dict:
    retry_context = ""
    if state.review_feedback:
        retry_context = f"\n\nPrevious attempt was rejected. Feedback: {state.review_feedback}\nFix this in your new version."

    prompt = f"""You are a coding agent. Implement the following task in Python.

Task: {state.task_description}
Subtasks: {state.subtasks}{retry_context}"""

    result = ask_json(prompt, CodeResult)

    return {
        "code": result.code,
        "file_name": result.file_name,
        "explanation": result.explanation,
        "status": "testing",
        "iteration_count": state.iteration_count + 1,
    }
