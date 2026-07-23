from .state import PipelineState
import json
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def planner_node(state: PipelineState) -> dict:
    prompt = f"""You are a planning agent. Break the following coding task into a
short list of concrete subtasks, and briefly note your approach.

Task: {state.task_description}

Respond ONLY with JSON in this exact format, no other text:
{{"subtasks": ["...", "..."], "approach_notes": "..."}}"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    parsed = json.loads(raw_text)

    return {
        "subtasks": parsed["subtasks"],
        "approach_notes": parsed["approach_notes"],
        "status": "coding",
    }