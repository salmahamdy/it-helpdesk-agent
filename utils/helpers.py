import json


def format_json_display(data: dict) -> str:
    return json.dumps(data, indent=2)


def confidence_label(score: float) -> str:
    if score >= 0.85:
        return "High"
    elif score >= 0.6:
        return "Medium"
    return "Low"


def confidence_color(score: float) -> str:
    if score >= 0.85:
        return "#22c55e"
    elif score >= 0.6:
        return "#f59e0b"
    return "#ef4444"


def escalation_badge(required: bool) -> str:
    if required:
        return "🔴 Escalation Required"
    return "🟢 No Escalation Needed"
