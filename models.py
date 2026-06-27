from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ---- Enums ----

class FitLevel(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"

class GapSeverity(str, Enum):
    CRITICAL = "Critical"
    PREFERRED = "Preferred"
    NICE_TO_HAVE = "Nice to Have"


# ---- Job Description Models ----

class JobRequirements(BaseModel):
    job_title: str
    company: str = ""
    required_skills: List[str]
    preferred_skills: List[str]
    years_experience_required: int = 0
    education_requirement: str = ""
    key_responsibilities: List[str]
    ats_keywords: List[str]
    seniority_level: str = "mid"


# ---- Resume / Candidate Models ----

class CandidateProfile(BaseModel):
    name: str = "Candidate"
    current_title: str = ""
    years_of_experience: int = 0
    skills: List[str]
    education: str = ""
    certifications: List[str] = []
    notable_achievements: List[str] = []
    summary_statement: str = ""


# ---- Analysis Models ----

class SkillEvaluation(BaseModel):
    skill: str
    required: bool
    candidate_has: bool
    severity: GapSeverity
    recommendation: str


class FitAnalysis(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    fit_level: FitLevel
    skills_score: int = Field(ge=0, le=100)
    experience_score: int = Field(ge=0, le=100)
    education_score: int = Field(ge=0, le=100)
    ats_coverage_score: int = Field(ge=0, le=100)
    skill_evaluations: List[SkillEvaluation]
    strengths: List[str]
    critical_gaps: List[str]
    preferred_gaps: List[str]
    ats_missing_keywords: List[str]
    recommendations: List[str]
    predicted_interview_questions: List[str]
    executive_summary: str
