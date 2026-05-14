from agent.prompt import build_prompt
from agent.llm import call_groq
from rag.retriever import retrieve_similar_cases, add_to_knowledge_base

# Only auto-persist cases above this confidence
MIN_CONFIDENCE_TO_SAVE = 0.75


def run_agent(issue: str) -> tuple[dict, list[dict]]:
    similar_cases = retrieve_similar_cases(issue)
    prompt = build_prompt(issue, similar_cases)
    response = call_groq(prompt)

    saved = False
    confidence = response.get("confidence", 0)
    if confidence >= MIN_CONFIDENCE_TO_SAVE:
        _persist_case(issue, response)
        saved = True

    response["_saved_to_kb"] = saved
    return response, similar_cases


def _persist_case(issue: str, response: dict) -> None:
    resolution_text = " ".join(response.get("resolution_steps", []))
    case = {
        "issue": issue,
        "resolution": resolution_text,
        "issue_class": response.get("issue_class", "Unknown"),
        "commands": response.get("commands", []),
        "escalation_required": response.get("escalation_required", False),
        "tags": _extract_tags(issue, response),
        "source": "agent",
        "verified": False,
    }
    add_to_knowledge_base(case)


def _extract_tags(issue: str, response: dict) -> list[str]:
    """Pull simple tags from the issue class and common keywords."""
    tags = []
    issue_class = response.get("issue_class", "")
    for part in issue_class.replace("-", " ").replace("/", " ").split():
        tag = part.strip().lower()
        if tag and len(tag) > 1:
            tags.append(tag)
    return list(set(tags))
