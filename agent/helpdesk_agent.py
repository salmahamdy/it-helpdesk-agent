from agent.prompt import build_prompt
from agent.llm import call_groq
from rag.retriever import retrieve_similar_cases, add_to_knowledge_base


def run_agent(issue: str) -> tuple[dict, list[dict]]:
    similar_cases = retrieve_similar_cases(issue)
    prompt = build_prompt(issue, similar_cases)
    response = call_groq(prompt)
    _persist_case(issue, response)
    return response, similar_cases


def _persist_case(issue: str, response: dict) -> None:
    resolution_text = " ".join(response.get("resolution_steps", []))
    case = {
        "issue": issue,
        "resolution": resolution_text,
        "issue_class": response.get("issue_class", "Unknown"),
        "commands": response.get("commands", []),
        "escalation_required": response.get("escalation_required", False),
    }
    add_to_knowledge_base(case)
