from .state import PipelineState
from .llm import ask_json
from pydantic import BaseModel


class Plan(BaseModel):
    subtasks: list[str]
    approach_notes: str


def planner_node(state: PipelineState) -> dict:
    prompt = f"""You are a planning agent. Break the following coding task into a
short list of concrete subtasks, and briefly note your approach.

Task: {state.task_description}"""

    plan = ask_json(prompt, Plan)

    return {
        "subtasks": plan.subtasks,
        "approach_notes": plan.approach_notes,
        "status": "coding",
    }
