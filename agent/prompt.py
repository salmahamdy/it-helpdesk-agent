def build_prompt(issue: str, similar_cases: list[dict]) -> str:
    rag_context = ""
    if similar_cases:
        rag_context = "SIMILAR RESOLVED CASES FROM KNOWLEDGE BASE:\n"
        for i, case in enumerate(similar_cases, 1):
            rag_context += f"""
Case {i} (similarity: {case.get('similarity_score', 0):.2f}):
  Issue: {case['issue']}
  Resolution: {case.get('resolution', 'N/A')}
  Category: {case.get('issue_class', 'Unknown')}
  Commands: {', '.join(case.get('commands', [])) or 'None'}
"""

    prompt = f"""You are an expert IT Help Desk engineer. Analyze the user's issue and provide a structured response.

{rag_context}

CURRENT USER ISSUE:
{issue}

Respond ONLY with a valid JSON object in this exact format — no markdown, no explanation, no preamble:
{{
  "issue_class": "<category like Hardware/Network/Software/Security/Performance>",
  "confidence": <float between 0.0 and 1.0>,
  "diagnosis_summary": "<2-3 sentence technical diagnosis>",
  "resolution_steps": ["<step 1>", "<step 2>", "<step 3>"],
  "commands": ["<command1>", "<command2>"],
  "escalation_required": <true or false>,
  "preventive_measures": ["<measure 1>", "<measure 2>"]
}}"""
    return prompt
