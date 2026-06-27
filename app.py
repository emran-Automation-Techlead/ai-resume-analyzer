import os
import tempfile
from dotenv import load_dotenv
load_dotenv()

import gradio as gr

from resume_service import parse_resume
from job_service import analyze_job_description, calculate_ats_coverage
from analysis_service import generate_fit_analysis, stream_recommendations
from report_service import generate_markdown_report, generate_pdf_report
from models import FitAnalysis, CandidateProfile, JobRequirements

# ---- Globals to hold last analysis for export ----
_last_analysis: FitAnalysis = None
_last_candidate: CandidateProfile = None
_last_job: JobRequirements = None


# ---- Score bar HTML ----

def _score_bar(label: str, score: int) -> str:
    color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
    return f"""
    <div style="margin: 6px 0;">
      <div style="display:flex; justify-content:space-between; font-size:13px; margin-bottom:3px;">
        <span>{label}</span><span style="font-weight:bold; color:{color};">{score}/100</span>
      </div>
      <div style="background:#e5e7eb; border-radius:6px; height:10px;">
        <div style="background:{color}; width:{score}%; height:10px; border-radius:6px;"></div>
      </div>
    </div>"""


def _scores_html(analysis: FitAnalysis) -> str:
    fit_colors = {"Excellent": "#22c55e", "Good": "#3b82f6", "Fair": "#f59e0b", "Poor": "#ef4444"}
    fc = fit_colors.get(analysis.fit_level, "#6b7280")
    html = f"""
    <div style="padding:16px; background:#f8fafc; border-radius:10px; border:1px solid #e5e7eb;">
      <div style="text-align:center; margin-bottom:14px;">
        <span style="font-size:42px; font-weight:800; color:{fc};">{analysis.overall_score}</span>
        <span style="font-size:18px; color:#6b7280;">/100</span>
        <span style="display:block; font-size:16px; font-weight:600; color:{fc};">{analysis.fit_level} Match</span>
      </div>
      {_score_bar("Skills Match", analysis.skills_score)}
      {_score_bar("Experience", analysis.experience_score)}
      {_score_bar("Education", analysis.education_score)}
      {_score_bar("ATS Coverage", analysis.ats_coverage_score)}
    </div>"""
    return html


def _status_html(message: str, color: str = "#3b82f6") -> str:
    return f"""<div style="padding:10px 14px; background:{color}15; border-left:4px solid {color};
    border-radius:6px; color:{color}; font-weight:500; font-size:14px;">{message}</div>"""


# ---- Main analysis function ----

def run_analysis(resume_file, jd_text):
    global _last_analysis, _last_candidate, _last_job

    if resume_file is None:
        yield (_status_html("⚠ Please upload a resume file.", "#ef4444"),
               "", "", "", gr.update(value=None), gr.update(value=None))
        return
    if not jd_text or len(jd_text.strip()) < 50:
        yield (_status_html("⚠ Please paste a job description (at least 50 characters).", "#ef4444"),
               "", "", "", gr.update(value=None), gr.update(value=None))
        return

    # -- Step 1: Parse resume --
    yield (_status_html("📄 Parsing resume..."), "", "", "",
           gr.update(value=None), gr.update(value=None))
    try:
        candidate, resume_text = parse_resume(resume_file.name)
    except Exception as e:
        yield (_status_html(f"❌ Resume parsing failed: {e}", "#ef4444"),
               "", "", "", gr.update(value=None), gr.update(value=None))
        return

    # -- Step 2: Analyse job description --
    yield (_status_html("🔍 Analysing job description..."), "", "", "",
           gr.update(value=None), gr.update(value=None))
    try:
        job = analyze_job_description(jd_text)
        ats_data = calculate_ats_coverage(resume_text, job)
    except Exception as e:
        yield (_status_html(f"❌ Job analysis failed: {e}", "#ef4444"),
               "", "", "", gr.update(value=None), gr.update(value=None))
        return

    # -- Step 3: Generate fit analysis --
    yield (_status_html("⚡ Generating fit analysis..."), "", "", "",
           gr.update(value=None), gr.update(value=None))
    try:
        analysis = generate_fit_analysis(candidate, job, ats_data)
        _last_analysis = analysis
        _last_candidate = candidate
        _last_job = job
    except Exception as e:
        yield (_status_html(f"❌ Fit analysis failed: {e}", "#ef4444"),
               "", "", "", gr.update(value=None), gr.update(value=None))
        return

    scores_html = _scores_html(analysis)

    # Summary tab
    summary_md = f"""## {candidate.name} → {job.job_title} at {job.company}

**{analysis.executive_summary}**

### Strengths
{chr(10).join(f'- ✅ {s}' for s in analysis.strengths)}

### Critical Gaps
{chr(10).join(f'- ❌ {g}' for g in analysis.critical_gaps) or '_None identified_'}

### Missing ATS Keywords
{chr(10).join(f'`{kw}`' for kw in analysis.ats_missing_keywords[:12]) or '_Good ATS coverage_'}
"""

    # Interview questions tab
    questions_md = "## Predicted Interview Questions\n\n" + "\n\n".join(
        f"**{i+1}.** {q}" for i, q in enumerate(analysis.predicted_interview_questions)
    )

    # -- Step 4: Stream recommendations --
    yield (_status_html("✍ Streaming coaching advice...", "#8b5cf6"),
           scores_html, summary_md, questions_md,
           gr.update(value=None), gr.update(value=None))

    accumulated = ""
    try:
        for chunk in stream_recommendations(analysis):
            accumulated += chunk
            yield (_status_html("✍ Streaming coaching advice...", "#8b5cf6"),
                   scores_html, summary_md, accumulated,
                   gr.update(value=None), gr.update(value=None))
    except Exception as e:
        accumulated += f"\n\n_Streaming error: {e}_"

    yield (_status_html("✅ Analysis complete!", "#22c55e"),
           scores_html, summary_md, accumulated,
           gr.update(value=None), gr.update(value=None))


# ---- Export handlers ----

def export_markdown():
    if _last_analysis is None:
        return gr.update(value=None)
    content = generate_markdown_report(_last_analysis, _last_candidate, _last_job)
    path = os.path.join(tempfile.gettempdir(), "smartfit_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return gr.update(value=path)


def export_pdf():
    if _last_analysis is None:
        return gr.update(value=None)
    pdf_bytes = generate_pdf_report(_last_analysis, _last_candidate, _last_job)
    path = os.path.join(tempfile.gettempdir(), "smartfit_report.pdf")
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return gr.update(value=path)


# ---- UI ----

CUSTOM_CSS = """
#header { text-align: center; padding: 20px 0 10px 0; }
#header h1 { font-size: 2.2em; color: #1e40af; margin: 0; }
#header p  { color: #6b7280; margin: 4px 0 0 0; }
.analyze-btn { background: #1e40af !important; }
"""

with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS, title="SmartFit AI") as demo:

    gr.HTML("""
    <div id="header">
      <h1>🎯 SmartFit AI</h1>
      <p>Resume & Job Match Analyzer — Dual-LLM powered with streaming insights</p>
    </div>
    """)

    with gr.Row():
        # ---- Left: Inputs ----
        with gr.Column(scale=1):
            gr.Markdown("### Upload & Analyse")
            resume_upload = gr.File(
                label="Resume (PDF, PNG or JPG)",
                file_types=[".pdf", ".png", ".jpg", ".jpeg"]
            )
            jd_input = gr.Textbox(
                label="Job Description",
                placeholder="Paste the full job description here...",
                lines=14
            )
            analyze_btn = gr.Button("Analyse Fit", variant="primary", elem_classes=["analyze-btn"])

        # ---- Right: Results ----
        with gr.Column(scale=2):
            status_box = gr.HTML(_status_html("Ready — upload a resume and paste a job description.", "#6b7280"))
            score_display = gr.HTML("")

            with gr.Tabs():
                with gr.Tab("Overview"):
                    summary_output = gr.Markdown("")
                with gr.Tab("Coaching Advice"):
                    recs_output = gr.Markdown("")
                with gr.Tab("Interview Prep"):
                    questions_output = gr.Markdown("")

    with gr.Row():
        export_md_btn = gr.Button("Export Markdown")
        export_pdf_btn = gr.Button("Export PDF")
        download_file = gr.File(label="Download", visible=True)

    # ---- Event wiring ----
    analyze_btn.click(
        fn=run_analysis,
        inputs=[resume_upload, jd_input],
        outputs=[status_box, score_display, summary_output, recs_output, questions_output,
                 download_file],
        queue=True
    )
    export_md_btn.click(fn=export_markdown, outputs=[download_file])
    export_pdf_btn.click(fn=export_pdf, outputs=[download_file])


if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
