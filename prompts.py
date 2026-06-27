# ---- Resume Parsing ----

RESUME_EXTRACTION_SYSTEM = """You are an expert resume parser. Extract all information from the resume provided.
Return a JSON object that exactly matches this structure:
{
  "name": "full name",
  "current_title": "most recent job title",
  "years_of_experience": <integer>,
  "skills": ["skill1", "skill2", ...],
  "education": "highest degree and field",
  "certifications": ["cert1", ...],
  "notable_achievements": ["achievement1", ...],
  "summary_statement": "brief professional summary"
}
Be precise. Only include what is explicitly stated in the resume."""

def resume_extraction_user(text: str) -> str:
    return f"Parse this resume and return structured JSON:\n\n{text}"

def resume_vision_user() -> str:
    return "Parse this resume image and return structured JSON matching the schema in your instructions."


# ---- Job Description Analysis ----

JOB_ANALYSIS_SYSTEM = """You are a job requirements analyst. Extract structured requirements from the job description.
Identify ALL required and preferred skills, responsibilities, and ATS keywords."""


def job_analysis_user(jd_text: str) -> str:
    return f"Analyse this job description and extract structured requirements:\n\n{jd_text}"


# ---- Fit Analysis ----

FIT_ANALYSIS_SYSTEM = """You are a senior technical recruiter with 15 years of experience.
Analyse the candidate profile against the job requirements and produce a detailed fit analysis.
Be honest and specific. Base scores on the deterministic values provided — do not change them.
Return a JSON object matching the FitAnalysis schema exactly."""

def fit_analysis_user(candidate_json: str, job_json: str, scores: dict) -> str:
    return f"""Analyse this candidate against this job. Use these pre-computed scores as anchors:
- skills_score: {scores['skills_score']}
- experience_score: {scores['experience_score']}
- education_score: {scores['education_score']}
- ats_coverage_score: {scores['ats_coverage_score']}

CANDIDATE:
{candidate_json}

JOB REQUIREMENTS:
{job_json}

Return a complete FitAnalysis JSON with skill_evaluations for every required skill,
3-5 strengths, all critical gaps, all preferred gaps, missing ATS keywords,
5 prioritised recommendations, 6-8 predicted interview questions, and a 3-sentence executive summary."""


# ---- Streaming Recommendations ----

RECOMMENDATIONS_STREAM_SYSTEM = """You are a career coach giving detailed, actionable advice.
Write in a warm, direct tone. Be specific — reference actual skills and gaps from the analysis."""

def recommendations_stream_user(analysis_summary: str) -> str:
    return f"""Based on this fit analysis, write a detailed 400-500 word coaching narrative covering:
1. Overall assessment and what the score means
2. Top 3 strengths to emphasise in the application
3. How to address the critical gaps (be specific and practical)
4. ATS optimisation tips for this specific role
5. One piece of honest advice about this application

Analysis summary:
{analysis_summary}"""
