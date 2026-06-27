import json
from typing import Generator

import anthropic

from models import CandidateProfile, JobRequirements, FitAnalysis, SkillEvaluation, GapSeverity, FitLevel
from prompts import FIT_ANALYSIS_SYSTEM, fit_analysis_user, RECOMMENDATIONS_STREAM_SYSTEM, recommendations_stream_user
from config import settings

# ---- Client ----
_claude = anthropic.Anthropic(api_key=settings.anthropic_api_key)


# ---- Deterministic scoring (no AI — prevents hallucination) ----

def compute_deterministic_scores(candidate: CandidateProfile,
                                  job: JobRequirements,
                                  ats_data: dict) -> dict:
    """Compute sub-scores locally. These are passed to Claude as anchors."""
    # Skills score: how many required skills the candidate has
    req_skills_lower = [s.lower() for s in job.required_skills]
    candidate_skills_lower = [s.lower() for s in candidate.skills]
    matched = sum(1 for s in req_skills_lower if any(s in cs or cs in s for cs in candidate_skills_lower))
    skills_score = int(min(matched / max(len(req_skills_lower), 1), 1.0) * 100)

    # Experience score: candidate years vs required years
    req_years = max(job.years_experience_required, 1)
    exp_score = int(min(candidate.years_of_experience / req_years, 1.0) * 100)

    # Education score: keyword match
    edu_keywords = {"phd": 100, "doctorate": 100, "master": 85, "msc": 85,
                    "mba": 85, "bachelor": 70, "bsc": 70, "degree": 60, "diploma": 50}
    edu_lower = (candidate.education + " " + job.education_requirement).lower()
    edu_score = 50
    for kw, score in edu_keywords.items():
        if kw in edu_lower:
            edu_score = score
            break

    return {
        "skills_score": skills_score,
        "experience_score": exp_score,
        "education_score": edu_score,
        "ats_coverage_score": ats_data["coverage_pct"]
    }


def _score_to_fit_level(score: int) -> FitLevel:
    if score >= 80:
        return FitLevel.EXCELLENT
    elif score >= 60:
        return FitLevel.GOOD
    elif score >= 40:
        return FitLevel.FAIR
    return FitLevel.POOR


# ---- Claude fit analysis ----

def generate_fit_analysis(candidate: CandidateProfile,
                           job: JobRequirements,
                           ats_data: dict) -> FitAnalysis:
    """Call Claude to produce a full FitAnalysis using deterministic scores as anchors."""
    scores = compute_deterministic_scores(candidate, job, ats_data)

    response = _claude.messages.create(
        model=settings.claude_model,
        max_tokens=3000,
        system=FIT_ANALYSIS_SYSTEM,
        messages=[{
            "role": "user",
            "content": fit_analysis_user(
                candidate.model_dump_json(indent=2),
                job.model_dump_json(indent=2),
                scores
            )
        }]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())

    # Force deterministic scores — Claude cannot override them
    data["skills_score"] = scores["skills_score"]
    data["experience_score"] = scores["experience_score"]
    data["education_score"] = scores["education_score"]
    data["ats_coverage_score"] = scores["ats_coverage_score"]

    # Compute overall as weighted average
    overall = int(
        scores["skills_score"] * 0.40 +
        scores["experience_score"] * 0.30 +
        scores["education_score"] * 0.15 +
        scores["ats_coverage_score"] * 0.15
    )
    data["overall_score"] = overall
    data["fit_level"] = _score_to_fit_level(overall).value

    return FitAnalysis.model_validate(data)


# ---- Claude streaming recommendations ----

def stream_recommendations(analysis: FitAnalysis) -> Generator[str, None, None]:
    """Stream a detailed coaching narrative from Claude."""
    summary = f"""
Overall Score: {analysis.overall_score}/100 ({analysis.fit_level})
Executive Summary: {analysis.executive_summary}
Critical Gaps: {', '.join(analysis.critical_gaps)}
Preferred Gaps: {', '.join(analysis.preferred_gaps)}
Strengths: {', '.join(analysis.strengths)}
Missing ATS Keywords: {', '.join(analysis.ats_missing_keywords[:10])}
Top Recommendations: {chr(10).join(f'- {r}' for r in analysis.recommendations[:5])}
"""
    with _claude.messages.stream(
        model=settings.claude_model,
        max_tokens=1000,
        system=RECOMMENDATIONS_STREAM_SYSTEM,
        messages=[{"role": "user", "content": recommendations_stream_user(summary)}]
    ) as stream:
        for text in stream.text_stream:
            yield text
