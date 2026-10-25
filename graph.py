from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph, END
from agents.state import PipelineState
from agents.planner import planner_node
from agents.coder import coder_node
from agents.tester import tester_node
from agents.reviewer import reviewer_node


def route_after_review(state: PipelineState) -> str:
    # routers can't update state, so reviewer_node decides the status and this just reads it
    if state.status == "coding":
        return "coder"
    return state.status


graph = StateGraph(PipelineState)

graph.add_node("planner", planner_node)
graph.add_node("coder", coder_node)
graph.add_node("tester", tester_node)
graph.add_node("reviewer", reviewer_node)

graph.set_entry_point("planner")
graph.add_edge("planner", "coder")
graph.add_edge("coder", "tester")
graph.add_edge("tester", "reviewer")

graph.add_conditional_edges(
    "reviewer",
    route_after_review,
    {"coder": "coder", "done": END, "failed": END},
)

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({
        "task_description": "Write a function that checks if a string is a palindrome, and print test results for a few cases."
    })
    print(result)