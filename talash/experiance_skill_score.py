# ============================================================
# experience_skill_score.py
# Complete module for Module 3.8 (Professional Experience)
# and Module 3.9 (Skill Alignment) scoring
# ============================================================

import asyncio
import json
from datetime import date, datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import re
import os
from typing import Optional

from db_models import Candidate, ProfessionalExperienceScore, SkillAlignmentScore
from llm_client import litellm_chat

load_dotenv()

#  Scoring weights 
# Module 3.8  Professional Experience            60 pts
#    Timeline Consistency                      20 pts
#        gap_detection          8
#        overlap_analysis       6
#        gap_justification      6
#    Career Progression                        25 pts
#        role_seniority        10
#        tenure_consistency     8
#        domain_continuity      7
#    Data Quality Bonus                        15 pts
#
# Module 3.9  Skill Alignment                    40 pts
#    Skill-to-Experience                       18 pts
#    Skill-to-Publication                      12 pts
#    Skill Consistency                         10 pts
#
# NOTE: Module 3.9 is skipped when ALL skills are inferred.
#       In that case the 3.8 raw score is rescaled to /100.
# 

WEIGHTS = {
    # 3.8 Timeline
    "gap_detection":      8,
    "overlap_analysis":   6,
    "gap_justification":  6,
    # 3.8 Career
    "role_seniority":    10,
    "tenure_consistency": 8,
    "domain_continuity":  7,
    # 3.8 Data bonus
    "data_quality":      15,
    # 3.9 Skill
    "skill_experience":  18,
    "skill_publication": 12,
    "skill_consistency": 10,
}

MAX_38 = 60
MAX_39 = 40

SENIORITY_MAP = {
    # intern / student
    "intern": 1, "trainee": 1, "student": 1,
    # junior
    "junior": 2, "jr": 2, "entry": 2, "graduate": 2,
    # mid-level
    "engineer": 3, "developer": 3, "analyst": 3,
    "officer": 3, "coordinator": 3, "lecturer": 3,
    "support": 3, "executive": 3, "specialist": 3,
    # senior
    "senior": 4, "sr": 4, "lead": 4, "principal": 4,
    "head": 4, "assistant professor": 4,
    # management
    "manager": 5, "director": 5, "associate professor": 5,
    "program": 5, "superintendent": 5,
    # executive
    "professor": 6, "vp": 6, "vice president": 6,
    "cto": 6, "ceo": 6, "chief": 6, "partner": 6,
}

ACADEMIC_KEYWORDS = {
    "engineering", "computer", "electrical", "software", "technology",
    "science", "it", "information", "networks", "systems", "data",
    "ai", "ml", "research",
}

GAP_JUSTIFY_KEYWORDS = {
    "phd", "ms", "msc", "master", "bachelor", "study", "studying",
    "research", "freelance", "consulting", "training", "sabbatical",
    "family", "health", "startup", "entrepreneur",
}

TODAY = date.today()


# ============================================================
# UTILITIES
# ============================================================

def _to_date(val):
    """Normalize a date string or date/datetime to a date object."""
    if val is None:
        return TODAY
    if isinstance(val, date):
        return val if not isinstance(val, datetime) else val.date()
    if isinstance(val, str):
        val = val.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return TODAY


def _months(start, end):
    """Positive month difference between two date objects."""
    d1 = _to_date(start)
    d2 = _to_date(end)
    diff = (d2.year - d1.year) * 12 + (d2.month - d1.month)
    return max(0, diff)


# ============================================================
# CELL 2  Data Loader
# ============================================================

def load_candidate(candidate_id: int) -> dict | None:
    """
    Load a candidate from the database exactly as the existing
    pipeline does.  Returns the same dict structure your codebase
    already produces, or None if not found.
    """
    # Import here to delay database engine creation until first use
    from db_connect import get_session
    
    session = get_session()
    try:
        cand = session.query(Candidate).filter_by(id=candidate_id).first()
        if not cand:
            return None
        return {
            "id": cand.id,
            "candidate_id": cand.candidate_id,
            "name": cand.name,
            "email": cand.email,
            "phone": cand.phone,
            "education": [
                {
                    "id": e.id,
                    "degree": e.degree,
                    "degree_level": e.degree_level,
                    "field": e.field,
                    "institution": e.institution,
                    "start_year": e.start_year,
                    "end_year": e.end_year,
                }
                for e in cand.education
            ],
            "experience": [
                {
                    "id": ex.id,
                    "company": ex.company,
                    "role": ex.role,
                    "employment_type": ex.employment_type,
                    "start_date": ex.start_date,
                    "end_date": ex.end_date,
                    "description": ex.description,
                }
                for ex in cand.experience
            ],
            "skills": [
                {"id": s.id, "skill_name": s.skill_name, "inferred": s.inferred}
                for s in cand.skills
            ],
            "publications": [
                {
                    "id": p.id,
                    "pub_type": p.pub_type.value if p.pub_type else None,
                    "title": p.title,
                    "venue": p.venue,
                    "year": p.year,
                    "authors": p.authors,
                    "authorship_role": p.authorship_role.value if p.authorship_role else None,
                    "wos_indexed": p.wos_indexed,
                    "scopus_indexed": p.scopus_indexed,
                    "quartile": p.quartile,
                    "impact_factor": p.impact_factor,
                    "journal_name": p.journal_name,
                    "conference_name": p.conference_name,
                }
                for p in cand.publications
            ],
        }
    finally:
        session.close()


# ============================================================
# CELL 3  Timeline Analysis  (Module 3.8  sub-component i)
# ============================================================

def _overlaps(s1, e1, s2, e2):
    """Return overlap in months between two date ranges, or 0."""
    a = max(_to_date(s1), _to_date(s2))
    b = min(_to_date(e1), _to_date(e2))
    return max(0, _months(a, b))


def analyse_timeline(experience: list, education: list) -> dict:
    exp_sorted = sorted(
        experience,
        key=lambda x: _to_date(x.get("start_date")),
    )

    gaps = []
    job_overlaps = []
    edu_overlaps = []
    flags = []

    #  Gap detection between jobs 
    for i in range(len(exp_sorted) - 1):
        cur   = exp_sorted[i]
        nxt   = exp_sorted[i + 1]
        end   = _to_date(cur.get("end_date"))
        start = _to_date(nxt.get("start_date"))
        gap_m = _months(end, start)
        if gap_m >= 2:
            justified = False
            for edu in education:
                edu_s_yr = edu.get("start_year") or (edu.get("end_year", 2000) - 4)
                edu_e_yr = edu.get("end_year") or edu_s_yr + 4
                edu_s = date(edu_s_yr, 1, 1)
                edu_e = date(edu_e_yr, 12, 31)
                if _overlaps(end, start, edu_s, edu_e) > 0:
                    justified = True
                    break
            gaps.append({
                "period":      f"{end.strftime('%Y-%m')}  {start.strftime('%Y-%m')}",
                "months":      gap_m,
                "preceded_by": f"{cur['role']} @ {cur['company']}",
                "followed_by": f"{nxt['role']} @ {nxt['company']}",
                "justified":   justified,
            })
            if not justified and gap_m > 12:
                flags.append(
                    f"MAJOR GAP ({gap_m}m): {end.strftime('%Y-%m')}  "
                    f"{start.strftime('%Y-%m')}  unexplained"
                )
            elif not justified and gap_m > 6:
                flags.append(
                    f"SIGNIFICANT GAP ({gap_m}m): {end.strftime('%Y-%m')}  "
                    f"{start.strftime('%Y-%m')}"
                )

    #  Job-to-job overlap detection 
    for i in range(len(exp_sorted)):
        for j in range(i + 1, len(exp_sorted)):
            a = exp_sorted[i]
            b = exp_sorted[j]
            ov = _overlaps(
                a.get("start_date"), a.get("end_date"),
                b.get("start_date"), b.get("end_date"),
            )
            if ov > 0:
                et_a = (a.get("employment_type") or "").lower()
                et_b = (b.get("employment_type") or "").lower()
                part_time = any(k in et_a + et_b for k in
                                ["part", "consult", "freelance", "contract", "visiting"])
                concern = "reasonable" if (ov <= 2 or part_time) else "review_needed"
                if ov > 6 and not part_time:
                    concern = "concerning"
                job_overlaps.append({
                    "job_a":         f"{a['role']} @ {a['company']}",
                    "job_b":         f"{b['role']} @ {b['company']}",
                    "months":        ov,
                    "concern_level": concern,
                })
                if concern == "concerning":
                    flags.append(
                        f"JOB OVERLAP ({ov}m): '{a['role']}' and '{b['role']}'  full-time?"
                    )

    #  Education vs Employment overlap 
    for edu in education:
        edu_s_yr = edu.get("start_year") or (edu.get("end_year", 2000) - 4)
        edu_e_yr = edu.get("end_year") or edu_s_yr + 4
        edu_s = date(edu_s_yr, 1, 1)
        edu_e = date(edu_e_yr, 12, 31)
        for job in exp_sorted:
            ov = _overlaps(
                job.get("start_date"), job.get("end_date"),
                edu_s, edu_e,
            )
            if ov > 0:
                et = (job.get("employment_type") or "").lower()
                academic_role = any(k in (job.get("role") or "").lower()
                                    for k in ["research", "assistant", "lecturer",
                                              "teach", "tutor", "professor"])
                part_time = any(k in et for k in ["part", "research", "teaching"])
                concern = "reasonable" if (part_time or academic_role) else "review_needed"
                edu_overlaps.append({
                    "edu":   f"{edu['degree']} @ {edu.get('institution', '?')} (end {edu_e_yr})",
                    "job":   f"{job['role']} @ {job['company']}",
                    "months": ov,
                    "concern_level": concern,
                })

    return {
        "gaps":         gaps,
        "job_overlaps": job_overlaps,
        "edu_overlaps": edu_overlaps,
        "flags":        flags,
    }


# ============================================================
# CELL 4  Career Progression  (Module 3.8  sub-component ii)
# ============================================================

def _job_seniority(role: str) -> int:
    """Map a job title to a 1-6 seniority integer."""
    if not role:
        return 2
    r = role.lower()
    for key, lvl in sorted(SENIORITY_MAP.items(), key=lambda x: -len(x[0])):
        if key in r:
            return lvl
    return 2  # default: mid-level unknown


def analyse_career(experience: list) -> dict:
    if not experience:
        return {
            "seniority_trajectory": [],
            "seniority_trend": "flat",
            "avg_tenure_months": 0,
            "domain_continuity": "weak",
            "total_experience_months": 0,
            "notes": ["No experience records found."],
        }

    exp_sorted = sorted(experience, key=lambda x: _to_date(x.get("start_date")))
    trajectory = []
    domains    = []
    tenures    = []
    notes      = []

    for job in exp_sorted:
        start   = _to_date(job.get("start_date"))
        end     = _to_date(job.get("end_date"))
        tenure  = _months(start, end)
        tenures.append(tenure)
        seniority = _job_seniority(job.get("role", ""))
        trajectory.append({
            "role":            job.get("role", "?"),
            "company":         job.get("company", "?"),
            "seniority_level": seniority,
            "months":          tenure,
        })
        role_words = set((job.get("role") or "").lower().split())
        comp_words = set((job.get("company") or "").lower().split())
        combined   = role_words | comp_words
        if combined & ACADEMIC_KEYWORDS:
            domains.append("academic_tech")
        else:
            domains.append("other")

    #  Seniority trend 
    levels = [t["seniority_level"] for t in trajectory]
    if len(levels) >= 2:
        delta = levels[-1] - levels[0]
        if delta >= 2:
            trend = "rising"
        elif delta >= 0:
            trend = "flat"
        else:
            trend = "declining"
            notes.append("Seniority appears to decline  verify role titles.")
    else:
        trend = "flat"

    #  Tenure note 
    avg_tenure = sum(tenures) / len(tenures) if tenures else 0
    if avg_tenure < 12:
        notes.append(f"Short average tenure ({avg_tenure:.0f}m)  possible job-hopping.")
    elif avg_tenure >= 48:
        notes.append(f"Long average tenure ({avg_tenure:.0f}m)  good stability.")

    #  Domain continuity 
    unique_domains = set(domains)
    if len(unique_domains) == 1:
        domain_cont = "strong"
    elif len(unique_domains) <= 2:
        domain_cont = "moderate"
    else:
        domain_cont = "weak"

    total_months = sum(tenures)

    return {
        "seniority_trajectory":    trajectory,
        "seniority_trend":         trend,
        "avg_tenure_months":       round(avg_tenure, 1),
        "domain_continuity":       domain_cont,
        "total_experience_months": total_months,
        "notes":                   notes,
    }


# ============================================================
# CELL 5  Skill Alignment  (Module 3.9)  LLM-Powered
# ============================================================

#  Pydantic Structured Output Schema 

class SkillDetail(BaseModel):
    skill: str = Field(
        description="The skill name exactly as listed by the candidate"
    )
    evidence_strength: str = Field(
        description="One of: STRONG, PARTIAL, WEAK, UNSUPPORTED"
    )
    exp_evidence: str = Field(
        description="What experience evidence was found, or 'None found'"
    )
    pub_evidence: str = Field(
        description="What publication evidence was found, or 'None found'"
    )
    exp_match_count: int = Field(
        description="Number of experience entries that support this skill (0 if none)"
    )
    pub_match_count: int = Field(
        description="Number of publications that support this skill (0 if none)"
    )
    source_diversity: int = Field(
        description="Score 0-3: 0=no evidence, 1=publications only, 2=experience only, 3=both sources"
    )
    reasoning: str = Field(
        description="1-2 sentence explanation of the evidence strength assigned"
    )


class SkillScores(BaseModel):
    skill_experience: float = Field(
        description="Score 0-18: how well skills are backed by experience entries"
    )
    skill_publication: float = Field(
        description="Score 0-12: how well skills are backed by publications"
    )
    skill_consistency: float = Field(
        description="Score 0-10: consistency and diversity of evidence across all skills"
    )


class SkillScoreReasons(BaseModel):
    skill_experience: str = Field(
        description="1-2 sentence reason explaining the skill_experience score given"
    )
    skill_publication: str = Field(
        description="1-2 sentence reason explaining the skill_publication score given"
    )
    skill_consistency: str = Field(
        description="1-2 sentence reason explaining the skill_consistency score given"
    )


class SkillAlignmentResult(BaseModel):
    skill_details: list[SkillDetail] = Field(
        description="One entry per explicit skill  ALL skills evaluated in a single pass"
    )
    scores: SkillScores
    score_reasons: SkillScoreReasons


def _extract_json_from_response(text: str) -> str:
    """Robustly extract JSON from LLM response with markdown fences."""
    # Strategy 1: remove markdown fences
    cleaned = re.sub(
        r"^```json\s*|^```\s*|```\s*$", "", text, flags=re.MULTILINE
    ).strip()

    if cleaned.startswith("{"):
        return cleaned

    # Strategy 2: find outermost JSON object
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return cleaned


def analyse_skills(
    skills: list,
    experience: list,
    publications: list,
) -> dict | None:
    """
    LLM-powered skill alignment (Module 3.9).
    One structured LLM call evaluates ALL explicit skills at once.

    Returns
    -------
    {
      "applicable": bool,
      "reason":     str,
      "skill_details": [ { skill, evidence_strength, exp_match_count,
                           pub_match_count, source_diversity, reasoning,
                           exp_evidence, pub_evidence } ],
      "strong_count":      int,
      "partial_count":     int,
      "weak_count":        int,
      "unsupported_count": int,
      "llm_scores":        { skill_experience, skill_publication, skill_consistency },
      "llm_score_reasons": { skill_experience, skill_publication, skill_consistency },
    }
    """
    #  Guard: no skills 
    if not skills:
        return {
            "applicable": False,
            "reason": "No skills listed in CV.",
            "skill_details": [],
            "strong_count": 0, "partial_count": 0,
            "weak_count": 0, "unsupported_count": 0,
        }

    #  Guard: all inferred  skip module 
    all_inferred = all(s.get("inferred", False) for s in skills)
    if all_inferred:
        return {
            "applicable": False,
            "reason": (
                "All skills are LLM-inferred (inferred=True). "
                "Module 3.9 not scored  explicit skill claims required."
            ),
            "skill_details": [],
            "strong_count": 0, "partial_count": 0,
            "weak_count": 0, "unsupported_count": 0,
        }

    explicit_skills = [s for s in skills if not s.get("inferred", False)]

    #  Build prompt 
    skills_list = "\n".join(f"- {s['skill_name']}" for s in explicit_skills)

    exp_text = ""
    for i, job in enumerate(experience, 1):
        exp_text += (
            f"\n[EXP {i}]"
            f" Role: {job.get('role', 'N/A')} |"
            f" Company: {job.get('company', 'N/A')}\n"
            f"  Description: {job.get('description') or 'No description provided.'}\n"
        )

    pub_text = ""
    for i, pub in enumerate(publications, 1):
        venue = (
            pub.get("journal_name")
            or pub.get("conference_name")
            or pub.get("venue")
            or "N/A"
        )
        pub_text += (
            f"\n[PUB {i}]"
            f" Title: {pub.get('title', 'N/A')} |"
            f" Venue: {venue}\n"
        )

    prompt = f"""You are an expert CV evaluator assessing skill evidence for a job application.

Evaluate how well each listed skill is supported by the candidate's experience
and publications. Be SEMANTIC  do not just match keywords literally.

Examples of semantic matching:
   "PyTorch"     also supported by "neural network training", "deep learning framework", "model implementation"
   "Docker"      also supported by "containerization", "deployment pipeline", "DevOps"
   "FastAPI"     also supported by "REST API", "backend service", "Python web framework"
   "LangChain"   also supported by "LLM orchestration", "AI pipeline", "RAG system"
   "spaCy"       also supported by "NLP pipeline", "named entity recognition", "text processing"


SKILLS TO EVALUATE  (evaluate ALL of them  one entry per skill)

{skills_list}


EXPERIENCE RECORDS

{exp_text if exp_text.strip() else "No experience records provided."}


PUBLICATIONS

{pub_text if pub_text.strip() else "No publications provided."}


EVIDENCE STRENGTH RULES

STRONG       skill evidenced in 2+ experience entries AND at least 1 publication
PARTIAL      skill evidenced in experience entries OR in publications with reasonable depth
WEAK         single indirect mention or loosely related context found
UNSUPPORTED  no meaningful link found in any experience or publication

FIELD RULES
  exp_match_count  : count of [EXP N] entries that support this skill
  pub_match_count  : count of [PUB N] entries that support this skill
  source_diversity : 0 = no evidence | 1 = publications only | 2 = experience only | 3 = both


SCORING RULES  (assign holistically across ALL skills)

  skill_experience  018 : proportion + quality of skills backed by experience
  skill_publication 012 : proportion + quality of skills backed by publications
  skill_consistency 010 : average source diversity and consistency across all skills

REQUIRED JSON OUTPUT (return ONLY valid JSON, no markdown, no preamble):
{{
  "skill_details": [
    {{
      "skill": "skill name",
      "evidence_strength": "STRONG|PARTIAL|WEAK|UNSUPPORTED",
      "exp_match_count": <int>,
      "pub_match_count": <int>,
      "source_diversity": <0-3>,
      "exp_evidence": "description or 'None found'",
      "pub_evidence": "description or 'None found'",
      "reasoning": "explanation"
    }}
  ],
  "scores": {{
    "skill_experience": <0-18>,
    "skill_publication": <0-12>,
    "skill_consistency": <0-10>
  }},
  "score_reasons": {{
    "skill_experience": "reason",
    "skill_publication": "reason",
    "skill_consistency": "reason"
  }}
}}

Return {len(explicit_skills)} entries  one per skill above."""

    #  Single LLM call 
    print(f"     Evaluating {len(explicit_skills)} skill(s) with LLM...")
    try:
        result_raw = litellm_chat(prompt)
        content_llm = result_raw.content
        
        # Robustly extract JSON
        json_str = _extract_json_from_response(content_llm)
        result = SkillAlignmentResult.model_validate_json(json_str)
    except Exception as e:
        print(f"      LLM skill evaluation failed: {e}")
        return {
            "applicable": False,
            "reason": f"LLM evaluation failed: {str(e)}",
            "skill_details": [],
            "strong_count": 0, "partial_count": 0,
            "weak_count": 0, "unsupported_count": 0,
        }

    #  Convert Pydantic  plain dict for rest of pipeline 
    skill_details_dict = []
    counts = {"STRONG": 0, "PARTIAL": 0, "WEAK": 0, "UNSUPPORTED": 0}

    for d in result.skill_details:
        strength = d.evidence_strength.upper().strip()
        if strength not in counts:
            strength = "UNSUPPORTED"
        counts[strength] += 1
        skill_details_dict.append({
            "skill":             d.skill,
            "inferred":          False,
            "exp_match_count":   d.exp_match_count,
            "pub_match_count":   d.pub_match_count,
            "source_diversity":  d.source_diversity,
            "evidence_strength": strength,
            "exp_roles":         [d.exp_evidence],
            "pub_titles":        [d.pub_evidence],
            "reasoning":         d.reasoning,
        })

    return {
        "applicable":        True,
        "reason":            f"{len(explicit_skills)} explicit skill(s) evaluated by LLM.",
        "skill_details":     skill_details_dict,
        "strong_count":      counts["STRONG"],
        "partial_count":     counts["PARTIAL"],
        "weak_count":        counts["WEAK"],
        "unsupported_count": counts["UNSUPPORTED"],
        #  LLM-assigned scores & reasons (consumed by score_39) 
        "llm_scores": {
            "skill_experience":  result.scores.skill_experience,
            "skill_publication": result.scores.skill_publication,
            "skill_consistency": result.scores.skill_consistency,
        },
        "llm_score_reasons": {
            "skill_experience":  result.score_reasons.skill_experience,
            "skill_publication": result.score_reasons.skill_publication,
            "skill_consistency": result.score_reasons.skill_consistency,
        },
    }


# ============================================================
# CELL 6  Scoring Engine
# ============================================================

def _grade(score: float) -> str:
    if score >= 85: return "STRONG"
    if score >= 70: return "GOOD"
    if score >= 55: return "SATISFACTORY"
    return "WEAK"


def score_38(timeline: dict, career: dict, experience: list, education: list) -> dict:
    """Compute Module 3.8 raw score (out of 60) with per-component breakdown."""
    reasons = {}
    W = WEIGHTS

    #  (A) Gap Detection  8 pts 
    gaps    = timeline["gaps"]
    major   = sum(1 for g in gaps if g["months"] > 12 and not g["justified"])
    signif  = sum(1 for g in gaps if 6 < g["months"] <= 12 and not g["justified"])
    minor   = sum(1 for g in gaps if 2 < g["months"] <= 6  and not g["justified"])

    gap_score  = W["gap_detection"]
    gap_score -= major  * 4
    gap_score -= signif * 2
    gap_score -= minor  * 0.5
    gap_score  = max(0.0, gap_score)

    reasons["gap_detection"] = (
        f"{len(gaps)} gap(s) found: "
        f"{major} major, {signif} significant, {minor} minor | "
        f"score {gap_score:.1f}/{W['gap_detection']}"
    )

    #  (B) Overlap Analysis  6 pts 
    concerning = sum(1 for o in timeline["job_overlaps"] if o["concern_level"] == "concerning")
    review     = sum(1 for o in timeline["job_overlaps"] if o["concern_level"] == "review_needed")

    overlap_score  = W["overlap_analysis"]
    overlap_score -= concerning * 3
    overlap_score -= review     * 1
    overlap_score  = max(0.0, overlap_score)

    reasons["overlap_analysis"] = (
        f"{len(timeline['job_overlaps'])} job overlap(s): "
        f"{concerning} concerning, {review} review-needed | "
        f"score {overlap_score:.1f}/{W['overlap_analysis']}"
    )

    #  (C) Gap Justification  6 pts 
    unjustified    = [g for g in gaps if not g["justified"]]
    gap_just_score = W["gap_justification"]
    if unjustified:
        gap_just_score -= min(len(unjustified) * 1.5, W["gap_justification"])
    gap_just_score = max(0.0, gap_just_score)

    reasons["gap_justification"] = (
        f"{len(unjustified)} unjustified gap(s) | "
        f"score {gap_just_score:.1f}/{W['gap_justification']}"
    )

    #  (D) Role Seniority / Progression  10 pts 
    traj  = career["seniority_trajectory"]
    trend = career["seniority_trend"]

    seniority_score = 0.0
    if trend == "rising":
        seniority_score = W["role_seniority"]
    elif trend == "flat":
        if traj:
            max_level = max(t["seniority_level"] for t in traj)
            seniority_score = min(W["role_seniority"], max_level * 1.5)
        else:
            seniority_score = 0
    else:  # declining
        seniority_score = W["role_seniority"] * 0.3

    reasons["role_seniority"] = (
        f"Trend: {trend} | max level reached: "
        f"{max((t['seniority_level'] for t in traj), default=0)} | "
        f"score {seniority_score:.1f}/{W['role_seniority']}"
    )

    #  (E) Tenure Consistency  8 pts 
    avg_t = career["avg_tenure_months"]
    if avg_t >= 36:
        tenure_score = W["tenure_consistency"]
    elif avg_t >= 24:
        tenure_score = W["tenure_consistency"] * 0.8
    elif avg_t >= 12:
        tenure_score = W["tenure_consistency"] * 0.5
    else:
        tenure_score = W["tenure_consistency"] * 0.2

    reasons["tenure_consistency"] = (
        f"Avg tenure: {avg_t:.0f}m | "
        f"score {tenure_score:.1f}/{W['tenure_consistency']}"
    )

    #  (F) Domain Continuity  7 pts 
    dc_map       = {"strong": 7.0, "moderate": 4.5, "weak": 2.0}
    domain_score = dc_map.get(career["domain_continuity"], 2.0)

    reasons["domain_continuity"] = (
        f"Domain continuity: {career['domain_continuity']} | "
        f"score {domain_score:.1f}/{W['domain_continuity']}"
    )

    #  (G) Data Quality Bonus  15 pts 
    dq = W["data_quality"]
    missing_type      = sum(1 for e in experience if not e.get("employment_type"))
    missing_desc      = sum(1 for e in experience if not e.get("description"))
    missing_edu_start = sum(1 for e in education  if not e.get("start_year"))

    dq -= missing_type      * 1.5
    dq -= missing_desc      * 1.0
    dq -= missing_edu_start * 0.5
    dq  = max(0.0, dq)

    reasons["data_quality"] = (
        f"Missing emp_type: {missing_type} | "
        f"missing description: {missing_desc} | "
        f"missing edu start_year: {missing_edu_start} | "
        f"score {dq:.1f}/{W['data_quality']}"
    )

    raw = (
        gap_score + overlap_score + gap_just_score
        + seniority_score + tenure_score + domain_score
        + dq
    )
    raw = min(raw, MAX_38)

    return {
        "scores": {
            "gap_detection":     round(gap_score, 1),
            "overlap_analysis":  round(overlap_score, 1),
            "gap_justification": round(gap_just_score, 1),
            "role_seniority":    round(seniority_score, 1),
            "tenure_consistency":round(tenure_score, 1),
            "domain_continuity": round(domain_score, 1),
            "data_quality":      round(dq, 1),
        },
        "reasons": reasons,
        "raw":     round(raw, 1),
        "max":     MAX_38,
    }


def score_39(skill_analysis: dict) -> dict:
    """
    Module 3.9 score (out of 40).
    Uses LLM-assigned scores directly  no recomputation.
    Returns applicable=False when all skills are inferred.
    """
    if not skill_analysis or not skill_analysis.get("applicable"):
        return {
            "applicable": False,
            "reason": (skill_analysis or {}).get("reason", "Skill module not applicable."),
            "scores": {
                "skill_experience":  0,
                "skill_publication": 0,
                "skill_consistency": 0,
            },
            "reasons": {},
            "raw": 0,
            "max": MAX_39,
        }

    #  Read LLM scores directly 
    llm_scores  = skill_analysis["llm_scores"]
    llm_reasons = skill_analysis["llm_score_reasons"]

    # Clamp to valid weight ranges (safety net)
    skill_exp_score   = round(min(max(llm_scores["skill_experience"],  0), WEIGHTS["skill_experience"]),  1)
    skill_pub_score   = round(min(max(llm_scores["skill_publication"], 0), WEIGHTS["skill_publication"]), 1)
    consistency_score = round(min(max(llm_scores["skill_consistency"], 0), WEIGHTS["skill_consistency"]), 1)

    raw = min(skill_exp_score + skill_pub_score + consistency_score, MAX_39)

    reasons = {
        "skill_experience":  (
            f"score {skill_exp_score}/{WEIGHTS['skill_experience']} | "
            f"{llm_reasons['skill_experience']}"
        ),
        "skill_publication": (
            f"score {skill_pub_score}/{WEIGHTS['skill_publication']} | "
            f"{llm_reasons['skill_publication']}"
        ),
        "skill_consistency": (
            f"score {consistency_score}/{WEIGHTS['skill_consistency']} | "
            f"{llm_reasons['skill_consistency']}"
        ),
    }

    return {
        "applicable": True,
        "reason":     skill_analysis["reason"],
        "scores": {
            "skill_experience":  skill_exp_score,
            "skill_publication": skill_pub_score,
            "skill_consistency": consistency_score,
        },
        "reasons": reasons,
        "raw":     round(raw, 1),
        "max":     MAX_39,
    }


def combine_scores(s38: dict, s39: dict) -> dict:
    """
    If 3.9 is not applicable, rescale 3.8 to 100.
    Otherwise sum both modules.
    """
    if not s39.get("applicable"):
        rescaled = round(s38["raw"] / MAX_38 * 100, 1)
        return {
            "module_38_raw": s38["raw"],
            "module_39_raw": None,
            "final_score":   rescaled,
            "note": "Module 3.9 not applicable (inferred skills). Score rescaled from 3.8 only.",
            "grade": _grade(rescaled),
        }
    total = s38["raw"] + s39["raw"]
    return {
        "module_38_raw": s38["raw"],
        "module_39_raw": s39["raw"],
        "final_score":   round(total, 1),
        "note": "Both modules scored.",
        "grade": _grade(total),
    }


# ============================================================
# CELL 7  Report Printer & Email Generator
# ============================================================

_BAR_WIDTH = 16

def _bar(score, max_score):
    filled = round(_BAR_WIDTH * score / max_score) if max_score else 0
    return "█" * filled + "░" * (_BAR_WIDTH - filled)

def _pct(score, max_score):
    return f"{100*score/max_score:.1f}%" if max_score else "N/A"


def print_experience_report(
    name: str,
    s38: dict,
    s39: dict,
    combined: dict,
    timeline: dict,
    career: dict,
    skill_analysis: dict,
):
    W    = WEIGHTS
    sc38 = s38["scores"]
    sc39 = s39.get("scores", {})
    sep  = "═" * 60
    dash = "─" * 60

    print(f"\n{sep}")
    print(f"  PROFESSIONAL EXPERIENCE & SKILL ALIGNMENT REPORT")
    print(f"  {name}")
    print(f"{sep}\n")

    #  Module 3.8 
    print("   MODULE 3.8  Professional Experience \n")
    print(f"  {'Timeline Consistency':30s} "
          f"{sc38['gap_detection']+sc38['overlap_analysis']+sc38['gap_justification']:5.1f} / "
          f"{W['gap_detection']+W['overlap_analysis']+W['gap_justification']}")
    print(f"    Gap Detection           {sc38['gap_detection']:5.1f} / {W['gap_detection']}   "
          f"[{_bar(sc38['gap_detection'],    W['gap_detection'])}]  "
          f"{_pct(sc38['gap_detection'],    W['gap_detection'])}")
    print(f"    Overlap Analysis        {sc38['overlap_analysis']:5.1f} / {W['overlap_analysis']}   "
          f"[{_bar(sc38['overlap_analysis'], W['overlap_analysis'])}]  "
          f"{_pct(sc38['overlap_analysis'], W['overlap_analysis'])}")
    print(f"    Gap Justification       {sc38['gap_justification']:5.1f} / {W['gap_justification']}   "
          f"[{_bar(sc38['gap_justification'],W['gap_justification'])}]  "
          f"{_pct(sc38['gap_justification'],W['gap_justification'])}")
    print()
    print(f"  {'Career Progression':30s} "
          f"{sc38['role_seniority']+sc38['tenure_consistency']+sc38['domain_continuity']:5.1f} / "
          f"{W['role_seniority']+W['tenure_consistency']+W['domain_continuity']}")
    print(f"    Role Seniority          {sc38['role_seniority']:5.1f} / {W['role_seniority']}   "
          f"[{_bar(sc38['role_seniority'],    W['role_seniority'])}]  "
          f"{_pct(sc38['role_seniority'],    W['role_seniority'])}")
    print(f"    Tenure Consistency      {sc38['tenure_consistency']:5.1f} / {W['tenure_consistency']}    "
          f"[{_bar(sc38['tenure_consistency'],W['tenure_consistency'])}]  "
          f"{_pct(sc38['tenure_consistency'],W['tenure_consistency'])}")
    print(f"    Domain Continuity       {sc38['domain_continuity']:5.1f} / {W['domain_continuity']}    "
          f"[{_bar(sc38['domain_continuity'], W['domain_continuity'])}]  "
          f"{_pct(sc38['domain_continuity'], W['domain_continuity'])}")
    print()
    print(f"  {'Data Quality Bonus':30s} {sc38['data_quality']:5.1f} / {W['data_quality']}")
    print(f"{dash}")
    print(f"  {'Module 3.8 Total':30s} {s38['raw']:5.1f} / {MAX_38}")
    print()

    #  Module 3.9 
    if s39.get("applicable"):
        print("   MODULE 3.9  Skill Alignment \n")
        print(f"    Skill-to-Experience     {sc39['skill_experience']:5.1f} / {W['skill_experience']}   "
              f"[{_bar(sc39['skill_experience'],  W['skill_experience'])}]  "
              f"{_pct(sc39['skill_experience'],  W['skill_experience'])}")
        print(f"    Skill-to-Publication    {sc39['skill_publication']:5.1f} / {W['skill_publication']}   "
              f"[{_bar(sc39['skill_publication'], W['skill_publication'])}]  "
              f"{_pct(sc39['skill_publication'], W['skill_publication'])}")
        print(f"    Skill Consistency       {sc39['skill_consistency']:5.1f} / {W['skill_consistency']}   "
              f"[{_bar(sc39['skill_consistency'], W['skill_consistency'])}]  "
              f"{_pct(sc39['skill_consistency'], W['skill_consistency'])}")
        print(f"{dash}")
        print(f"  {'Module 3.9 Total':30s} {s39['raw']:5.1f} / {MAX_39}")
    else:
        print(f"   MODULE 3.9  Skill Alignment  N/A")
        print(f"    {s39.get('reason', '')}")
    print()

    #  Final 
    print(f"{sep}")
    print(f"  FINAL SCORE   {combined['final_score']:6.1f} / 100   {combined['grade']}")
    if combined.get("note"):
        print(f"  Note: {combined['note']}")
    print(f"{sep}\n")

    #  Component Reasons 
    print(f"  COMPONENT REASONS")
    print(f"{dash}")
    for key, reason in s38["reasons"].items():
        print(f"  [{key}]")
        print(f"     {reason}")
    if s39.get("applicable"):
        for key, reason in s39.get("reasons", {}).items():
            print(f"  [{key}]")
            print(f"     {reason}")
    print()

    #  Career trajectory 
    print(f"  CAREER TRAJECTORY")
    print(f"{dash}")
    traj = career["seniority_trajectory"]
    if traj:
        for t in traj:
            bar = "█" * t["seniority_level"] + "░" * (6 - t["seniority_level"])
            print(f"  [{bar}] L{t['seniority_level']}  "
                  f"{t['role'][:35]:35s} @ {t['company'][:25]:25s} ({t['months']}m)")
    print(f"  Trend: {career['seniority_trend'].upper()} | "
          f"Avg tenure: {career['avg_tenure_months']:.0f}m | "
          f"Domain: {career['domain_continuity'].upper()}")
    for note in career.get("notes", []):
        print(f"    {note}")
    print()

    #  Timeline flags 
    if timeline["flags"]:
        print(f"  TIMELINE FLAGS")
        print(f"{dash}")
        for flag in timeline["flags"]:
            print(f"    {flag}")
        print()

    #  Skill evidence breakdown 
    if s39.get("applicable") and skill_analysis and skill_analysis.get("skill_details"):
        print(f"  SKILL EVIDENCE BREAKDOWN")
        print(f"{dash}")
        for d in skill_analysis["skill_details"]:
            icon = {
                "STRONG": "✓", "PARTIAL": "◐", "WEAK": "◑", "UNSUPPORTED": "✗"
            }.get(d["evidence_strength"], "?")
            print(f"  {icon} {d['skill']:<30s}  [{d['evidence_strength']:<11s}]  "
                  f"exp:{d['exp_match_count']}  pub:{d['pub_match_count']}")
            print(f"       {d['reasoning']}")
        print()

    print(f"{sep}\n")


def generate_inquiry_email(
    name: str,
    email: str | None,
    timeline: dict,
    career: dict,
    skill_analysis: dict | None,
) -> str | None:
    """
    Returns a draft email if there are issues needing clarification,
    or None if no inquiry is needed.
    """
    questions = []

    # Gap questions
    for gap in timeline["gaps"]:
        if not gap["justified"] and gap["months"] > 3:
            questions.append(
                f"   We noticed a gap of approximately {gap['months']} months "
                f"({gap['period']}) between your roles at "
                f"'{gap['preceded_by'].split('@')[-1].strip()}' and "
                f"'{gap['followed_by'].split('@')[-1].strip()}'. "
                f"Could you describe what you were doing during this period?"
            )

    # Overlap questions
    for ov in timeline["job_overlaps"]:
        if ov["concern_level"] in ("concerning", "review_needed"):
            questions.append(
                f"   Your CV indicates you held '{ov['job_a']}' and "
                f"'{ov['job_b']}' concurrently for {ov['months']} month(s). "
                f"Could you clarify the nature and hours of each role?"
            )

    # Career notes
    for note in career.get("notes", []):
        if "job-hopping" in note:
            questions.append(
                "   Your average tenure per role is relatively short. "
                "Could you briefly explain the reasons for the transitions?"
            )

    # Skill questions  use LLM-identified UNSUPPORTED skills
    if skill_analysis and skill_analysis.get("applicable"):
        unsupported = [
            d["skill"] for d in skill_analysis["skill_details"]
            if d["evidence_strength"] == "UNSUPPORTED"
        ]
        if unsupported:
            skills_str = ", ".join(f'"{s}"' for s in unsupported)
            questions.append(
                f"   You have listed the following skill(s) for which we could not "
                f"find supporting evidence in your job descriptions or publications: "
                f"{skills_str}. Could you provide context on where and how you "
                f"developed these skills?"
            )

    if not questions:
        return None

    body = f"""Subject: Request for Additional Information  CV Review ({name})

Dear {name},

Thank you for submitting your CV for our review. As part of our structured
evaluation process, we analyse employment history, career progression, and
skill evidence in detail. We have identified a few areas where further
clarification would help us complete a fair and accurate assessment.

QUESTIONS FOR YOUR CLARIFICATION

{chr(10).join(questions)}

Please reply within 5 business days. Your responses will be treated
confidentially and used solely for the purposes of this evaluation.

We appreciate your time and look forward to hearing from you.

Warm regards,
CV Assessment Team
"""
    return body


# ============================================================
# CELL 8  Main Runner
# ============================================================

def run_candidate(candidate_id: int = None, data: dict = None) -> dict:
    """
    Full pipeline: load  analyse  score  report  email.

    Parameters
    ----------
    candidate_id : int, optional   Load from DB when provided.
    data         : dict, optional  Use pre-loaded dict directly.
    """
    #  Step 1: Load 
    if data:
        candidate = data
    elif candidate_id is not None:
        print(f"   Loading candidate {candidate_id} from database...")
        candidate = load_candidate(candidate_id)
        if not candidate:
            print(f"     Candidate {candidate_id} not found.")
            return {}
    else:
        raise ValueError("Provide candidate_id or data=")

    name       = candidate.get("name", "Unknown")
    email      = candidate.get("email")
    experience = candidate.get("experience", [])
    education  = candidate.get("education", [])
    skills     = candidate.get("skills", [])
    pubs       = candidate.get("publications", [])

    print(f"     Experience: {len(experience)} | Education: {len(education)} | "
          f"Skills: {len(skills)} | Publications: {len(pubs)}")

    #  Step 2: Analyse timeline 
    print(f"     Timeline analysis...")
    timeline = analyse_timeline(experience, education)

    #  Step 3: Analyse career 
    print(f"     Career analysis...")
    career = analyse_career(experience)

    #  Step 4: Analyse skills (LLM call happens here) 
    print(f"     Skill alignment analysis...")
    skill_analysis = analyse_skills(skills, experience, pubs)

    #  Step 5: Score 
    print(f"     Computing scores...")
    s38      = score_38(timeline, career, experience, education)
    s39      = score_39(skill_analysis)
    combined = combine_scores(s38, s39)

    #  Step 6: Print report 
    print_experience_report(name, s38, s39, combined, timeline, career, skill_analysis)

    #  Step 7: Email (if needed) 
    email_draft = generate_inquiry_email(name, email, timeline, career, skill_analysis)
    if email_draft:
        print("═" * 60)
        print("  DRAFT INQUIRY EMAIL")
        print("═" * 60)
        print(email_draft)
    else:
        print("   No inquiry email needed  all timeline data is clear.\n")

    return {
        "candidate":      candidate,
        "timeline":       timeline,
        "career":         career,
        "skill_analysis": skill_analysis,
        "score_38":       s38,
        "score_39":       s39,
        "combined":       combined,
        "email_draft":    email_draft,
    }


# ============================================================
# DATABASE SAVE FUNCTIONS (Modules 3.8 & 3.9)
# ============================================================

def save_professional_experience_score(candidate_id: int, result: dict) -> bool:
    """
    Save Module 3.8 (Professional Experience) analysis results to the database.
    """
    # Import here to delay database engine creation until first use
    from db_connect import get_session
    
    session = get_session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            print(f"      Candidate {candidate_id} not found.")
            return False

        timeline  = result.get("timeline", {})
        career    = result.get("career", {})
        score_38  = result.get("score_38", {})

        scores    = score_38.get("scores", {})
        reasons   = score_38.get("reasons", {})
        raw       = score_38.get("raw", 0)

        pe_score = ProfessionalExperienceScore(
            candidate_id=candidate_id,
            gap_detection_score=scores.get("gap_detection", 0),
            overlap_analysis_score=scores.get("overlap_analysis", 0),
            gap_justification_score=scores.get("gap_justification", 0),
            role_seniority_score=scores.get("role_seniority", 0),
            tenure_consistency_score=scores.get("tenure_consistency", 0),
            domain_continuity_score=scores.get("domain_continuity", 0),
            data_quality_bonus=scores.get("data_quality", 0),
            raw_score=raw,
            grade=_grade(raw),
            gaps=json.dumps(timeline.get("gaps", []), default=str),
            job_overlaps=json.dumps(timeline.get("job_overlaps", []), default=str),
            edu_overlaps=json.dumps(timeline.get("edu_overlaps", []), default=str),
            flags=json.dumps(timeline.get("flags", []), default=str),
            seniority_trajectory=json.dumps(career.get("seniority_trajectory", []), default=str),
            seniority_trend=career.get("seniority_trend", "flat"),
            avg_tenure_months=career.get("avg_tenure_months", 0),
            total_experience_months=career.get("total_experience_months", 0),
            domain_continuity=career.get("domain_continuity", "weak"),
            career_notes=json.dumps(career.get("notes", []), default=str),
            reasons=json.dumps(reasons, default=str),
            created_at=datetime.utcnow(),
        )

        session.add(pe_score)
        session.commit()
        print(f"     Module 3.8 saved ({raw}/60)")
        return True

    except Exception as e:
        session.rollback()
        print(f"      Error saving Module 3.8: {e}")
        return False
    finally:
        session.close()


def save_skill_alignment_score(candidate_id: int, result: dict) -> bool:
    """
    Save Module 3.9 (Skill Alignment) analysis results to the database.
    """
    # Import here to delay database engine creation until first use
    from db_connect import get_session
    
    session = get_session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            print(f"      Candidate {candidate_id} not found.")
            return False

        skill_analysis = result.get("skill_analysis", {})
        score_39       = result.get("score_39", {})

        applicable = score_39.get("applicable", False)
        reason     = score_39.get("reason", "")
        scores     = score_39.get("scores", {})
        reasons    = score_39.get("reasons", {})
        raw        = score_39.get("raw", 0)

        skill_details = skill_analysis.get("skill_details", [])
        total_skills  = len(skill_details)
        strong_count  = skill_analysis.get("strong_count", 0)
        partial_count = skill_analysis.get("partial_count", 0)
        weak_count    = skill_analysis.get("weak_count", 0)
        unsupported_count = skill_analysis.get("unsupported_count", 0)

        skill_score = SkillAlignmentScore(
            candidate_id=candidate_id,
            applicable=applicable,
            applicability_reason=reason,
            skill_experience_score=scores.get("skill_experience", 0),
            skill_publication_score=scores.get("skill_publication", 0),
            skill_consistency_score=scores.get("skill_consistency", 0),
            raw_score=raw,
            grade=_grade(raw),
            skill_details=json.dumps(skill_details, default=str),
            total_skills_evaluated=total_skills,
            strong_count=strong_count,
            partial_count=partial_count,
            weak_count=weak_count,
            unsupported_count=unsupported_count,
            reasons=json.dumps(reasons, default=str),
            created_at=datetime.utcnow(),
        )

        session.add(skill_score)
        session.commit()
        print(f"     Module 3.9 saved ({'N/A' if not applicable else f'{raw}/40'})")
        return True

    except Exception as e:
        session.rollback()
        print(f"      Error saving Module 3.9: {e}")
        return False
    finally:
        session.close()


def save_professional_and_skill_scores(candidate_id: int, result: dict) -> bool:
    """
    Convenience function to save both Module 3.8 and 3.9 scores.
    """
    success_38 = save_professional_experience_score(candidate_id, result)
    success_39 = save_skill_alignment_score(candidate_id, result)
    return success_38 and success_39