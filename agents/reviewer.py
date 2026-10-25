from .state import PipelineState
import json
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def reviewer_node(state: PipelineState) -> dict:
    prompt = f"""You are a code review agent. Review this code and its test results.

Code:
{state.code}

Test passed: {state.test_passed}
Stdout: {state.stdout}
Stderr: {state.stderr}

If the code is correct and tests passed, approve it.
If not, explain exactly what needs to be fixed.

Respond ONLY with JSON in this exact format, no other text:
{{"approved": true/false, "review_feedback": "..." or null}}"""

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

    if parsed["approved"]:
        status = "done"
    elif state.iteration_count >= state.max_iterations:
        status = "failed"
    else:
        status = "coding"

    return {
        "approved": parsed["approved"],
        "review_feedback": parsed.get("review_feedback"),
        "status": status,
    }