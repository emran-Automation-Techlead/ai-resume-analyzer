import base64
import json
import fitz  # PyMuPDF
import anthropic

from models import CandidateProfile
from prompts import RESUME_EXTRACTION_SYSTEM, resume_extraction_user, resume_vision_user
from config import settings

# ---- Client ----
_claude = anthropic.Anthropic(api_key=settings.anthropic_api_key)


# ---- PDF text extraction ----

def extract_text_from_pdf(file_path: str) -> str:
    """Extract selectable text from a PDF using PyMuPDF."""
    doc = fitz.open(file_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages).strip()


def _has_selectable_text(text: str) -> bool:
    return len(text.strip()) > 100


# ---- Claude text parsing ----

def _parse_candidate_from_text(text: str) -> CandidateProfile:
    """Call Claude to extract a structured CandidateProfile from resume text."""
    response = _claude.messages.create(
        model=settings.claude_model,
        max_tokens=1500,
        system=RESUME_EXTRACTION_SYSTEM,
        messages=[{"role": "user", "content": resume_extraction_user(text)}]
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return CandidateProfile.model_validate(json.loads(raw.strip()))


# ---- Claude Vision parsing ----

def _parse_resume_with_vision(file_path: str) -> CandidateProfile:
    """Use Claude Vision to parse a scanned or image-based resume."""
    with open(file_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Detect media type
    suffix = file_path.lower().split(".")[-1]
    media_map = {"pdf": "application/pdf", "png": "image/png",
                 "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    media_type = media_map.get(suffix, "image/png")

    response = _claude.messages.create(
        model=settings.claude_model,
        max_tokens=1500,
        system=RESUME_EXTRACTION_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data
                    }
                },
                {"type": "text", "text": resume_vision_user()}
            ]
        }]
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return CandidateProfile.model_validate(json.loads(raw.strip()))


# ---- Public router ----

def parse_resume(file_path: str) -> tuple[CandidateProfile, str]:
    """
    Parse a resume from PDF, PNG, or JPG.
    Returns (CandidateProfile, raw_text) — raw_text used for ATS keyword matching.
    """
    suffix = file_path.lower().split(".")[-1]

    if suffix == "pdf":
        text = extract_text_from_pdf(file_path)
        if _has_selectable_text(text):
            print(f"[resume_service] Parsing PDF via text extraction ({len(text)} chars)")
            profile = _parse_candidate_from_text(text)
            return profile, text
        else:
            print("[resume_service] PDF has no selectable text — using Claude Vision")
            profile = _parse_resume_with_vision(file_path)
            return profile, profile.model_dump_json()
    else:
        print(f"[resume_service] Parsing image resume via Claude Vision ({suffix})")
        profile = _parse_resume_with_vision(file_path)
        return profile, profile.model_dump_json()
