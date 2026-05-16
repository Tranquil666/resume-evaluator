# Resume Evaluator

An AI-powered ATS (Applicant Tracking System) that parses resumes and scores them across multiple dimensions using **Llama 3.3 70B** via Groq.

## Features

- Upload **PDF or DOCX** resumes (or use built-in sample resumes)
- Extract structured candidate data: contact info, skills, experience, education, certifications, projects
- **ATS Score (0–100)** broken down across 4 dimensions:
  - Relevant Skills (0–40)
  - Experience Match (0–30)
  - Education (0–15)
  - Formatting (0–15)
- Paste a **job description** for tailored keyword match analysis
- Interview preparation: suggested questions and technical areas
- **Download JSON report** of the full evaluation
- Results auto-saved to `Outputs/`

## Demo

Try it live → **[resume-evaluator.streamlit.app](https://tranquil666-resume-evaluator.streamlit.app)**

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit |
| LLM | Llama 3.3 70B via Groq (free) |
| PDF parsing | pdfminer.six |
| DOCX parsing | python-docx |
| Language | Python 3.8+ |

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Tranquil666/resume-evaluator.git
cd resume-evaluator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

Get a free Groq API key at [console.groq.com](https://console.groq.com).

```bash
cp .env.example .env
# Edit .env and add your key:
# GROQ_API_KEY=your_key_here
```

### 4. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Project Structure

```
resume-evaluator/
├── app.py              # Streamlit web UI
├── resume_utils.py     # PDF/DOCX parsing + LLM extraction
├── ats_scorer.py       # ATS scoring logic
├── sample_resumes.py   # 3 built-in test resumes
├── requirements.txt
└── Outputs/            # Auto-saved JSON reports
```

## Deployment

This app is deployed on **Streamlit Community Cloud**. To deploy your own fork:

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the entry point
4. Add `GROQ_API_KEY` under **Advanced settings → Secrets**

## License

MIT
