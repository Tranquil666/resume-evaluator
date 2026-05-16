import json
import os
import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Pull key from Streamlit Cloud secrets if available
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from resume_utils import process_resume
from ats_scorer import calculate_ats_score
from sample_resumes import SAMPLE_RESUMES

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Evaluator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.score-ring {
    font-size: 3rem;
    font-weight: 800;
    text-align: center;
    padding: 1rem;
    border-radius: 50%;
    width: 120px;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: auto;
}
.score-high   { background:#d1fae5; color:#065f46; }
.score-medium { background:#fef3c7; color:#92400e; }
.score-low    { background:#fee2e2; color:#991b1b; }
.tag {
    display:inline-block;
    background:#e0e7ff;
    color:#3730a3;
    border-radius:9999px;
    padding:2px 10px;
    font-size:0.8rem;
    margin:2px;
}
.tag-green { background:#d1fae5; color:#065f46; }
.tag-red   { background:#fee2e2; color:#991b1b; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def score_class(score: int) -> str:
    if score >= 75:
        return "score-high"
    if score >= 50:
        return "score-medium"
    return "score-low"


def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Average"
    return "Needs Work"


def save_output(data: dict, filename: str):
    out_dir = Path("Outputs")
    out_dir.mkdir(exist_ok=True)
    stem = Path(filename).stem
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{stem}_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    return out_path


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")

    api_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Free key from console.groq.com — stored only for this session.",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    st.divider()
    st.markdown("### How it works")
    st.markdown(
        """
1. Upload a PDF or DOCX resume (or use a sample)
2. Optionally paste a job description
3. Click **Evaluate**
4. Get structured data + ATS score
5. Download the JSON report
"""
    )
    st.divider()
    st.markdown("### Try a sample resume")
    sample_choice = st.selectbox(
        "Load sample",
        ["— none —"] + [r["name"] for r in SAMPLE_RESUMES],
    )


# ── Main ───────────────────────────────────────────────────────────────────────
st.title("📄 Resume Evaluator")
st.caption("Upload a resume, get structured insights and an ATS score powered by Llama 3.3 70B via Groq.")

col_upload, col_jd = st.columns([1, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload Resume (PDF or DOCX)",
        type=["pdf", "docx"],
        help="Max size: 5 MB",
    )

with col_jd:
    job_description = st.text_area(
        "Job Description (optional)",
        height=160,
        placeholder="Paste the job description here to get a tailored ATS match score…",
    )

# Resolve input: file upload beats sample selection
resume_bytes: bytes | None = None
resume_filename = ""

if uploaded_file is not None:
    resume_bytes = uploaded_file.read()
    resume_filename = uploaded_file.name
elif sample_choice != "— none —":
    sample = next(r for r in SAMPLE_RESUMES if r["name"] == sample_choice)
    resume_bytes = sample["text"].encode()
    resume_filename = f"{sample['name'].replace(' ', '_')}_sample.txt"
    st.info(f"Using sample resume: **{sample['name']}**")

# ── Evaluate button ────────────────────────────────────────────────────────────
evaluate = st.button(
    "🔍 Evaluate Resume",
    type="primary",
    disabled=(resume_bytes is None or not os.getenv("GROQ_API_KEY")),
)

if not os.getenv("GROQ_API_KEY"):
    st.warning("Please enter your Groq API key in the sidebar to continue. Get one free at console.groq.com")

if evaluate and resume_bytes:
    with st.spinner("Parsing resume with GPT-4o-mini…"):
        try:
            analysis = process_resume(resume_bytes, resume_filename)
        except Exception as e:
            st.error(f"Failed to parse resume: {e}")
            st.stop()

    with st.spinner("Calculating ATS score…"):
        try:
            raw_text = analysis.pop("_raw_text", "")
            ats = calculate_ats_score(raw_text, job_description)
        except Exception as e:
            st.error(f"Failed to score resume: {e}")
            st.stop()

    full_output = {**analysis, "ats_score": ats}
    saved_path = save_output(full_output, resume_filename)

    st.success(f"Evaluation complete! Saved to `{saved_path}`")

    # ── ATS Score Overview ─────────────────────────────────────────────────
    st.header("ATS Score")

    total = ats.get("total_score", 0)
    css_cls = score_class(total)
    label = score_label(total)

    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    with c1:
        st.markdown(
            f'<div class="score-ring {css_cls}">{total}</div>'
            f'<p style="text-align:center;font-weight:600;margin-top:6px">{label}</p>',
            unsafe_allow_html=True,
        )
    with c2:
        st.metric("Verdict", ats.get("overall_verdict", "—"))
    with c3:
        st.metric("Recommendation", ats.get("hire_recommendation", "—"))

    # Score breakdown bars
    st.subheader("Score Breakdown")
    breakdown = ats.get("breakdown", {})
    dim_labels = {
        "relevant_skills": "Relevant Skills",
        "experience_match": "Experience Match",
        "education": "Education",
        "formatting": "Formatting",
    }
    for key, dim_label in dim_labels.items():
        dim = breakdown.get(key, {})
        score = dim.get("score", 0)
        max_score = dim.get("max", 40)
        feedback = dim.get("feedback", "")
        pct = score / max_score if max_score else 0
        col_a, col_b = st.columns([1, 3])
        with col_a:
            st.metric(dim_label, f"{score}/{max_score}")
        with col_b:
            st.progress(pct, text=feedback)

    # Strengths & Improvements
    col_s, col_i = st.columns(2)
    with col_s:
        st.subheader("✅ Strengths")
        for s in ats.get("strengths", []):
            st.markdown(f"- {s}")
    with col_i:
        st.subheader("⚡ Improvements")
        for imp in ats.get("improvements", []):
            st.markdown(f"- {imp}")

    # Keyword matches
    kw_matches = ats.get("keyword_matches", [])
    kw_missing = ats.get("missing_keywords", [])
    if kw_matches or kw_missing:
        st.subheader("Keywords")
        col_km, col_kmiss = st.columns(2)
        with col_km:
            st.markdown("**Present**")
            tags = " ".join(f'<span class="tag tag-green">{k}</span>' for k in kw_matches)
            st.markdown(tags or "—", unsafe_allow_html=True)
        with col_kmiss:
            st.markdown("**Missing**")
            tags = " ".join(f'<span class="tag tag-red">{k}</span>' for k in kw_missing)
            st.markdown(tags or "—", unsafe_allow_html=True)

    st.divider()

    # ── Candidate Info ─────────────────────────────────────────────────────
    st.header("Candidate Profile")
    cand = analysis.get("candidate", {})

    col_info, col_skills = st.columns([1, 1])
    with col_info:
        st.subheader("Contact & Overview")
        info_rows = {
            "Name": cand.get("name"),
            "Title": cand.get("current_title"),
            "Experience": f"{cand.get('years_of_experience', '?')} years",
            "Email": cand.get("email"),
            "Phone": cand.get("phone"),
            "Location": cand.get("location"),
            "LinkedIn": cand.get("linkedin"),
            "GitHub": cand.get("github"),
        }
        for k, v in info_rows.items():
            if v:
                st.markdown(f"**{k}:** {v}")

    with col_skills:
        st.subheader("Skills")
        skills = analysis.get("skills", {})
        for category, items in skills.items():
            if items:
                tags_html = " ".join(f'<span class="tag">{s}</span>' for s in items)
                st.markdown(f"**{category.title()}**")
                st.markdown(tags_html, unsafe_allow_html=True)

    # Summary
    if analysis.get("summary"):
        st.subheader("Summary")
        st.info(analysis["summary"])

    st.divider()

    # ── Experience ─────────────────────────────────────────────────────────
    st.header("Work Experience")
    for exp in analysis.get("experience", []):
        with st.expander(
            f"**{exp.get('title', 'Role')}** @ {exp.get('company', 'Company')}  ·  {exp.get('start_date', '')} – {exp.get('end_date', '')}"
        ):
            if exp.get("location"):
                st.markdown(f"📍 {exp['location']}")
            if exp.get("responsibilities"):
                st.markdown("**Responsibilities**")
                for r in exp["responsibilities"]:
                    st.markdown(f"- {r}")
            if exp.get("achievements"):
                st.markdown("**Achievements**")
                for a in exp["achievements"]:
                    st.markdown(f"- {a}")

    # ── Education ─────────────────────────────────────────────────────────
    st.header("Education")
    edu_cols = st.columns(min(len(analysis.get("education", [])) or 1, 3))
    for i, edu in enumerate(analysis.get("education", [])):
        with edu_cols[i % 3]:
            st.markdown(
                f"**{edu.get('degree', '')}** in {edu.get('field', '')}\n\n"
                f"{edu.get('institution', '')}  \n"
                f"Graduated: {edu.get('year', '—')}"
                + (f"  \nGPA: {edu['gpa']}" if edu.get("gpa") else "")
            )

    # ── Certifications & Projects ─────────────────────────────────────────
    col_cert, col_proj = st.columns(2)
    with col_cert:
        if analysis.get("certifications"):
            st.header("Certifications")
            for c in analysis["certifications"]:
                st.markdown(f"🏅 {c}")

    with col_proj:
        if analysis.get("projects"):
            st.header("Projects")
            for proj in analysis["projects"]:
                with st.expander(proj.get("name", "Project")):
                    st.write(proj.get("description", ""))
                    if proj.get("technologies"):
                        tags = " ".join(
                            f'<span class="tag">{t}</span>' for t in proj["technologies"]
                        )
                        st.markdown(tags, unsafe_allow_html=True)

    # ── Interview Topics ──────────────────────────────────────────────────
    interview = analysis.get("interview_topics", {})
    if interview:
        st.header("Interview Preparation")
        col_it, col_iq = st.columns(2)
        with col_it:
            st.subheader("Technical Areas")
            for area in interview.get("technical_areas", []):
                st.markdown(f"- {area}")
        with col_iq:
            st.subheader("Suggested Questions")
            for q in interview.get("suggested_questions", []):
                st.markdown(f"- {q}")

    st.divider()

    # ── Download ───────────────────────────────────────────────────────────
    st.subheader("Download Report")
    st.download_button(
        label="⬇️ Download JSON Report",
        data=json.dumps(full_output, indent=2),
        file_name=f"{Path(resume_filename).stem}_evaluation.json",
        mime="application/json",
    )
