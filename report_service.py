import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER

from models import FitAnalysis, CandidateProfile, JobRequirements


# ---- Score colour helper ----

def _score_color(score: int) -> str:
    if score >= 75:
        return "#22c55e"   # green
    elif score >= 50:
        return "#f59e0b"   # amber
    return "#ef4444"       # red


# ---- Markdown export ----

def generate_markdown_report(analysis: FitAnalysis,
                              candidate: CandidateProfile,
                              job: JobRequirements) -> str:
    lines = [
        f"# SmartFit AI Report",
        f"**Candidate:** {candidate.name}  |  **Role:** {job.job_title} at {job.company}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## Overall Fit Score",
        f"### {analysis.overall_score}/100 — {analysis.fit_level}",
        "",
        "| Dimension | Score |",
        "|-----------|-------|",
        f"| Skills Match | {analysis.skills_score}/100 |",
        f"| Experience | {analysis.experience_score}/100 |",
        f"| Education | {analysis.education_score}/100 |",
        f"| ATS Coverage | {analysis.ats_coverage_score}/100 |",
        "",
        "---",
        "",
        "## Executive Summary",
        analysis.executive_summary,
        "",
        "---",
        "",
        "## Strengths",
        *[f"- {s}" for s in analysis.strengths],
        "",
        "---",
        "",
        "## Skills Gap Analysis",
        "",
        "| Skill | Have It? | Priority |",
        "|-------|----------|----------|",
        *[f"| {e.skill} | {'✅' if e.candidate_has else '❌'} | {e.severity} |"
          for e in analysis.skill_evaluations],
        "",
        "---",
        "",
        "## Top Recommendations",
        *[f"{i+1}. {r}" for i, r in enumerate(analysis.recommendations)],
        "",
        "---",
        "",
        "## Missing ATS Keywords",
        *[f"- {kw}" for kw in analysis.ats_missing_keywords],
        "",
        "---",
        "",
        "## Predicted Interview Questions",
        *[f"{i+1}. {q}" for i, q in enumerate(analysis.predicted_interview_questions)],
    ]
    return "\n".join(lines)


# ---- PDF export ----

def generate_pdf_report(analysis: FitAnalysis,
                         candidate: CandidateProfile,
                         job: JobRequirements) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # ---- Title ----
    title_style = ParagraphStyle("Title", parent=styles["Heading1"],
                                  fontSize=22, textColor=colors.HexColor("#1e40af"),
                                  alignment=TA_CENTER, spaceAfter=6)
    story.append(Paragraph("SmartFit AI — Fit Analysis Report", title_style))

    sub_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                fontSize=11, textColor=colors.HexColor("#6b7280"),
                                alignment=TA_CENTER, spaceAfter=20)
    story.append(Paragraph(
        f"{candidate.name}  ·  {job.job_title} @ {job.company}  ·  "
        f"{datetime.now().strftime('%d %b %Y')}",
        sub_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 0.4*cm))

    # ---- Score table ----
    score_color = colors.HexColor(_score_color(analysis.overall_score))
    score_data = [
        ["Overall Score", "Skills", "Experience", "Education", "ATS Coverage"],
        [
            Paragraph(f'<font color="{_score_color(analysis.overall_score)}" size="16"><b>{analysis.overall_score}/100</b></font>', styles["Normal"]),
            f"{analysis.skills_score}/100",
            f"{analysis.experience_score}/100",
            f"{analysis.education_score}/100",
            f"{analysis.ats_coverage_score}/100",
        ]
    ]
    score_table = Table(score_data, colWidths=[3.5*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.5*cm))

    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                         textColor=colors.HexColor("#1e40af"), spaceBefore=14, spaceAfter=6)
    body = styles["BodyText"]

    # ---- Executive summary ----
    story.append(Paragraph("Executive Summary", h2))
    story.append(Paragraph(analysis.executive_summary, body))
    story.append(Spacer(1, 0.3*cm))

    # ---- Strengths ----
    story.append(Paragraph("Strengths", h2))
    for s in analysis.strengths:
        story.append(Paragraph(f"✓  {s}", body))
    story.append(Spacer(1, 0.3*cm))

    # ---- Skills gap table ----
    story.append(Paragraph("Skills Gap Analysis", h2))
    skill_data = [["Skill", "Have It?", "Priority", "Recommendation"]]
    for ev in analysis.skill_evaluations:
        skill_data.append([
            ev.skill,
            "✅" if ev.candidate_has else "❌",
            ev.severity,
            Paragraph(ev.recommendation, ParagraphStyle("sm", fontSize=8))
        ])
    skill_table = Table(skill_data, colWidths=[3.5*cm, 2*cm, 3*cm, 8*cm])
    skill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(skill_table)
    story.append(Spacer(1, 0.3*cm))

    # ---- Recommendations ----
    story.append(Paragraph("Top Recommendations", h2))
    for i, rec in enumerate(analysis.recommendations, 1):
        story.append(Paragraph(f"{i}.  {rec}", body))
    story.append(Spacer(1, 0.3*cm))

    # ---- Interview Questions ----
    story.append(Paragraph("Predicted Interview Questions", h2))
    for i, q in enumerate(analysis.predicted_interview_questions, 1):
        story.append(Paragraph(f"{i}.  {q}", body))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
