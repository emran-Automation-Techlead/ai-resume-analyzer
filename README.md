# 🎯 SmartFit AI — Resume & Job Match Analyzer

> Dual-LLM powered resume analysis with vision parsing, Pydantic v2 structured scoring, and live-streamed coaching advice.

---

## What It Does

Upload any resume (PDF or scanned image), paste a job description, and SmartFit AI will:

- Parse your resume using **Claude Vision** (works on scanned/image PDFs too)
- Extract structured job requirements using **OpenAI GPT-4o native structured outputs**
- Score your fit across 4 dimensions: Skills · Experience · Education · ATS Coverage
- Stream a personalised coaching narrative from Claude
- Predict the 6–8 most likely interview questions based on your gaps
- Export a full report as **Markdown** or a styled **PDF**

---

## Features

- Multi-modal resume input (text PDF + scanned image via Claude Vision)
- Pydantic v2 structured extraction — zero JSON parsing errors
- 4-dimension deterministic fit scoring (no hallucinated scores)
- Live streaming recommendations (character-by-character in the UI)
- ATS keyword gap analysis with coverage percentage
- Skills gap table with severity labels (Critical / Preferred / Nice to Have)
- Predicted interview questions from identified gaps
- Export as Markdown or styled PDF with score bars
- Docker-ready for deployment

---

## Architecture

```
Resume (PDF/Image)  ──►  resume_service.py  ──►  CandidateProfile
Job Description     ──►  job_service.py     ──►  JobRequirements
                                 │
                    analysis_service.py
                    (deterministic scores + Claude FitAnalysis + streaming)
                                 │
                    report_service.py  ──►  Markdown / PDF
                                 │
                           app.py (Gradio UI)
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Resume Vision | Claude claude-sonnet-4-6 (multi-modal) |
| JD Extraction | OpenAI GPT-4o (native structured outputs) |
| Fit Analysis | Claude (JSON + streaming) |
| Data Models | Pydantic v2 |
| UI | Gradio Blocks with streaming |
| PDF Export | ReportLab |
| Deployment | Docker |

---

## How to Run

```bash
# 1. Clone
git clone https://github.com/emran-Automation-Techlead/ai-resume-analyzer
cd ai-resume-analyzer

# 2. Set up environment
cp .env.example .env
# Edit .env and add your API keys

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch
python app.py
# Open http://localhost:7860
```

### Docker

```bash
docker build -t smartfit-ai .
docker run -p 7860:7860 --env-file .env smartfit-ai
```

---

## Project Structure

```
ai-resume-analyzer/
├── app.py                  # Gradio UI with streaming
├── resume_service.py       # PDF text + Claude Vision parsing
├── job_service.py          # OpenAI structured JD extraction
├── analysis_service.py     # Fit scoring + Claude streaming
├── report_service.py       # Markdown + PDF export
├── models.py               # Pydantic v2 data models
├── prompts.py              # All LLM prompt templates
├── config.py               # pydantic-settings configuration
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Key Design Decisions

- **Deterministic scoring** — sub-scores (skills, experience, education, ATS) are computed with pure Python before calling the LLM. Claude receives them as anchors and cannot override them, eliminating hallucinated scores.
- **Dual-LLM strategy** — Claude handles vision parsing and long-form writing (its strengths); OpenAI handles structured extraction via native `response_format` (no post-processing needed).
- **Streaming first** — recommendations stream character-by-character so the UI feels alive, not like it's waiting for a batch result.

---

Built by [Mohammed Imran Ali](https://github.com/emran-Automation-Techlead) · [Hugging Face](https://huggingface.co/EmranAIShaper)
