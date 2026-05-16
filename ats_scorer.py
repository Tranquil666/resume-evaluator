import json
from groq import Groq

_client = None

MODEL = "llama-3.3-70b-versatile"


def get_client():
    global _client
    if _client is None:
        _client = Groq()
    return _client

SCORING_PROMPT = """You are an expert ATS (Applicant Tracking System) evaluator.
Score the resume below across four dimensions. Return JSON only, no markdown.

Scoring criteria:
- relevant_skills (0-40): Technical skills depth, breadth, and relevance to the role
- experience_match (0-30): Years of experience, role relevance, career progression
- education (0-15): Degree level, institution prestige, relevant certifications
- formatting (0-15): Clarity, structure, keyword density, ATS-friendliness

{job_context}

Return this exact JSON structure:
{{
  "total_score": 0,
  "breakdown": {{
    "relevant_skills": {{"score": 0, "max": 40, "feedback": "..."}},
    "experience_match": {{"score": 0, "max": 30, "feedback": "..."}},
    "education": {{"score": 0, "max": 15, "feedback": "..."}},
    "formatting": {{"score": 0, "max": 15, "feedback": "..."}}
  }},
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "keyword_matches": [],
  "missing_keywords": [],
  "overall_verdict": "Strong/Good/Average/Weak candidate",
  "hire_recommendation": "Highly Recommended/Recommended/Maybe/Not Recommended"
}}

Resume:
"""


def calculate_ats_score(resume_text: str, job_description: str = "") -> dict:
    if job_description.strip():
        job_context = f"Job Description to match against:\n{job_description}\n\nFor keyword_matches and missing_keywords, compare the resume against this job description."
    else:
        job_context = "No specific job description provided. Evaluate as a general software/tech resume."

    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": SCORING_PROMPT.format(job_context=job_context) + resume_text,
            }
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)

    # Ensure total_score is computed correctly
    breakdown = result.get("breakdown", {})
    computed_total = sum(v.get("score", 0) for v in breakdown.values())
    result["total_score"] = computed_total
    return result
