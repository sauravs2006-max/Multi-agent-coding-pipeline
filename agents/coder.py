from .state import PipelineState
import json
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def coder_node(state: PipelineState) -> dict:
    retry_context = ""
    if state.review_feedback:
        retry_context = f"\n\nPrevious attempt was rejected. Feedback: {state.review_feedback}\nFix this in your new version."

    prompt = f"""You are a coding agent. Implement the following task in Python.

Task: {state.task_description}
Subtasks: {state.subtasks}{retry_context}

Respond ONLY with JSON in this exact format, no other text:
{{"code": "...", "file_name": "...", "explanation": "..."}}"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    parsed = json.loads(raw)

    return {
        "code": parsed["code"],
        "file_name": parsed["file_name"],
        "explanation": parsed["explanation"],
        "status": "testing",
        "iteration_count": state.iteration_count + 1,
    }