"""Developer profile extraction agent.

Phase 3 turns the already-extracted CV database records into a developer-focused
profile. The deterministic layer guarantees a profile can be saved without an
LLM; the LLM layer refines projects, practices, role signals, and warnings when
provider credentials are available.
"""

import json
import re
from datetime import date, datetime
from typing import Any, Optional

from ..db_models import Candidate
from ..llm_client import structured_invoke
from .constants import DEVELOPER_ROLES
from .extraction_schema import DeveloperProfileExtraction, DeveloperProjectExtraction


PROGRAMMING_LANGUAGES = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
    "golang", "rust", "php", "ruby", "kotlin", "swift", "dart", "scala",
    "r", "sql", "html", "css",
}

FRAMEWORKS_LIBRARIES = {
    "react", "vue", "angular", "next.js", "nextjs", "node.js", "nodejs",
    "express", "django", "flask", "fastapi", "spring", "spring boot",
    "laravel", "rails", "asp.net", ".net", "flutter", "react native",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
}

DATABASES = {
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis",
    "oracle", "sql server", "mssql", "firebase", "dynamodb", "cassandra",
    "elasticsearch",
}

CLOUD_DEVOPS_TOOLS = {
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "jenkins", "github actions", "gitlab ci", "ci/cd", "terraform",
    "ansible", "nginx", "linux", "vercel", "netlify", "render",
}

TESTING_TOOLS = {
    "pytest", "unittest", "jest", "mocha", "cypress", "playwright",
    "selenium", "junit", "testng", "rspec", "postman",
}

ARCHITECTURE_PRACTICES = {
    "rest", "graphql", "api", "microservices", "mvc", "mvvm", "clean architecture",
    "solid", "design patterns", "authentication", "authorization", "jwt",
    "oauth", "performance", "scalability", "security", "documentation",
}

SENIORITY_KEYWORDS = [
    ("principal", "principal"),
    ("lead", "lead"),
    ("senior", "senior"),
    ("sr.", "senior"),
    ("manager", "manager"),
    ("engineer", "mid"),
    ("developer", "mid"),
    ("junior", "junior"),
    ("jr.", "junior"),
    ("intern", "intern"),
]


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        clean = str(item or "").strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _find_terms(text: str, vocabulary: set[str]) -> list[str]:
    normalized = f" {text.lower()} "
    found = []
    for term in sorted(vocabulary, key=len, reverse=True):
        pattern = r"(?<![a-z0-9+#.])" + re.escape(term.lower()) + r"(?![a-z0-9+#.])"
        if re.search(pattern, normalized):
            found.append(term)
    return _dedupe(found)


def _to_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.date()
        except ValueError:
            continue
    return None


def _month_span(start: Optional[str], end: Optional[str]) -> int:
    start_date = _to_date(start)
    end_date = _to_date(end) or date.today()
    if not start_date:
        return 0
    return max(0, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month))


def _infer_seniority(role: Optional[str]) -> Optional[str]:
    role_text = (role or "").lower()
    for keyword, level in SENIORITY_KEYWORDS:
        if keyword in role_text:
            return level
    return None


def _candidate_payload(candidate: Candidate) -> dict[str, Any]:
    education = [
        {
            "degree": row.degree,
            "field": row.field,
            "institution": row.institution,
            "start_year": row.start_year,
            "end_year": row.end_year,
        }
        for row in candidate.education or []
    ]
    experience = [
        {
            "company": row.company,
            "role": row.role,
            "employment_type": row.employment_type,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "description": row.description,
        }
        for row in candidate.experience or []
    ]
    skills = [
        {"skill_name": row.skill_name, "inferred": row.inferred}
        for row in candidate.skills or []
    ]
    publications = [
        {
            "title": row.title,
            "venue": row.venue,
            "year": row.year,
        }
        for row in candidate.publications or []
    ]
    return {
        "candidate_id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "education": education,
        "experience": experience,
        "skills": skills,
        "publications": publications,
    }


def _combined_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for skill in payload.get("skills", []):
        parts.append(skill.get("skill_name") or "")
    for exp in payload.get("experience", []):
        parts.extend([exp.get("role") or "", exp.get("company") or "", exp.get("description") or ""])
    for edu in payload.get("education", []):
        parts.extend([edu.get("degree") or "", edu.get("field") or "", edu.get("institution") or ""])
    for pub in payload.get("publications", []):
        parts.extend([pub.get("title") or "", pub.get("venue") or ""])
    return "\n".join(parts)


def deterministic_extract(candidate: Candidate, target_role: str) -> DeveloperProfileExtraction:
    payload = _candidate_payload(candidate)
    text = _combined_text(payload)

    explicit_skills = [s["skill_name"] for s in payload["skills"] if s.get("skill_name")]
    skill_text = " ".join(explicit_skills)
    all_text = f"{skill_text}\n{text}"

    current_exp = payload["experience"][-1] if payload["experience"] else {}
    current_role = current_exp.get("role")
    total_months = sum(
        _month_span(exp.get("start_date"), exp.get("end_date"))
        for exp in payload["experience"]
        if any(term in " ".join([exp.get("role") or "", exp.get("description") or ""]).lower()
               for term in ["developer", "engineer", "software", "frontend", "backend", "full stack", "programmer"])
    )

    projects = []
    work_highlights = []
    links = _dedupe(re.findall(r"https?://[^\s,)]+", all_text))

    for exp in payload["experience"]:
        desc = exp.get("description") or ""
        if desc:
            work_highlights.append(f"{exp.get('role') or 'Role'} @ {exp.get('company') or 'Company'}: {desc[:240]}")
        project_terms = _find_terms(desc, PROGRAMMING_LANGUAGES | FRAMEWORKS_LIBRARIES | DATABASES | CLOUD_DEVOPS_TOOLS)
        if desc and any(word in desc.lower() for word in ["project", "built", "developed", "implemented", "designed"]):
            projects.append(DeveloperProjectExtraction(
                name=exp.get("role"),
                description=desc[:500],
                technologies=project_terms,
                evidence_source=f"Experience: {exp.get('role') or 'Unknown'} @ {exp.get('company') or 'Unknown'}",
                links=links,
            ))

    warnings = []
    if not explicit_skills:
        warnings.append("No explicit skills were found in the stored CV data.")
    if not projects:
        warnings.append("No clearly described developer projects were detected from experience descriptions.")
    if not links:
        warnings.append("No GitHub, portfolio, or deployed project links were detected.")

    return DeveloperProfileExtraction(
        target_role=target_role,
        current_role=current_role,
        seniority_level=_infer_seniority(current_role),
        total_relevant_experience_months=total_months,
        programming_languages=_dedupe(_find_terms(all_text, PROGRAMMING_LANGUAGES)),
        frameworks_libraries=_dedupe(_find_terms(all_text, FRAMEWORKS_LIBRARIES)),
        databases=_dedupe(_find_terms(all_text, DATABASES)),
        cloud_devops_tools=_dedupe(_find_terms(all_text, CLOUD_DEVOPS_TOOLS)),
        testing_tools=_dedupe(_find_terms(all_text, TESTING_TOOLS)),
        architecture_practices=_dedupe(_find_terms(all_text, ARCHITECTURE_PRACTICES)),
        projects=projects,
        work_highlights=_dedupe(work_highlights),
        links=links,
        certifications=[
            edu["degree"] for edu in payload["education"]
            if edu.get("degree") and any(k in (edu.get("degree") or "").lower() for k in ["cert", "aws", "azure", "google"])
        ],
        extraction_warnings=warnings,
        extraction_confidence="medium" if explicit_skills or payload["experience"] else "low",
    )


def llm_refine_profile(
    payload: dict[str, Any],
    target_role: str,
    baseline: DeveloperProfileExtraction,
) -> DeveloperProfileExtraction:
    role_label = DEVELOPER_ROLES.get(target_role, target_role)
    prompt = f"""
You are the Developer Profile Extraction Agent for Talash.
Extract a developer-focused profile for target role: {role_label}.

Rules:
- Use only the candidate data and baseline hints below.
- Return data through the provided structured-output schema.
- Do not score the candidate.
- Do not invent evidence.
- Keep warnings explicit when project evidence, links, dates, or skills are missing.
- Prefer concrete evidence over generic labels.
- Set target_role exactly to "{target_role}".

Candidate data:
{json.dumps(payload, ensure_ascii=True, default=str)}

Baseline deterministic extraction:
{baseline.model_dump_json()}
"""
    refined = structured_invoke(prompt, DeveloperProfileExtraction)
    refined.target_role = target_role
    return refined


def extract_developer_profile(candidate: Candidate, target_role: str) -> DeveloperProfileExtraction:
    payload = _candidate_payload(candidate)
    baseline = deterministic_extract(candidate, target_role)
    try:
        return llm_refine_profile(payload, target_role, baseline)
    except Exception as e:
        baseline.extraction_warnings.append(f"LLM refinement unavailable; deterministic extraction used. Reason: {e}")
        return baseline


def profile_to_storage(profile: DeveloperProfileExtraction) -> dict[str, Any]:
    data = profile.model_dump()
    return {
        "target_role": profile.target_role,
        "current_role": profile.current_role,
        "seniority_level": profile.seniority_level,
        "total_relevant_experience_months": profile.total_relevant_experience_months,
        "programming_languages": _json_dumps(data["programming_languages"]),
        "frameworks_libraries": _json_dumps(data["frameworks_libraries"]),
        "databases": _json_dumps(data["databases"]),
        "cloud_devops_tools": _json_dumps(data["cloud_devops_tools"]),
        "testing_tools": _json_dumps(data["testing_tools"]),
        "architecture_practices": _json_dumps(data["architecture_practices"]),
        "projects": _json_dumps(data["projects"]),
        "work_highlights": _json_dumps(data["work_highlights"]),
        "links": _json_dumps(data["links"]),
        "certifications": _json_dumps(data["certifications"]),
        "extraction_warnings": _json_dumps(data["extraction_warnings"]),
        "raw_profile_json": _json_dumps(data),
        "extraction_confidence": profile.extraction_confidence,
    }
