from agent.prompt import build_prompt
from agent.llm import call_groq
from rag.retriever import retrieve_similar_cases, add_to_knowledge_base
from config import MIN_CONFIDENCE_TO_SAVE, GROUNDING_THRESHOLD


def run_agent(issue: str, os_info: str | None = None) -> tuple[dict, list[dict]]:
    similar_cases = retrieve_similar_cases(issue)  # verified-only by default
    # Retrieve on the clean issue, but give the model the OS context too.
    issue_for_prompt = issue if not os_info else f"{issue}\n\nUser system / OS: {os_info}"
    prompt = build_prompt(issue_for_prompt, similar_cases)
    response = call_groq(prompt)

    # We KNOW whether RAG context was supplied, so compute it rather than
    # trusting the model's self-report.
    response["used_rag"] = len(similar_cases) > 0

    confidence = _safe_float(response.get("confidence"))
    top_score = max((c.get("similarity_score", 0.0) for c in similar_cases), default=0.0)

    # Confidence only decides whether the answer is worth a human's review time.
    # It does NOT make the case retrievable — only mark_verified() does that.
    queued = confidence >= MIN_CONFIDENCE_TO_SAVE
    if queued:
        _queue_for_review(issue, response, confidence, top_score)

    response["_saved_to_kb"] = queued
    response["_review"] = {
        "queued_for_review": queued,
        "model_confidence": confidence,
        "retrieval_score": round(top_score, 3),
        "grounded": top_score >= GROUNDING_THRESHOLD,
        "reason": (
            "queued pending human verification"
            if queued
            else f"confidence {confidence:.2f} < {MIN_CONFIDENCE_TO_SAVE}"
        ),
    }
    return response, similar_cases


def _queue_for_review(issue: str, response: dict, confidence: float, top_score: float) -> None:
    """Persist an agent answer as an UNVERIFIED case awaiting human review.

    verified=False means it will not be retrieved as context until promoted
    via retriever.mark_verified(). Provenance is stored to support triage.
    """
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
        "review_status": "pending",
        # provenance for the reviewer / future automated checks
        "model_confidence": confidence,
        "retrieval_score": round(top_score, 3),
        "grounded": top_score >= GROUNDING_THRESHOLD,
    }
    add_to_knowledge_base(case)


def _safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_tags(issue: str, response: dict) -> list[str]:
    """Pull simple tags from the issue class and common keywords."""
    tags = []
    issue_class = response.get("issue_class", "")
    for part in issue_class.replace("-", " ").replace("/", " ").split():
        tag = part.strip().lower()
        if tag and len(tag) > 1:
            tags.append(tag)
    return list(set(tags))
