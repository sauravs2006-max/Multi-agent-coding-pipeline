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
    file_name: str = ""
    explanation: str = ""

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