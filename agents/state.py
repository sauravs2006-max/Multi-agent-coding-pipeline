from pydantic import BaseModel
from typing import Optional


class PipelineState(BaseModel):
    # Input
    task_description: str

    # Planner output
    subtasks: list[str] = []
    approach_notes: str = ""

    # Coder output
    code: str = ""
    test_code: str = ""
    explanation: str = ""
    code_history: list[str] = []  # every attempt, so the eval can grade the first try too

    # Tester output
    test_passed: bool = False
    test_results: list[dict] = []
    stdout: str = ""
    stderr: str = ""

    # Reviewer output
    approved: bool = False
    review_feedback: Optional[str] = None

    # Loop control
    iteration_count: int = 0
    max_iterations: int = 3
    status: str = "planning"