# summarizers.py
"""
Comprehensive CV Evaluation Report Generator
Generates detailed scores and analysis across all modules.

State key contract (must match what each analysis node writes):
  result["education_analysis"]         from education_analysis node
  result["research_analysis"]          from research_analysis node
  result["experience_skill_analysis"]  from experiance_skill_analysis node
  result["tvs_ccs_analysis"]           from tvs_ccs_analysis node
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from .db_models import Candidate, CVSummary

# ============================================================================
# SCORING WEIGHTS
# ============================================================================
MODULE_WEIGHTS = {
    "education":  0.25,   # 25%
    "research":   0.35,   # 35%
    "experience": 0.20,   # 20%
    "tvs_ccs":    0.10,   # 10%
}


# ============================================================================
# MODULE 3.1: EDUCATION REPORT
# ============================================================================

def generate_education_report(edu_analysis: Dict) -> Dict[str, Any]:
    """
    Build education report from what education_analysis node stored in state:
      {
        "score":      final_total,    used as report score
        "grade":      label,          EXCELLENT / GOOD / AVERAGE / WEAK
        "base_total": base_total,
        "bonus":      bonus,
        "components": { degree_level, overall_gpa, institution_quality,
                        consistency, continuity, data_completeness }
      }
    """
    if not edu_analysis or "error" in edu_analysis:
        return {
            "module": "3.1 Educational Profile Analysis",
            "score": 0, "max_score": 100,
            "grade": "INCOMPLETE",
            "status": " No data available",
            "components": [],
            "interpretation": "Education analysis could not be performed.",
            "strengths": [],
            "weaknesses": ["Missing education data"],
            "recommendations": ["Submit education records for evaluation"],
        }

    components = edu_analysis.get("components", {})

    degree_level        = components.get("degree_level", {})
    overall_gpa         = components.get("overall_gpa", {})
    institution_quality = components.get("institution_quality", {})
    consistency         = components.get("consistency", {})
    continuity          = components.get("continuity", {})
    data_completeness   = components.get("data_completeness", {})

    def pct(score, max_val):
        return (score / max_val * 100) if max_val else 0

    component_details = [
        {
            "name": "Degree Level",
            "score": degree_level.get("score", 0),
            "max": degree_level.get("max", 25),
            "percentage": pct(degree_level.get("score", 0), degree_level.get("max", 25)),
            "reason": degree_level.get("reason", ""),
            "status": "" if degree_level.get("score", 0) >= 20 else "" if degree_level.get("score", 0) >= 10 else "",
        },
        {
            "name": "Overall GPA/Performance",
            "score": overall_gpa.get("score", 0),
            "max": overall_gpa.get("max", 30),
            "percentage": pct(overall_gpa.get("score", 0), overall_gpa.get("max", 30)),
            "weighted_avg": overall_gpa.get("weighted_avg", 0),
            "reason": overall_gpa.get("reason", ""),
            "status": "" if overall_gpa.get("score", 0) >= 24 else "" if overall_gpa.get("score", 0) >= 12 else "",
        },
        {
            "name": "Institution Quality (QS/THE Rankings)",
            "score": institution_quality.get("score", 0),
            "max": institution_quality.get("max", 20),
            "percentage": pct(institution_quality.get("score", 0), institution_quality.get("max", 20)),
            "tier": institution_quality.get("tier", "Unknown"),
            "institution": institution_quality.get("institution", "Unknown"),
            "reason": institution_quality.get("reason", ""),
            "status": "" if institution_quality.get("score", 0) >= 15 else "" if institution_quality.get("score", 0) >= 10 else "",
        },
        {
            "name": "Academic Consistency",
            "score": consistency.get("score", 0),
            "max": consistency.get("max", 10),
            "percentage": pct(consistency.get("score", 0), consistency.get("max", 10)),
            "gpa_trend": consistency.get("gpa_trend_score", 0),
            "field_alignment": consistency.get("field_alignment_score", 0),
            "reason": consistency.get("reason", ""),
            "status": "" if consistency.get("score", 0) >= 8 else "" if consistency.get("score", 0) >= 5 else "",
        },
        {
            "name": "Educational Continuity (Gap Analysis)",
            "score": continuity.get("score", 0),
            "max": continuity.get("max", 10),
            "percentage": pct(continuity.get("score", 0), continuity.get("max", 10)),
            "gaps": continuity.get("gaps_found", []),
            "reason": continuity.get("reason", ""),
            "status": "" if continuity.get("score", 0) >= 8 else "" if continuity.get("score", 0) >= 5 else "",
        },
        {
            "name": "Data Completeness (BONUS)",
            "score": data_completeness.get("score", 0),
            "max": data_completeness.get("max", 5),
            "percentage": pct(data_completeness.get("score", 0), data_completeness.get("max", 5)),
            "reason": data_completeness.get("reason", ""),
            "status": "" if data_completeness.get("score", 0) >= 4 else "",
        },
    ]

    #  score / grade come directly from what education_analysis stored 
    total_score = edu_analysis.get("score", 0)   # = final_total
    grade       = edu_analysis.get("grade", "UNKNOWN")  # = label

    interpretation_map = {
        "EXCELLENT": "Outstanding academic profile with strong progression, high performance, quality institutions, and excellent consistency.",
        "GOOD":      "Solid academic foundation with good progression and institutional quality. Minor gaps may exist but are explained by work experience.",
        "AVERAGE":   "Acceptable academic profile but with some inconsistencies, lower performance metrics, or significant unexplained gaps.",
        "WEAK":      "Weak academic profile with poor performance, unexplained gaps, or low institutional quality.",
    }
    interpretation = interpretation_map.get(grade, "Academic profile requires review.")

    strengths, weaknesses, recommendations = [], [], []

    if degree_level.get("score", 0) >= 25:
        strengths.append("PhD qualification (highest tier degree)")
    elif degree_level.get("score", 0) >= 20:
        strengths.append("Postgraduate qualification")

    if overall_gpa.get("score", 0) >= 24:
        strengths.append(f"Strong GPA performance (Weighted avg: {overall_gpa.get('weighted_avg', 0):.1f}%)")

    if institution_quality.get("score", 0) >= 15:
        strengths.append(f"Quality institution ({institution_quality.get('institution', '')})")

    if consistency.get("score", 0) >= 8:
        strengths.append("Excellent field alignment and GPA trend")

    if continuity.get("gaps_found"):
        weaknesses.append(f"Education gaps detected: {', '.join(continuity.get('gaps_found', []))}")
        recommendations.append("Clarify unexplained education gaps with documentation of work experience")

    if data_completeness.get("score", 0) < 5:
        weaknesses.append("Incomplete profile information (missing email/phone)")
        recommendations.append("Update CV with complete contact information (email, phone)")

    if institution_quality.get("tier", 3) >= 3:
        weaknesses.append(f"Institution ranking: Tier {institution_quality.get('tier', 'Unknown')} (not top-tier)")

    if overall_gpa.get("score", 0) < 12:
        recommendations.append("Consider additional certifications to strengthen academic profile")

    return {
        "module": "3.1 Educational Profile Analysis",
        "score": total_score,
        "max_score": 100,
        "grade": grade,
        "percentage": pct(total_score, 100),
        "status": "" if grade in ("EXCELLENT", "GOOD") else "" if grade == "AVERAGE" else "",
        "components": component_details,
        "base_score": edu_analysis.get("base_total", 0),
        "bonus": edu_analysis.get("bonus", 0),
        "interpretation": interpretation,
        "strengths": strengths or ["Education records available"],
        "weaknesses": weaknesses or ["No major issues"],
        "recommendations": recommendations or ["Continue current academic trajectory"],
    }


# ============================================================================
# MODULE 3.2-3.7: RESEARCH REPORT
# ============================================================================

def generate_research_report(research_analysis: Dict) -> Dict[str, Any]:
    """
    Build research report from what research_analysis node stored in state:
      {
        "score":      final_score,
        "grade":      label,          STRONG / MODERATE / WEAK
        "components": { authorship_strength, research_collaboration,
                        publication_quality, conference_maturity,
                        supervision_record, patents_books },
        "counts":     { total_publications, total_journal_papers, ... },
        "warnings":   [...],
        "recommendations": [...],
      }
    """
    if not research_analysis or "error" in research_analysis:
        return {
            "module": "3.2-3.7 Research Profile Analysis",
            "score": 0, "max_score": 100,
            "grade": "INCOMPLETE",
            "status": " No research data",
            "components": [],
            "interpretation": "Research profile could not be evaluated.",
            "publication_counts": {},
            "strengths": [],
            "weaknesses": ["No publications found"],
            "recommendations": ["Submit research publication records"],
        }

    components = research_analysis.get("components", {})
    counts     = research_analysis.get("counts", {})
    warnings   = research_analysis.get("warnings", [])

    authorship    = components.get("authorship_strength", 0)
    collaboration = components.get("research_collaboration", 0)
    quality       = components.get("publication_quality", 0)
    conference    = components.get("conference_maturity", 0)
    supervision   = components.get("supervision_record", 0)
    patents_books = components.get("patents_books", 0)

    component_details = [
        {"name": "Authorship & First-Author Strength",       "score": authorship,    "max": 10,  "status": "" if authorship >= 8    else "" if authorship >= 5    else ""},
        {"name": "Research Collaboration & Co-authorship",   "score": collaboration, "max": 15,  "status": "" if collaboration >= 12 else "" if collaboration >= 8 else ""},
        {"name": "Publication Quality (Indexing/Quartiles)", "score": quality,       "max": 20,  "status": "" if quality >= 16       else "" if quality >= 10      else ""},
        {"name": "Conference Maturity & Ranking",            "score": conference,    "max": 10,  "status": "" if conference >= 8     else "" if conference >= 5    else ""},
        {"name": "Student Supervision Record",               "score": supervision,   "max": 20,  "status": "" if supervision >= 16   else "" if supervision >= 8   else ""},
        {"name": "Patents & Books Authored",                 "score": patents_books, "max": 15,  "status": "" if patents_books >= 12 else "" if patents_books >= 6  else ""},
    ]

    total_score = research_analysis.get("score", 0)
    grade       = research_analysis.get("grade", "UNKNOWN")

    interpretation_map = {
        "STRONG":   "Excellent research profile with high-quality publications, strong collaboration, good indexing, and active supervision.",
        "MODERATE": "Decent research output with some quality publications and collaboration, but room for improvement in indexing or supervision.",
        "WEAK":     "Limited research output or publications in lower-tier venues. Concerns about verification, indexing, or collaboration.",
    }
    interpretation = interpretation_map.get(grade, "Insufficient research data for evaluation.")

    total_pubs = counts.get("total_publications", 0)
    strengths, weaknesses = [], []

    if total_pubs >= 10:
        strengths.append(f"Strong publication count ({total_pubs} publications)")
    elif total_pubs >= 5:
        strengths.append(f"Decent publication record ({total_pubs} publications)")
    if collaboration >= 12:
        strengths.append("Excellent collaboration network with international reach")
    if supervision >= 16:
        strengths.append("Strong supervision record with documented PhD/MS students")
    if patents_books >= 12:
        strengths.append("Patents or book chapters demonstrating applied research")

    if total_pubs < 5:
        weaknesses.append("Limited number of publications")
    if quality < 5:
        weaknesses.append("Publications not verified in major indexing databases (Scopus/WoS)")
    if supervision == 0:
        weaknesses.append("No documented student supervision record")
    if warnings:
        weaknesses.extend(f" {w}" for w in warnings[:3])

    recommendations = list(research_analysis.get("recommendations", []))
    if total_pubs < 5:
        recommendations.append("Increase publication output in indexed journals")
    if quality < 10:
        recommendations.append("Target Q1/Q2 Scopus or WoS-indexed journals")
    if supervision == 0:
        recommendations.append("Document and record MS/PhD student supervision")

    return {
        "module": "3.2-3.7 Research Profile Analysis",
        "score": total_score,
        "max_score": 100,
        "grade": grade,
        "percentage": (total_score / 100 * 100),
        "status": "" if grade in ("STRONG", "MODERATE") else "",
        "components": component_details,
        "publication_counts": {
            "Total Publications": total_pubs,
            "Journal Papers":     counts.get("total_journal_papers", 0),
            "Conference Papers":  counts.get("total_conference_papers", 0),
            "Patents":            counts.get("total_patents", 0),
            "Books":              counts.get("total_books", 0),
        },
        "interpretation": interpretation,
        "strengths": strengths or ["Research profile available"],
        "weaknesses": weaknesses or ["No major issues"],
        "recommendations": recommendations[:5] or ["Continue publishing in quality venues"],
    }


# ============================================================================
# MODULE 3.8-3.9: EXPERIENCE & SKILLS REPORT
# ============================================================================

def generate_experience_skills_report(exp_analysis: Dict) -> Dict[str, Any]:
    """
    Build experience/skills report from what experiance_skill_analysis node stored:
      {
        "final_score": ...,
        "grade":       ...,    EXCELLENT / SATISFACTORY / WEAK
        "module_38":   { "score": ..., "max": 60, "components": {...} },
        "module_39":   { "applicable": bool, "score": ... },
        "timeline_flags": [...],
      }
    """
    if not exp_analysis or "error" in exp_analysis:
        return {
            "module": "3.8-3.9 Experience & Skills Analysis",
            "score": 0, "max_score": 100,
            "grade": "INCOMPLETE",
            "status": " No experience data",
            "components": [],
            "interpretation": "Experience analysis could not be performed.",
            "strengths": [],
            "weaknesses": ["No employment records"],
            "recommendations": ["Submit employment history"],
        }

    final_score    = exp_analysis.get("final_score", 0)
    grade          = exp_analysis.get("grade", "UNKNOWN")
    timeline_flags = exp_analysis.get("timeline_flags", [])

    module_38      = exp_analysis.get("module_38", {})
    m38_components = module_38.get("components", {})
    m38_score      = module_38.get("score", 0)
    m38_max        = module_38.get("max", 60)

    sub_components = [
        {"name": "Data Quality",               "score": m38_components.get("data_quality", 0),       "max": 10, "status": "" if m38_components.get("data_quality", 0) >= 8       else ""},
        {"name": "Gap Detection",              "score": m38_components.get("gap_detection", 0),      "max": 10, "status": "" if m38_components.get("gap_detection", 0) >= 8      else ""},
        {"name": "Gap Justification",          "score": m38_components.get("gap_justification", 0),  "max": 10, "status": "" if m38_components.get("gap_justification", 0) >= 8  else ""},
        {"name": "Role Seniority Progression", "score": m38_components.get("role_seniority", 0),     "max": 10, "status": "" if m38_components.get("role_seniority", 0) >= 8     else ""},
        {"name": "Tenure Consistency",         "score": m38_components.get("tenure_consistency", 0), "max": 10, "status": "" if m38_components.get("tenure_consistency", 0) >= 8 else ""},
        {"name": "Domain Continuity",          "score": m38_components.get("domain_continuity", 0),  "max": 10, "status": "" if m38_components.get("domain_continuity", 0) >= 7  else ""},
        {"name": "Overlap Analysis",           "score": m38_components.get("overlap_analysis", 0),   "max": 10, "status": "" if m38_components.get("overlap_analysis", 0) >= 8   else ""},
    ]

    component_details = [
        {
            "name": "Employment Timeline Consistency (Module 3.8)",
            "score": m38_score,
            "max": m38_max,
            "percentage": (m38_score / m38_max * 100) if m38_max else 0,
            "sub_components": sub_components,
            "reason": "Employment history timeline verification",
            "status": "" if m38_score >= 45 else "" if m38_score >= 30 else "",
        }
    ]

    module_39     = exp_analysis.get("module_39", {})
    m39_applicable = module_39.get("applicable", False)
    m39_score      = module_39.get("score", 0)

    if m39_applicable and m39_score:
        component_details.append({
            "name": "Skill Alignment with Experience & Publications (Module 3.9)",
            "score": m39_score,
            "max": 40,
            "percentage": (m39_score / 40 * 100),
            "reason": "Skills validation against job roles and research output",
            "status": "" if m39_score >= 32 else "" if m39_score >= 20 else "",
        })

    interpretation_map = {
        "EXCELLENT":    "Strong career progression with clear advancement, consistent domain expertise, and well-documented experience.",
        "SATISFACTORY": "Acceptable career trajectory with some employment activity, but with inconsistencies or gaps that need clarification.",
        "WEAK":         "Limited or unclear employment history with significant gaps, overlaps, or lack of documented experience.",
    }
    interpretation = interpretation_map.get(grade, "Experience profile requires review.")

    strengths, weaknesses, recommendations = [], [], []

    if m38_components.get("role_seniority", 0) >= 8:
        strengths.append("Clear career progression to senior roles")
    if m38_components.get("domain_continuity", 0) >= 7:
        strengths.append("Consistent domain expertise (same field across roles)")
    if m38_components.get("tenure_consistency", 0) >= 8:
        strengths.append("Stable role tenure (not job-hopping)")

    if timeline_flags:
        weaknesses.extend(f" {flag}" for flag in timeline_flags)
        recommendations.append("Provide documentation/explanation for employment gaps and role overlaps")
    if m38_components.get("gap_justification", 0) < 5:
        weaknesses.append("Employment gaps lack adequate justification")
    if m38_components.get("overlap_analysis", 0) < 5:
        weaknesses.append("Unexplained job overlaps or concurrent roles")
    if not m39_applicable:
        recommendations.append("Submit skill inventory for validation against job roles")

    recommendations.append("Ensure chronological consistency in employment records")

    return {
        "module": "3.8-3.9 Experience & Skills Analysis",
        "score": final_score,
        "max_score": 100,
        "grade": grade,
        "percentage": final_score,
        "status": "" if grade in ("EXCELLENT", "SATISFACTORY") else "" if grade == "WEAK" else "",
        "components": component_details,
        "timeline_flags": timeline_flags,
        "interpretation": interpretation,
        "strengths": strengths or ["Employment records available"],
        "weaknesses": weaknesses or ["No major issues"],
        "recommendations": recommendations or ["Review employment details"],
    }


# ============================================================================
# MODULE 3.6-3.7: TOPIC VARIABILITY & COLLABORATION REPORT
# ============================================================================

from typing import Dict, Any


def _safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def _safe_int(x, default=0):
    try:
        if x is None:
            return default
        return int(x)
    except (TypeError, ValueError):
        return default


def generate_tvs_ccs_report(tvs_analysis: Dict) -> Dict[str, Any]:
    """
    Robust TVS/CCS report generator (safe against NoneType crashes)
    """

    if not tvs_analysis:
        return {
            "module": "3.6-3.7 Research Focus & Collaboration",
            "score": 0,
            "max_score": 100,
            "grade": "INCOMPLETE",
            "status": " No collaboration data",
            "components": [],
            "interpretation": "Could not analyze research focus and collaboration.",
            "strengths": [],
            "weaknesses": ["Insufficient data"],
            "recommendations": ["Submit publication records"],
        }

    module_36 = tvs_analysis.get("module_36") or {}
    module_37 = tvs_analysis.get("module_37") or {}

    # =========================
    # SAFE EXTRACTION (CRITICAL FIX)
    # =========================
    m36_applicable = bool(module_36.get("applicable", False))
    m36_diversity = _safe_float(module_36.get("diversity_score"), 0.0)
    m36_focus_type = module_36.get("focus_type") or "unknown"
    m36_themes = _safe_int(module_36.get("themes_count"), 0)
    m36_trend = module_36.get("topic_trend") or "stable"
    m36_interpretation = module_36.get("overall_interpretation") or ""

    m37_applicable = bool(module_37.get("applicable", False))
    m37_network_diversity = _safe_float(module_37.get("network_diversity_score"), 0.0)
    m37_collab_type = module_37.get("collaboration_type") or "unknown"
    m37_unique_coauthors = _safe_int(module_37.get("unique_coauthors"), 0)
    m37_recurring = _safe_int(module_37.get("recurring_collaborators"), 0)
    m37_international = bool(module_37.get("international_flag", False))
    m37_interpretation = module_37.get("interpretation") or ""

    component_details = []

    # =========================
    # MODULE 3.6
    # =========================
    if m36_applicable:
        component_details.append({
            "name": "Research Topic Variability & Specialization (Module 3.6)",
            "score": m36_diversity * 10,
            "max": 100,
            "percentage": m36_diversity * 10,
            "focus_type": m36_focus_type,
            "themes": m36_themes,
            "trend": m36_trend,
            "interpretation": m36_interpretation,
            "status": "" if m36_diversity >= 7 else "" if m36_diversity >= 5 else "",
        })

    # =========================
    # MODULE 3.7
    # =========================
    if m37_applicable:
        component_details.append({
            "name": "Research Collaboration & Network Analysis (Module 3.7)",
            "score": m37_network_diversity * 10,
            "max": 100,
            "percentage": m37_network_diversity * 10,
            "collaboration_type": m37_collab_type,
            "unique_coauthors": m37_unique_coauthors,
            "recurring_collaborators": m37_recurring,
            "international": " Yes" if m37_international else " No",
            "interpretation": m37_interpretation,
            "status": "" if m37_network_diversity >= 7 else "" if m37_network_diversity >= 5 else "",
        })

    # =========================
    # SCORE CALCULATION (SAFE)
    # =========================
    scores = []

    if m36_applicable:
        scores.append(m36_diversity * 10)

    if m37_applicable:
        scores.append(m37_network_diversity * 10)

    avg_score = sum(scores) / len(scores) if scores else 0.0

    # =========================
    # INTERPRETATION
    # =========================
    if m36_applicable:
        if m36_focus_type == "specialist":
            interpretation = (
                f"Highly specialized research focus with {m36_themes} theme(s). "
                f"Strong depth in a narrow domain."
            )
        elif m36_focus_type == "broad_specialist":
            interpretation = (
                f"Specialized but expanding scope with {m36_themes} themes. "
                f"{m36_interpretation}"
            )
        else:
            interpretation = (
                f"Interdisciplinary research across {m36_themes} themes. "
                f"{m36_interpretation}"
            )
    else:
        interpretation = "Research focus and collaboration patterns unavailable."

    # =========================
    # STRENGTHS / WEAKNESSES
    # =========================
    strengths = []
    weaknesses = []
    recommendations = []

    if m37_network_diversity >= 7:
        strengths.append(f"Strong collaboration network ({m37_unique_coauthors} co-authors)")

    if m37_recurring >= 2:
        strengths.append(f"Stable collaborations ({m37_recurring} recurring partners)")

    if m37_international:
        strengths.append("International research collaboration")

    if m36_diversity >= 7:
        strengths.append("High topic diversity within domain")

    if m36_diversity < 4:
        weaknesses.append("Very narrow research focus")
        recommendations.append("Expand into adjacent research domains")

    if m37_network_diversity < 4:
        weaknesses.append("Weak collaboration network")
        recommendations.append("Increase collaboration with external researchers")

    if not m37_international:
        weaknesses.append("No international collaboration detected")

    if m36_trend == "declining":
        weaknesses.append("Declining research activity trend")

    if m37_recurring < 2:
        recommendations.append("Build stronger long-term collaborations")

    # =========================
    # GRADE
    # =========================
    grade = "GOOD" if avg_score >= 70 else "FAIR" if avg_score >= 50 else "WEAK"

    return {
        "module": "3.6-3.7 Research Focus & Collaboration Analysis",
        "score": avg_score,
        "max_score": 100,
        "grade": grade,
        "percentage": avg_score,
        "status": "" if avg_score >= 70 else "" if avg_score >= 50 else "",
        "components": component_details,
        "interpretation": interpretation,
        "strengths": strengths or ["No strong signals detected"],
        "weaknesses": weaknesses or ["No major weaknesses detected"],
        "recommendations": recommendations or ["Maintain current research trajectory"],
    }


# ============================================================================
# OVERALL SUMMARY GENERATOR
# ============================================================================

def generate_overall_summary(candidate_name: str, candidate_id: str, all_reports: Dict) -> Dict[str, Any]:
    """Combine all module reports into a weighted overall summary."""

    education_score  = all_reports.get("education",  {}).get("score", 0)
    research_score   = all_reports.get("research",   {}).get("score", 0)
    experience_score = all_reports.get("experience", {}).get("score", 0)
    tvs_score        = all_reports.get("tvs_ccs",    {}).get("score", 0)

    overall_weighted = (
        education_score  * MODULE_WEIGHTS["education"]  +
        research_score   * MODULE_WEIGHTS["research"]   +
        experience_score * MODULE_WEIGHTS["experience"] +
        tvs_score        * MODULE_WEIGHTS["tvs_ccs"]
    )

    if overall_weighted >= 80:
        overall_grade, overall_status = "EXCELLENT",    ""
    elif overall_weighted >= 65:
        overall_grade, overall_status = "GOOD",         ""
    elif overall_weighted >= 50:
        overall_grade, overall_status = "SATISFACTORY", ""
    else:
        overall_grade, overall_status = "WEAK",         ""

    module_summary = [
        {
            "name":   "3.1 Educational Profile",
            "score":  education_score,
            "max":    100,
            "grade":  all_reports.get("education",  {}).get("grade", "N/A"),
            "weight": f"{MODULE_WEIGHTS['education']*100:.0f}%",
        },
        {
            "name":   "3.2-3.7 Research Profile",
            "score":  research_score,
            "max":    100,
            "grade":  all_reports.get("research",   {}).get("grade", "N/A"),
            "weight": f"{MODULE_WEIGHTS['research']*100:.0f}%",
        },
        {
            "name":   "3.8-3.9 Experience & Skills",
            "score":  experience_score,
            "max":    100,
            "grade":  all_reports.get("experience", {}).get("grade", "N/A"),
            "weight": f"{MODULE_WEIGHTS['experience']*100:.0f}%",
        },
        {
            "name":   "3.6-3.7 Research Focus & Collaboration",
            "score":  tvs_score,
            "max":    100,
            "grade":  all_reports.get("tvs_ccs",    {}).get("grade", "N/A"),
            "weight": f"{MODULE_WEIGHTS['tvs_ccs']*100:.0f}%",
        },
    ]

    all_strengths, all_weaknesses, all_recommendations = [], [], []
    for report in all_reports.values():
        all_strengths.extend(report.get("strengths", [])[:2])
        all_weaknesses.extend(report.get("weaknesses", [])[:2])
        all_recommendations.extend(report.get("recommendations", [])[:1])

    return {
        "candidate": {
            "name": candidate_name,
            "id":   candidate_id,
            "evaluation_date": datetime.now().isoformat(),
        },
        "overall_score":      round(overall_weighted, 2),
        "overall_max":        100,
        "overall_grade":      overall_grade,
        "overall_status":     overall_status,
        "overall_percentage": round(overall_weighted, 1),
        "module_summary":     module_summary,
        "detailed_breakdown": {
            "education":  all_reports.get("education",  {}),
            "research":   all_reports.get("research",   {}),
            "experience": all_reports.get("experience", {}),
            "tvs_ccs":    all_reports.get("tvs_ccs",    {}),
        },
        "top_strengths":       list(dict.fromkeys(all_strengths))[:5],
        "top_weaknesses":      list(dict.fromkeys(all_weaknesses))[:5],
        "recommendations":     all_recommendations[:5],
        "summary_interpretation": _get_overall_interpretation(overall_weighted),
    }


def _get_overall_interpretation(score: float) -> str:
    if score >= 85:
        return ("Exceptional candidate profile with outstanding qualifications across education, research, "
                "and professional experience. Recommended for advanced academic or research positions.")
    elif score >= 75:
        return ("Strong candidate with solid academic background, reasonable research output, and clear career "
                "progression. Well-suited for academic or research roles with support for development areas.")
    elif score >= 60:
        return ("Satisfactory profile with acceptable qualifications but notable gaps in research output or career "
                "continuity. May benefit from addressing specific deficiencies before senior role consideration.")
    elif score >= 45:
        return ("Weak profile with significant gaps or inconsistencies in education, research, or experience. "
                "Requires substantial improvement and clarification of concerns.")
    else:
        return ("Concerning profile with major deficiencies. Recommend requesting additional documentation or "
                "substantial improvements before further evaluation.")


# ============================================================================
# DATABASE SAVE / LOAD
# ============================================================================

def save_summary_to_database(candidate_id: int, summary: Dict) -> bool:
    """Save overall CV summary to cv_summaries table."""
    # Import here to delay database engine creation until first use
    from .db_connect import get_session
    
    session = get_session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            print(f" Candidate with ID {candidate_id} not found")
            return False

        # Delete existing record (unique constraint on candidate_id)
        session.query(CVSummary).filter_by(candidate_id=candidate_id).delete()
        session.flush()

        module_summary = summary.get("module_summary", [])

        def _score(idx):
            return float(module_summary[idx].get("score", 0)) if len(module_summary) > idx else 0.0

        def _grade(idx):
            return module_summary[idx].get("grade", "N/A") if len(module_summary) > idx else "N/A"

        cv_summary = CVSummary(
            candidate_id   = candidate_id,
            overall_score  = float(summary.get("overall_score", 0)),
            overall_grade  = summary.get("overall_grade", "N/A"),
            overall_status = summary.get("overall_status", "N/A"),
            education_score  = _score(0),
            education_grade  = _grade(0),
            research_score   = _score(1),
            research_grade   = _grade(1),
            experience_score = _score(2),
            experience_grade = _grade(2),
            tvs_score        = _score(3),
            tvs_grade        = _grade(3),
            summary_data   = json.dumps(summary),
        )

        session.add(cv_summary)
        session.commit()
        print(f" Saved CV summary for {candidate.name}  Score: {summary.get('overall_score', 0):.1f}/100 [{summary.get('overall_grade')}]")
        return True

    except Exception as e:
        session.rollback()
        print(f" Error saving CV summary: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


# ============================================================================
# PRETTY PRINT
# ============================================================================

def pretty_print_overall_summary(summary: Dict) -> str:
    output = []
    output.append("\n\n")
    output.append("" + "" * 88 + "")
    output.append("" + " " * 20 + " CV COMPREHENSIVE EVALUATION REPORT " + " " * 26 + "")
    output.append("" + "" * 88 + "")

    output.append(f"\n CANDIDATE INFORMATION")
    output.append("" * 90)
    output.append(f"  Name:            {summary['candidate'].get('name', 'Unknown')}")
    output.append(f"  Candidate ID:    {summary['candidate'].get('id', 'N/A')}")
    output.append(f"  Evaluation Date: {summary['candidate'].get('evaluation_date', 'N/A')[:10]}")

    output.append(f"\n OVERALL EVALUATION SCORE")
    output.append("" * 90)
    output.append(f"  Total Score:   {summary.get('overall_score', 0):.1f} / {summary.get('overall_max', 100)}")
    output.append(f"  Percentage:    {summary.get('overall_percentage', 0):.1f}%")
    output.append(f"  Grade:         {summary.get('overall_status', '')}  {summary.get('overall_grade', 'N/A')}")

    output.append(f"\n MODULE BREAKDOWN (Weighted Scoring)")
    output.append("" * 90)
    output.append(f"  {'Module':<42} {'Score':<14} {'Grade':<16} {'Weight'}")
    output.append(f"  {'-'*42} {'-'*14} {'-'*16} {'-'*8}")
    for m in summary.get("module_summary", []):
        output.append(f"  {m['name']:<42} {m['score']:.1f}/{m['max']:<10} {m['grade']:<16} {m['weight']}")

    output.append(f"\n OVERALL INTERPRETATION")
    output.append("" * 90)
    output.append(f"  {summary.get('summary_interpretation', '')}\n")

    output.append(f" TOP STRENGTHS")
    output.append("" * 90)
    for s in summary.get("top_strengths", []):
        output.append(f"    {s}")

    output.append(f"\n  TOP CHALLENGES/WEAKNESSES")
    output.append("" * 90)
    for w in summary.get("top_weaknesses", []):
        output.append(f"    {w}")

    output.append(f"\n KEY RECOMMENDATIONS")
    output.append("" * 90)
    for i, r in enumerate(summary.get("recommendations", []), 1):
        output.append(f"  {i}. {r}")

    output.append(f"\n{'' * 90}\n")
    return "\n".join(output)
