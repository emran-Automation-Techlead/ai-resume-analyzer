import openai

from models import JobRequirements
from prompts import JOB_ANALYSIS_SYSTEM, job_analysis_user
from config import settings

# ---- Client ----
_oai = openai.OpenAI(api_key=settings.openai_api_key)


def analyze_job_description(jd_text: str) -> JobRequirements:
    """
    Extract structured JobRequirements from a job description using
    OpenAI native structured outputs (no JSON parsing needed).
    """
    completion = _oai.beta.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": JOB_ANALYSIS_SYSTEM},
            {"role": "user", "content": job_analysis_user(jd_text)}
        ],
        response_format=JobRequirements
    )
    return completion.choices[0].message.parsed


def calculate_ats_coverage(resume_text: str, job_reqs: JobRequirements) -> dict:
    """
    Compute ATS keyword coverage locally — deterministic, no hallucination risk.
    Returns coverage percentage plus found/missing keyword lists.
    """
    resume_lower = resume_text.lower()
    found = []
    missing = []

    for keyword in job_reqs.ats_keywords:
        if keyword.lower() in resume_lower:
            found.append(keyword)
        else:
            missing.append(keyword)

    total = len(job_reqs.ats_keywords)
    pct = int((len(found) / total * 100)) if total > 0 else 0

    return {
        "coverage_pct": pct,
        "found": found,
        "missing": missing
    }
