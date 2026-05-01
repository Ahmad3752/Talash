# edu_scores.py
from datetime import datetime
from db_models import Candidate, Education
from qs_ranker import InstitutionQualityScorer
from llm_client import litellm_chat

CURRENT_YEAR = datetime.now().year

def my_llm(system_prompt: str, user_prompt: str) -> str:
    response = litellm_chat(user_prompt, system_prompt)
    return response.content

scorer = InstitutionQualityScorer(llm_caller=my_llm)
def score_degree_level(education: list) -> dict:
    """
    Finds the highest degree_level the candidate holds.
    doctorate=25, postgrad=20, undergrad=15, school=0
    """
    level_points = {
        "doctorate": 25,
        "postgrad":  20,
        "undergrad": 15,
        "school":     0,
    }

    best_score = 0
    best_degree = "None"
    best_institution = "Unknown"

    for e in education:
        lvl = (e.get("degree_level") or "").lower().strip()
        pts = level_points.get(lvl, 0)
        if pts > best_score:
            best_score = pts
            best_degree = e.get("degree") or lvl
            best_institution = e.get("institution") or "Unknown"

    reason = f"{best_degree} from {best_institution}" if best_score > 0 else "No recognized degree found"

    return {
        "score": best_score,
        "max": 25,
        "reason": reason
    }



def score_overall_gpa(education: list) -> dict:
    """
    Weighted average of normalized_percentage across undergrad/postgrad/doctorate.
    Weights: doctorate=3, postgrad=2, undergrad=1
    """
    weight_map = {"doctorate": 3, "postgrad": 2, "undergrad": 1}

    total_weight = 0
    weighted_sum = 0.0
    details = []

    for e in education:
        lvl = (e.get("degree_level") or "").lower().strip()
        if lvl not in weight_map:
            continue  # skip school-level

        pct = e.get("normalized_percentage")
        if pct is None:
            continue

        w = weight_map[lvl]
        weighted_sum += pct * w
        total_weight += w
        details.append(f"{e.get('degree','?')}={pct:.1f}% (w={w})")

    if total_weight == 0:
        return {"score": 0, "max": 30, "reason": "No GPA/percentage data available", "weighted_avg": 0.0}

    weighted_avg = weighted_sum / total_weight

    # Map to score
    if   weighted_avg >= 90: pts = 30
    elif weighted_avg >= 85: pts = 27
    elif weighted_avg >= 80: pts = 24
    elif weighted_avg >= 75: pts = 20
    elif weighted_avg >= 70: pts = 16
    elif weighted_avg >= 65: pts = 12
    elif weighted_avg >= 60: pts = 8
    else:                    pts = 4

    reason = f"Weighted avg: {weighted_avg:.1f}% | {' | '.join(details)}"

    return {
        "score": pts,
        "max": 30,
        "reason": reason,
        "weighted_avg": round(weighted_avg, 2)
    }

def score_institution_quality(education: list) -> dict:
    """
    Evaluates the highest-level institution using your qs_ranker scorer.
    Falls back to next degree if top one fails.
    """
    # Priority: doctorate first, then postgrad, then undergrad
    priority = ["doctorate", "postgrad", "undergrad"]

    sorted_edu = sorted(
        [e for e in education if e.get("degree_level") in priority],
        key=lambda e: priority.index(e.get("degree_level", "undergrad"))
    )

    if not sorted_edu:
        return {
            "score": 0, "max": 20,
            "reason": "No higher education institution found",
            "tier": 3, "method": "none", "institution": "Unknown"
        }

    target = sorted_edu[0]
    institution_name = target.get("institution") or "Unknown"

    try:
        result = scorer.score_full(institution_name)
        score = min(result.score, 20)   # cap at 20
        tier = result.tier
        method = result.method
        reason = f"{result.reason} | Institution: {institution_name}"
    except Exception as ex:
        # Hard fallback if scorer itself fails
        score = 3
        tier = 3
        method = "fallback"
        reason = f"Scorer error ({ex})  defaulted to Tier 3 | {institution_name}"

    return {
        "score": score,
        "max": 20,
        "reason": reason,
        "tier": tier,
        "method": method,
        "institution": institution_name
    }

def score_consistency(education: list) -> dict:
    """
    Two sub-scores:
    1. GPA trend (5 pts): improving / stable / declining
    2. Field alignment (5 pts): same broad field across degrees
    """

    #  1. GPA Trend 
    relevant_levels = {"undergrad", "postgrad", "doctorate"}
    edu_sorted = sorted(
        [e for e in education
         if (e.get("degree_level") or "").lower() in relevant_levels
         and e.get("normalized_percentage") is not None
         and e.get("end_year") is not None],
        key=lambda e: e["end_year"]
    )

    if len(edu_sorted) <= 1:
        gpa_trend_score = 3
        gpa_reason = "Only one degree  neutral score"
    else:
        drops = []
        improvements = []
        for i in range(1, len(edu_sorted)):
            diff = edu_sorted[i]["normalized_percentage"] - edu_sorted[i-1]["normalized_percentage"]
            if diff > 0:
                improvements.append(diff)
            elif diff < 0:
                drops.append(abs(diff))

        max_drop = max(drops) if drops else 0

        if max_drop == 0:
            gpa_trend_score = 5
            gpa_reason = "GPA improving across all degrees"
        elif max_drop < 5:
            gpa_trend_score = 4
            gpa_reason = f"GPA stable (max drop {max_drop:.1f}% < 5%)"
        elif max_drop <= 15:
            gpa_trend_score = 3
            gpa_reason = f"GPA slight decline (max drop {max_drop:.1f}%)"
        else:
            gpa_trend_score = 1
            gpa_reason = f"GPA sharp decline (max drop {max_drop:.1f}% > 15%)"

    #  2. Field Alignment 
    FIELD_KEYWORDS = [
        "electrical", "electronics", "computer", "software", "mechanical",
        "civil", "chemical", "physics", "math", "biology", "medicine",
        "management", "business", "telecom", "communication", "network"
    ]

    def extract_field_keyword(field_str: str) -> str:
        if not field_str:
            return "unknown"
        f = field_str.lower()
        for kw in FIELD_KEYWORDS:
            if kw in f:
                return kw
        return f.split()[0] if f.split() else "unknown"

    higher_edu = [
        e for e in education
        if (e.get("degree_level") or "").lower() in relevant_levels
        and e.get("field")
    ]

    if len(higher_edu) <= 1:
        field_score = 5
        field_reason = "Single field  full alignment"
    else:
        keywords = [extract_field_keyword(e["field"]) for e in higher_edu]
        most_common = max(set(keywords), key=keywords.count)
        match_count = keywords.count(most_common)
        total = len(keywords)

        if match_count == total:
            field_score = 5
            field_reason = f"All degrees in same field ({most_common})"
        elif match_count >= total - 1:
            field_score = 3
            field_reason = f"Mostly same field ({match_count}/{total} match '{most_common}')"
        else:
            field_score = 1
            field_reason = f"Diverse fields  {keywords}"

    total_score = gpa_trend_score + field_score
    reason = f"GPA trend: {gpa_reason} | Field: {field_reason}"

    return {
        "score": total_score,
        "max": 10,
        "reason": reason,
        "gpa_trend_score": gpa_trend_score,
        "field_alignment_score": field_score
    }

def score_data_completeness(candidate_data: dict) -> dict:
    """
    Bonus points (0-5) for completeness of candidate profile.
    """
    pts = 0
    checks = []

    # +1: at least one education entry
    if candidate_data.get("education"):
        pts += 1
        checks.append("Education records: present")
    else:
        checks.append("Education records: MISSING")

    # +1: CGPA or percentage present in highest degree
    # Find highest-level degree
    level_order = {"doctorate": 3, "postgrad": 2, "undergrad": 1, "school": 0}
    edu = candidate_data.get("education", [])
    if edu:
        top_degree = max(edu, key=lambda e: level_order.get(
            (e.get("degree_level") or "").lower(), 0))
        has_grade = (
            top_degree.get("cgpa") is not None or
            top_degree.get("percentage") is not None or
            top_degree.get("normalized_percentage") is not None
        )
        if has_grade:
            pts += 1
            checks.append("GPA/percentage in top degree: present")
        else:
            checks.append("GPA/percentage in top degree: MISSING")

    # +1: at least one experience entry
    if candidate_data.get("experience"):
        pts += 1
        checks.append("Experience records: present")
    else:
        checks.append("Experience records: MISSING")

    # +1: email present
    if candidate_data.get("email"):
        pts += 1
        checks.append("Email: present")
    else:
        checks.append("Email: MISSING")

    # +1: phone present
    if candidate_data.get("phone"):
        pts += 1
        checks.append("Phone: present")
    else:
        checks.append("Phone: MISSING")

    reason = " | ".join(checks)

    return {
        "score": pts,
        "max": 5,
        "reason": reason
    }

def score_continuity(education: list, experience: list) -> dict:
    """
    Detects gaps between consecutive degrees and applies penalties.
    Recovers 1 pt per gap if covered by experience/publications.
    """

    relevant_levels = {"undergrad", "postgrad", "doctorate"}

    # Sort by end_year, filter out school and missing years
    edu_sorted = sorted(
        [e for e in education
         if (e.get("degree_level") or "").lower() in relevant_levels
         and e.get("end_year") is not None],
        key=lambda e: e["end_year"]
    )

    if len(edu_sorted) < 2:
        return {
            "score": 10, "max": 10,
            "reason": "Only one degree  no gaps to measure",
            "gaps_found": []
        }

    # Build experience year coverage set
    exp_years = set()
    for ex in experience:
        try:
            s = int(ex["start_date"][:4]) if ex.get("start_date") else None
            e_yr = int(ex["end_date"][:4]) if ex.get("end_date") else CURRENT_YEAR
            if s:
                exp_years.update(range(s, e_yr + 1))
        except (ValueError, TypeError):
            pass

    score = 10
    gaps_found = []

    # Check gap between each consecutive pair
    for i in range(1, len(edu_sorted)):
        prev_end = edu_sorted[i-1]["end_year"]
        curr_end = edu_sorted[i]["end_year"]
        gap = curr_end - prev_end

        if gap <= 1:
            continue  # normal, no penalty

        # Determine penalty
        if gap <= 3:
            penalty = 1
            size_label = "minor"
        elif gap <= 7:
            penalty = 2
            size_label = "moderate"
        else:
            penalty = 3
            size_label = "large"

        # Check if gap years are covered by experience
        gap_years = set(range(prev_end, curr_end))
        coverage = len(gap_years & exp_years)
        coverage_pct = coverage / len(gap_years) if gap_years else 0
        justified = coverage_pct >= 0.7

        if justified:
            penalty = max(0, penalty - 1)  # recover 1 pt

        score -= penalty

        gap_desc = (
            f"{gap} yrs ({prev_end}{curr_end}) [{size_label}]"
            f"{'  justified by work' if justified else '  unexplained'}"
        )
        gaps_found.append(gap_desc)

    score = max(0, score)

    reason = (
        f"{len(gaps_found)} gap(s) found: {'; '.join(gaps_found)}"
        if gaps_found else "No significant gaps detected"
    )

    return {
        "score": score,
        "max": 10,
        "reason": reason,
        "gaps_found": gaps_found
    }


def score_education(candidate_data: dict) -> dict:
    """
    Main function. Runs all 6 components and combines into final score.
    """
    education   = candidate_data.get("education", [])
    experience  = candidate_data.get("experience", [])

    # Run all components
    degree_result      = score_degree_level(education)
    gpa_result         = score_overall_gpa(education)
    institution_result = score_institution_quality(education)
    consistency_result = score_consistency(education)
    continuity_result  = score_continuity(education, experience)
    completeness_result = score_data_completeness(candidate_data)

    # Totals
    base_total = (
        degree_result["score"] +
        gpa_result["score"] +
        institution_result["score"] +
        consistency_result["score"] +
        continuity_result["score"]
    )
    bonus       = completeness_result["score"]
    final_total = base_total + bonus

    # Label based on final_total (including bonus)
    if   final_total >= 90: label = "EXCELLENT"
    elif final_total >= 75: label = "GOOD"
    elif final_total >= 60: label = "AVERAGE"
    else:                  label = "WEAK"

    return {
        "candidate_id": candidate_data.get("candidate_id", ""),
        "name":         candidate_data.get("name", "Unknown"),
        "components": {
            "degree_level":       degree_result,
            "overall_gpa":        gpa_result,
            "institution_quality": institution_result,
            "consistency":        consistency_result,
            "continuity":         continuity_result,
            "data_completeness":  completeness_result,
        },
        "base_total":  base_total,
        "bonus":       bonus,
        "final_total": final_total,
        "label":       label
    }

def pretty_print_result(result: dict):
    c = result["components"]
    w = 56  # width

    print("" * w)
    print(f"  EDUCATION SCORE REPORT  {result['name']}")
    print("" * w)

    rows = [
        ("Degree Level",        c["degree_level"],        ""),
        ("Overall GPA",         c["overall_gpa"],         f"Weighted avg: {c['overall_gpa'].get('weighted_avg', 0):.1f}%"),
        ("Institution Quality", c["institution_quality"], f"Tier {c['institution_quality'].get('tier','?')} | {c['institution_quality'].get('method','?')}"),
        ("Consistency",         c["consistency"],         f"GPA: {c['consistency']['gpa_trend_score']} | Field: {c['consistency']['field_alignment_score']}"),
        ("Continuity",          c["continuity"],          f"{len(c['continuity']['gaps_found'])} gap(s) found"),
    ]

    for label, comp, extra in rows:
        score_str = f"{comp['score']} / {comp['max']}"
        print(f"  {label:<22} {score_str:<8}  {extra}")

    print("" * w)
    print(f"  {'Base Total':<22} {result['base_total']} / 95")
    print(f"  {'Bonus (Completeness)':<22} {result['bonus']} / 5")
    print("" * w)

    stars = " " if result["label"] in ("EXCELLENT", "GOOD") else ""
    print(f"  {'FINAL TOTAL':<22} {result['final_total']} / 100   {stars}{result['label']}")
    print("" * w)

    # Gap details if any
    gaps = c["continuity"]["gaps_found"]
    if gaps:
        print("\n  Gap Details:")
        for g in gaps:
            print(f"     {g}")

    # Reasons
    print("\n  Component Reasons:")
    for key, comp in c.items():
        print(f"    [{key}] {comp['reason']}")




"""
edu_score_helpers.py
Save and load education scores for Module 3.1
"""

import json
from datetime import datetime
from db_models import EducationScore, Candidate

def save_education_score(candidate_id: int, result: dict) -> bool:
    """
    Save education module (3.1) score to database.
    
    Args:
        candidate_id (int): Candidate database ID
        result (dict): Result dict from education analysis with structure:
            {
                "name": str,
                "components": {...},
                "base_total": float,
                "bonus": float,
                "final_total": float,
                "label": str,
                ...
            }
    
    Returns:
        bool: True if saved successfully, False otherwise
    """
    # Import here to delay database engine creation until first use
    from db_connect import get_session
    
    session = get_session()
    
    try:
        # Verify candidate exists
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            print(f" Candidate with ID {candidate_id} not found")
            return False
        
        # Extract component scores
        components = result.get("components", {})
        
        degree_level = components.get("degree_level", {})
        overall_gpa = components.get("overall_gpa", {})
        institution_quality = components.get("institution_quality", {})
        consistency = components.get("consistency", {})
        continuity = components.get("continuity", {})
        
        # Create new score record
        edu_score = EducationScore(
            candidate_id=candidate_id,
            
            # Component scores
            degree_level_score=float(degree_level.get("score", 0)),
            overall_gpa_score=float(overall_gpa.get("score", 0)),
            institution_quality_score=float(institution_quality.get("score", 0)),
            consistency_score=float(consistency.get("score", 0)),
            continuity_score=float(continuity.get("score", 0)),
            data_completeness_bonus=float(result.get("bonus", 0)),
            
            # Final scores
            raw_score=float(result.get("final_total", 0)),
            grade=result.get("label", "UNKNOWN"),
            
            # Store all reasons as JSON for audit trail
            reasons=json.dumps({
                "degree_level_reason": degree_level.get("reason", ""),
                "overall_gpa_reason": overall_gpa.get("reason", ""),
                "institution_quality_reason": institution_quality.get("reason", ""),
                "consistency_reason": consistency.get("reason", ""),
                "continuity_reason": continuity.get("reason", ""),
                "data_completeness_reason": result.get("bonus_reason", ""),
            })
        )
        
        # Delete previous education score if exists (keep only latest)
        session.query(EducationScore).filter_by(candidate_id=candidate_id).delete()
        
        # Save new record
        session.add(edu_score)
        session.commit()
        
        print(f" Saved education score for {candidate.name} (ID: {candidate_id})")
        print(f"   Grade: {edu_score.grade} | Score: {edu_score.raw_score}/100")
        return True
        
    except Exception as e:
        session.rollback()
        print(f" Error saving education score: {e}")
        return False
    finally:
        session.close()


from typing import Optional

def load_education_score(candidate_id: int) -> Optional[dict]:
    """
    Load education score from database.
    
    Args:
        candidate_id (int): Candidate database ID
    
    Returns:
        dict: Score data, or None if not found
    """
    session = get_session()
    
    try:
        score = session.query(EducationScore).filter_by(candidate_id=candidate_id).first()
        
        if not score:
            print(f"  No education score found for candidate {candidate_id}")
            return None
        
        # Parse reasons back from JSON
        reasons = {}
        if score.reasons:
            reasons = json.loads(score.reasons)
        
        result = {
            "id": score.id,
            "candidate_id": score.candidate_id,
            "created_at": score.created_at.isoformat() if score.created_at else None,
            
            "components": {
                "degree_level": {
                    "score": score.degree_level_score,
                    "max": 25,
                    "reason": reasons.get("degree_level_reason", "")
                },
                "overall_gpa": {
                    "score": score.overall_gpa_score,
                    "max": 30,
                    "reason": reasons.get("overall_gpa_reason", "")
                },
                "institution_quality": {
                    "score": score.institution_quality_score,
                    "max": 20,
                    "reason": reasons.get("institution_quality_reason", "")
                },
                "consistency": {
                    "score": score.consistency_score,
                    "max": 10,
                    "reason": reasons.get("consistency_reason", "")
                },
                "continuity": {
                    "score": score.continuity_score,
                    "max": 10,
                    "reason": reasons.get("continuity_reason", "")
                },
            },
            
            "base_total": sum([
                score.degree_level_score,
                score.overall_gpa_score,
                score.institution_quality_score,
                score.consistency_score,
                score.continuity_score
            ]),
            "bonus": score.data_completeness_bonus,
            "final_total": score.raw_score,
            "label": score.grade,
        }
        
        return result
        
    except Exception as e:
        print(f" Error loading education score: {e}")
        return None
    finally:
        session.close()


def pretty_print_education_score(score_data: dict):
    """
    Pretty print education score (same format as your original output)
    
    Args:
        score_data (dict): Score data from load_education_score()
    """
    if not score_data:
        print("No score data to display")
        return
    
    c = score_data["components"]
    w = 56
    
    print("" * w)
    print(f"  EDUCATION SCORE REPORT (from DB)")
    print("" * w)
    
    rows = [
        ("Degree Level",        c["degree_level"],        ""),
        ("Overall GPA",         c["overall_gpa"],         ""),
        ("Institution Quality", c["institution_quality"], ""),
        ("Consistency",         c["consistency"],         ""),
        ("Continuity",          c["continuity"],          ""),
    ]
    
    for label, comp, extra in rows:
        score_str = f"{comp['score']:.1f} / {comp['max']}"
        print(f"  {label:<22} {score_str:<8}  {extra}")
    
    print("" * w)
    print(f"  {'Base Total':<22} {score_data['base_total']:.1f} / 95")
    print(f"  {'Bonus (Completeness)':<22} {score_data['bonus']:.1f} / 5")
    print("" * w)
    print(f"  {'FINAL TOTAL':<22} {score_data['final_total']:.1f} / 100   {score_data['label']}")
    print("" * w)
    
    # Reasons
    print("\n  Component Reasons:")
    for key, comp in c.items():
        if comp['reason']:
            print(f"    [{key}] {comp['reason']}")
    
    if score_data.get("created_at"):
        print(f"\n  Saved at: {score_data['created_at']}")
