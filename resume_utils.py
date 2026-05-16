import io
import json
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from groq import Groq

_client = None

MODEL = "llama-3.3-70b-versatile"


def get_client():
    global _client
    if _client is None:
        _client = Groq()
    return _client


ANALYSIS_SYSTEM_PROMPT = """You are an expert resume parser and HR specialist.
Extract structured information from the resume text provided.
Always respond with valid JSON only — no markdown, no explanation."""

ANALYSIS_USER_PROMPT = """Parse this resume and return a JSON object with exactly this structure:
{
  "candidate": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "phone number or null",
    "location": "City, Country or null",
    "linkedin": "URL or null",
    "github": "URL or null",
    "current_title": "Current/Most Recent Job Title",
    "years_of_experience": 0
  },
  "summary": "Brief professional summary from the resume, or null",
  "skills": {
    "technical": ["skill1", "skill2"],
    "soft": ["skill1", "skill2"],
    "tools": ["tool1", "tool2"],
    "languages": ["language1"]
  },
  "education": [
    {
      "degree": "Degree Name",
      "field": "Field of Study",
      "institution": "University Name",
      "year": "Graduation Year or range",
      "gpa": "GPA or null"
    }
  ],
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, Country or null",
      "start_date": "Month Year",
      "end_date": "Month Year or Present",
      "duration_months": 0,
      "responsibilities": ["key responsibility 1", "key responsibility 2"],
      "achievements": ["achievement 1"]
    }
  ],
  "certifications": ["cert1", "cert2"],
  "projects": [
    {
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["tech1", "tech2"]
    }
  ],
  "interview_topics": {
    "technical_areas": ["area1", "area2"],
    "suggested_questions": ["question1", "question2", "question3"]
  }
}

Resume text:
"""


def detect_file_type(buffer: bytes) -> str:
    if buffer[:4] == b"%PDF":
        return "pdf"
    if buffer[:2] == b"PK" and b"word/" in buffer[:2000]:
        return "docx"
    return "text"


def extract_text(buffer: bytes, file_type: str) -> str:
    if file_type == "pdf":
        return pdf_extract_text(io.BytesIO(buffer))
    if file_type == "docx":
        doc = Document(io.BytesIO(buffer))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return buffer.decode("utf-8", errors="ignore")


def analyze_resume(text: str) -> dict:
    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": ANALYSIS_USER_PROMPT + text},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def process_resume(buffer: bytes, filename: str = "") -> dict:
    file_type = detect_file_type(buffer)
    text = extract_text(buffer, file_type)
    if not text.strip():
        raise ValueError("Could not extract text from the uploaded file.")
    analysis = analyze_resume(text)
    analysis["_meta"] = {"filename": filename, "file_type": file_type, "char_count": len(text)}
    analysis["_raw_text"] = text
    return analysis
