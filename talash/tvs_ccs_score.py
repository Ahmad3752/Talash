# ============================================================
# tvs_ccs_score.py
# Complete module for Module 3.6 (Topic Variability)
# and Module 3.7 (Co-author Collaboration) analysis
#
# IMPORTANT: These modules are INFORMATIONAL (not scored)
# They produce structured output ready for:
#   - Display in research profile report
#   - Database storage
#   - Integration into final evaluation pipeline
# ============================================================

import asyncio
import json
from datetime import datetime
from collections import Counter
import re
import os

from pydantic import BaseModel, Field

from dotenv import load_dotenv

from db_models import Candidate, TopicVariabilityScore, CoauthorAnalysisScore

load_dotenv()

from llm_client import litellm_chat

#  Separator helpers 
SEP  = "═" * 60
DASH = "─" * 60
BAR_WIDTH = 16

def _bar(score, max_score):
    filled = round(BAR_WIDTH * score / max_score) if max_score else 0
    return "█" * filled + "░" * (BAR_WIDTH - filled)

def _pct(score, max_score):
    return f"{100 * score / max_score:.1f}%" if max_score else "N/A"


# ============================================================
# MODULE 3.6: Topic Variability Analysis (LLM-Based)
# ============================================================

class ThemeEntry(BaseModel):
    theme_name: str = Field(
        description="Short label for this research theme (3-5 words max)"
    )
    description: str = Field(
        description="One sentence summarizing what papers in this theme cover"
    )
    paper_count: int = Field(
        description="Number of papers assigned to this theme"
    )
    percentage: float = Field(
        description="Percentage of all publications falling in this theme (0-100)"
    )
    paper_ids: list[int] = Field(
        description="List of publication IDs assigned to this theme"
    )


class TopicTrendResult(BaseModel):
    trend: str = Field(
        description="One of: 'stable', 'shifting', 'expanding', 'insufficient_data'"
    )
    explanation: str = Field(
        description="One sentence explaining the trend"
    )


class TopicVariabilityResult(BaseModel):
    themes: list[ThemeEntry] = Field(
        description="Between 1 and 5 distinct research theme clusters"
    )
    dominant_theme: str = Field(
        description="The theme_name with the highest paper_count"
    )
    diversity_score: float = Field(
        description="Score from 0.0 to 10.0 for research breadth"
    )
    focus_type: str = Field(
        description="One of: 'deep_specialist' | 'broad_specialist' | 'generalist' | 'interdisciplinary'"
    )
    topic_trend: TopicTrendResult
    overall_interpretation: str = Field(
        description="2-3 sentences for evaluator summarizing research breadth"
    )


def _extract_json_from_response(text: str) -> str:
    """
    Robustly extract a JSON object from an LLM response that may contain
    markdown fences, prose headers, or plain text before/after the JSON.

    Strategy order:
      1. Strip ```json ... ``` or ``` ... ``` fences.
      2. If the result starts with '{', use it directly.
      3. Otherwise, find the first '{' and last '}' in the original text
         and extract the substring (handles prose preambles like **Themes:**).
      4. Return whatever we have so Pydantic can report a useful error.
    """
    # Strategy 1: remove markdown fences
    cleaned = re.sub(
        r"^```json\s*|^```\s*|```\s*$", "", text, flags=re.MULTILINE
    ).strip()

    if cleaned.startswith("{"):
        return cleaned

    # Strategy 2: find outermost JSON object in the raw text
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    # Strategy 3: give back the cleaned text and let Pydantic error
    return cleaned


def analyse_topic_variability(publications: list) -> dict:
    """
    Module 3.6  Topic Variability Analysis.
    
    Clusters publications into semantic research themes and computes
    diversity scores using LLM clustering.
    """
    
    #  Guard: no publications 
    if not publications:
        return {
            "applicable": False,
            "reason": "No publications found — topic variability cannot be assessed.",
            "themes": [],
            "dominant_theme": None,
            "diversity_score": None,
            "focus_type": None,
            "topic_trend": None,
            "trend_explanation": None,
            "overall_interpretation": None,
        }

    #  Guard: only 1 publication 
    if len(publications) == 1:
        return {
            "applicable": True,
            "reason": "Only 1 publication — diversity analysis has limited value.",
            "themes": [],
            "dominant_theme": None,
            "diversity_score": 0.0,
            "focus_type": "deep_specialist",
            "topic_trend": "insufficient_data",
            "trend_explanation": "A single publication cannot indicate trend direction.",
            "overall_interpretation": (
                "With only one publication, no meaningful topic variability "
                "analysis can be performed. Future publications will determine "
                "whether the candidate is a specialist or generalist."
            ),
        }

    #  Build prompt 
    pub_lines = ""
    for pub in publications:
        venue = (
            pub.get("journal_name")
            or pub.get("conference_name")
            or pub.get("venue")
            or "Unknown venue"
        )
        pub_lines += (
            f"\n[PUB {pub['id']}]"
            f"  Year: {pub.get('year', '?')} |"
            f"  Type: {pub.get('pub_type', '?')} |"
            f"  Venue: {venue}\n"
            f"  Title: {pub.get('title', 'No title')}\n"
        )

    prompt = f"""You are an expert research analyst evaluating a candidate's publication portfolio.

Your task is to:
1. Read ALL {len(publications)} publications listed below.
2. Group them into DISTINCT research themes (max 5 themes, fewer is better).
3. Compute a topic diversity score (0-10).
4. Identify the topic trend over time.
5. Write a 2-3 sentence overall interpretation for an evaluator.

CRITICAL OUTPUT RULES:
- Return ONLY a valid JSON object. No markdown. No prose. No headers. No explanation.
- Do NOT start with "**", "Research Themes", or any other text.
- Your ENTIRE response must start with {{ and end with }}.
- Every single [PUB N] must be assigned to exactly ONE theme.
- Use the PUB ID numbers exactly as shown (e.g., if you see [PUB 10], use 10).
- Merge closely related topics — do NOT create a theme per paper.
- The paper_ids list in each theme must contain the actual integer IDs shown.
- percentages across all themes must sum to exactly 100.

DIVERSITY SCORE GUIDE:
  0-2   All papers in one narrow subfield
  3-5   One main area with minor excursions
  6-8   Two or three strong, clearly different research areas
  9-10  Four or more unrelated areas — true generalist/interdisciplinary

TOPIC TREND GUIDE (look at years of each paper per theme):
  stable        Same area across all years
  shifting      Early papers in area A, later papers in area B
  expanding     Core area stable but new subfields added in later years
  insufficient  Too few papers or all published in the same year

REQUIRED JSON STRUCTURE:
{{
  "themes": [
    {{
      "theme_name": "...",
      "description": "...",
      "paper_count": <int>,
      "percentage": <float>,
      "paper_ids": [<int>, ...]
    }}
  ],
  "dominant_theme": "...",
  "diversity_score": <float 0-10>,
  "focus_type": "deep_specialist" | "broad_specialist" | "generalist" | "interdisciplinary",
  "topic_trend": {{
    "trend": "stable" | "shifting" | "expanding" | "insufficient_data",
    "explanation": "..."
  }},
  "overall_interpretation": "..."
}}

PUBLICATIONS  ({len(publications)} total)

{pub_lines}

Remember: respond with ONLY the JSON object above. Nothing else.
"""

    print(f"     [3.6] Calling LLM to cluster {len(publications)} publication(s)...")
    try:
        result_raw  = litellm_chat(prompt)
        content_llm = result_raw.content

        # Robustly extract JSON from whatever the LLM returned
        json_str = _extract_json_from_response(content_llm)

        result = TopicVariabilityResult.model_validate_json(json_str)

    except Exception as e:
        print(f"      LLM topic analysis failed: {e}")
        return {
            "applicable": False,
            "reason": f"LLM evaluation failed: {str(e)}",
            "themes": [],
            "dominant_theme": None,
            "diversity_score": None,
            "focus_type": None,
            "topic_trend": None,
            "trend_explanation": None,
            "overall_interpretation": None,
        }

    #  Validate paper_ids coverage 
    all_pub_ids   = {pub["id"] for pub in publications}
    assigned_ids  = set()
    for theme in result.themes:
        for pid in theme.paper_ids:
            assigned_ids.add(pid)

    missing  = all_pub_ids - assigned_ids
    extra    = assigned_ids - all_pub_ids

    id_coverage_ok = (len(missing) == 0 and len(extra) == 0)

    #  Build return dict 
    themes_list = []
    for theme in result.themes:
        themes_list.append({
            "theme_name":  theme.theme_name,
            "description": theme.description,
            "paper_count": theme.paper_count,
            "percentage":  round(theme.percentage, 1),
            "paper_ids":   theme.paper_ids,
        })

    # Sort themes descending by paper_count
    themes_list.sort(key=lambda t: t["paper_count"], reverse=True)

    return {
        "applicable":             True,
        "reason":                 f"{len(publications)} publication(s) analysed.",
        "themes":                 themes_list,
        "dominant_theme":         result.dominant_theme,
        "diversity_score":        round(result.diversity_score, 1),
        "focus_type":             result.focus_type,
        "topic_trend":            result.topic_trend.trend,
        "trend_explanation":      result.topic_trend.explanation,
        "overall_interpretation": result.overall_interpretation,
        "_meta": {
            "total_publications":    len(publications),
            "themes_identified":     len(themes_list),
            "id_coverage_ok":        id_coverage_ok,
            "missing_pub_ids":       list(missing),
            "extra_pub_ids":         list(extra),
        },
    }


# ============================================================
# MODULE 3.7: Co-author Collaboration Analysis (Direct)
# ============================================================

def _normalise_name(raw: str) -> str:
    """Normalise an author name string to canonical form."""
    # FIX: Guard against None input
    if raw is None:
        return ""

    name = raw.strip()
    if not name or name.lower() in {"et al.", "et al", "..."}:
        return ""

    name = re.sub(r"\.", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    tokens = name.split()
    normalised_tokens = []
    for tok in tokens:
        if len(tok) == 1:
            normalised_tokens.append(tok.upper())
        else:
            normalised_tokens.append(tok.capitalize())
    return " ".join(normalised_tokens)


def _is_same_person(name_a: str, name_b: str) -> bool:
    """Fuzzy check: are two author name strings the same person?"""
    if not name_a or not name_b:
        return False

    tokens_a = name_a.split()
    tokens_b = name_b.split()

    if name_a == name_b:
        return True

    if tokens_a and tokens_b:
        last_a = tokens_a[-1]
        last_b = tokens_b[-1]
        if last_a != last_b:
            return False

        first_a = tokens_a[0][0].upper() if tokens_a else ""
        first_b = tokens_b[0][0].upper() if tokens_b else ""
        return first_a == first_b

    return False


def _parse_author_list(authors_string: str) -> list[str]:
    """Split a comma-separated author string into a cleaned list."""
    if not authors_string or not authors_string.strip():
        return []

    raw_parts = authors_string.split(",")
    result = []
    for part in raw_parts:
        normalised = _normalise_name(part)
        if normalised:
            result.append(normalised)
    return result


def _resolve_candidate_name(candidate_name: str, author_list: list[str]) -> str | None:
    """Find the version of the candidate's name in the author list."""
    cand_norm = _normalise_name(candidate_name)
    for author in author_list:
        if _is_same_person(cand_norm, author):
            return author
    return None


_INTL_INDICATORS = [
    "shanshan", "tu", "wei", "li", "zhang", "wang", "chen", "liu",
    "alenezi", "fayadh", "alnaim", "norah", "alamri", "atif", "alqahtani",
    "mardeni", "roslee", "bin", "singh", "kumar", "patel",
]

def _detect_international(coauthor_names: list[str]) -> bool:
    """Rough heuristic: does co-author list suggest international collaboration?"""
    combined = " ".join(coauthor_names).lower()
    return any(indicator in combined for indicator in _INTL_INDICATORS)


def _hhi_diversity(freq_dict: dict) -> float:
    """Compute collaboration diversity using inverted HHI."""
    if not freq_dict:
        return 0.0

    total = sum(freq_dict.values())
    hhi = sum((count / total) ** 2 for count in freq_dict.values())
    diversity = (1.0 - hhi) * 10.0
    return round(diversity, 2)


def _collaboration_style(avg_authors: float, max_authors: int, solo_papers: int, total_pubs: int) -> str:
    """Classify collaboration style based on team size statistics."""
    solo_ratio = solo_papers / total_pubs if total_pubs else 0

    if solo_ratio >= 0.6:
        return "solo_researcher"
    if avg_authors <= 2.5:
        return "small_team"
    if avg_authors >= 4.5 or max_authors >= 7:
        return "large_group"
    return "mixed"


def _collaboration_type(unique_coauthors: int) -> str:
    """Classify collaboration network breadth."""
    if unique_coauthors < 5:
        return "narrow_network"
    if unique_coauthors <= 10:
        return "moderate_network"
    return "broad_network"


def _interpret_collaboration(
    unique_coauthors: int,
    recurring: int,
    style: str,
    coll_type: str,
    diversity_score: float,
    international: bool,
) -> str:
    """Generate 2-3 sentence evaluator interpretation."""
    parts = []

    if coll_type == "broad_network":
        parts.append(
            f"The candidate has a broad collaboration network with {unique_coauthors} "
            f"unique co-authors, indicating strong professional reach."
        )
    elif coll_type == "moderate_network":
        parts.append(
            f"The candidate collaborates with a moderate-sized network of "
            f"{unique_coauthors} unique co-authors."
        )
    else:
        parts.append(
            f"The candidate's collaboration network is narrow, with only "
            f"{unique_coauthors} unique co-author(s), suggesting limited external connections."
        )

    if recurring >= 3:
        parts.append(
            f"There are {recurring} recurring collaborator(s) (appearing in 2+ papers), "
            f"indicating stable and productive long-term research partnerships."
        )
    elif recurring > 0:
        parts.append(
            f"{recurring} collaborator(s) appear in multiple papers, suggesting some stability "
            f"in research partnerships."
        )
    else:
        parts.append(
            "No recurring collaborators detected — each publication involves a different co-author set."
        )

    if international and diversity_score >= 6:
        parts.append(
            "International collaboration is present and the diversity of co-authors is high, "
            "reflecting strong global academic engagement."
        )
    elif international:
        parts.append("Some evidence of international collaboration was detected.")
    elif diversity_score < 3:
        parts.append(
            "Collaboration diversity is low — the candidate tends to work repeatedly "
            "with the same small group."
        )

    return " ".join(parts)


def analyse_coauthors(publications: list, candidate_name: str) -> dict:
    """
    Module 3.7  Co-author Collaboration Analysis.
    
    Parses co-author lists and computes network-level collaboration statistics.
    """

    # FIX: Guard against None or empty candidate name
    if not candidate_name or not str(candidate_name).strip():
        return {
            "applicable": False,
            "reason": "Candidate name is missing — collaboration analysis cannot be assessed.",
            "unique_coauthors": 0,
            "total_collaborations": 0,
            "solo_papers": 0,
            "avg_authors_per_paper": 0.0,
            "max_authors_in_one_paper": 0,
            "top_collaborators": [],
            "recurring_collaborators": 0,
            "collaboration_style": None,
            "network_diversity_score": 0.0,
            "collaboration_type": None,
            "international_flag": False,
            "interpretation": "No candidate name provided.",
            "_meta": {},
        }

    #  Guard: no publications 
    if not publications:
        return {
            "applicable": False,
            "reason": "No publications found — collaboration analysis cannot be assessed.",
            "unique_coauthors": 0,
            "total_collaborations": 0,
            "solo_papers": 0,
            "avg_authors_per_paper": 0.0,
            "max_authors_in_one_paper": 0,
            "top_collaborators": [],
            "recurring_collaborators": 0,
            "collaboration_style": None,
            "network_diversity_score": 0.0,
            "collaboration_type": None,
            "international_flag": False,
            "interpretation": "No publications to analyse.",
            "_meta": {},
        }

    #  Core data structures 
    coauthor_freq: dict[str, int] = {}
    coauthor_papers: dict[str, list[str]] = {}
    author_counts_per_paper: list[int] = []

    solo_count = 0
    collaborative_count = 0
    parse_warnings = []
    cand_norm = _normalise_name(candidate_name)

    #  Per-publication processing 
    for pub in publications:
        raw_authors = pub.get("authors") or ""
        title       = pub.get("title") or "Untitled"
        pub_id      = pub.get("id")

        author_list = _parse_author_list(raw_authors)

        if not author_list:
            parse_warnings.append(f"[PUB {pub_id}] No authors parsed from: '{raw_authors[:60]}'")
            continue

        cand_in_paper = _resolve_candidate_name(candidate_name, author_list)

        if cand_in_paper is None:
            parse_warnings.append(
                f"[PUB {pub_id}] Candidate '{candidate_name}' not matched in author list: "
                f"{author_list}"
            )

        author_counts_per_paper.append(len(author_list))

        coauthors_this_paper = [
            a for a in author_list
            if not _is_same_person(cand_norm, a)
        ]

        if not coauthors_this_paper:
            solo_count += 1
        else:
            collaborative_count += 1
            for coauthor in coauthors_this_paper:
                coauthor_freq[coauthor] = coauthor_freq.get(coauthor, 0) + 1
                if coauthor not in coauthor_papers:
                    coauthor_papers[coauthor] = []
                coauthor_papers[coauthor].append(title)

    #  Aggregate statistics 
    total_pubs  = len(publications)
    unique_coa  = len(coauthor_freq)
    avg_authors = (
        round(sum(author_counts_per_paper) / len(author_counts_per_paper), 2)
        if author_counts_per_paper else 0.0
    )
    max_authors = max(author_counts_per_paper) if author_counts_per_paper else 0

    recurring_count = sum(1 for cnt in coauthor_freq.values() if cnt >= 2)

    top_n = 5
    sorted_coauthors = sorted(
        coauthor_freq.items(),
        key=lambda x: (-x[1], x[0])
    )
    top_collaborators = [
        {
            "name":   name,
            "count":  count,
            "papers": coauthor_papers.get(name, []),
        }
        for name, count in sorted_coauthors[:top_n]
    ]

    diversity_score = _hhi_diversity(coauthor_freq)
    style = _collaboration_style(avg_authors, max_authors, solo_count, total_pubs)
    coll_type = _collaboration_type(unique_coa)
    
    all_coauthor_names = list(coauthor_freq.keys())
    intl_flag = _detect_international(all_coauthor_names)

    interpretation = _interpret_collaboration(
        unique_coa, recurring_count, style, coll_type, diversity_score, intl_flag
    )

    return {
        "applicable": True,
        "reason": f"{total_pubs} publication(s) analysed.",
        "unique_coauthors":          unique_coa,
        "total_collaborations":      collaborative_count,
        "solo_papers":               solo_count,
        "avg_authors_per_paper":     avg_authors,
        "max_authors_in_one_paper":  max_authors,
        "top_collaborators":         top_collaborators,
        "recurring_collaborators":   recurring_count,
        "collaboration_style":       style,
        "network_diversity_score":   diversity_score,
        "collaboration_type":        coll_type,
        "international_flag":        intl_flag,
        "interpretation":            interpretation,
        "_meta": {
            "total_publications":   total_pubs,
            "candidate_name_used":  cand_norm,
            "parse_warnings":       parse_warnings,
            "all_coauthor_freq":    dict(sorted_coauthors),
        },
    }


# ============================================================
# REPORT PRINTERS (3.6 & 3.7)
# ============================================================

def print_topic_variability_report(topic: dict):
    """Print the Module 3.6 section of the research report."""

    print(f"\n{SEP}")
    print(f"  MODULE 3.6  Topic Variability Analysis")
    print(f"{SEP}\n")

    if not topic.get("applicable"):
        print(f"    Not applicable: {topic.get('reason', 'N/A')}")
        print()
        return

    if not topic.get("themes"):
        print(f"    {topic.get('reason', 'Insufficient data for theme clustering.')}")
        print()
        return

    div_score  = topic["diversity_score"]
    focus_type = topic["focus_type"].replace("_", " ").title()
    bar        = _bar(div_score, 10.0)

    print(f"  Diversity Score         {div_score:5.1f} / 10.0  [{bar}]  {_pct(div_score, 10.0)}")
    print(f"  Focus Type              {focus_type}")
    print(f"  Dominant Theme          {topic['dominant_theme']}")
    print()

    print(f"  RESEARCH THEME BREAKDOWN")
    print(f"{DASH}")
    print(f"  {'Theme':<35s}  Papers  %      Bar")
    print(f"  {'─'*35}      ")

    for theme in topic["themes"]:
        theme_bar = _bar(theme["percentage"], 100.0)
        print(
            f"  {theme['theme_name']:<35s}  "
            f"{theme['paper_count']:>4d}    "
            f"{theme['percentage']:>5.1f}%  "
            f"[{theme_bar}]"
        )
        print(f"     {theme['description']}")
    print()

    trend        = topic["topic_trend"].replace("_", " ").title()
    trend_detail = topic["trend_explanation"]
    print(f"  TOPIC TREND")
    print(f"{DASH}")
    print(f"  Trend:    {trend}")
    print(f"  Detail:   {trend_detail}")
    print()

    print(f"  INTERPRETATION")
    print(f"{DASH}")
    words  = topic["overall_interpretation"].split()
    line   = "  "
    for word in words:
        if len(line) + len(word) + 1 > 72:
            print(line)
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)
    print()

    meta = topic.get("_meta", {})
    if not meta.get("id_coverage_ok", True):
        print(f"    ⚠ DATA WARNING: Some publications were not assigned to a theme.")
    else:
        print(f"    ✓ All {meta.get('total_publications', '?')} publication(s) assigned to a theme.")
    print()
    print(f"{SEP}\n")


def print_coauthor_report(coauthor: dict):
    """Print the Module 3.7 section of the research report."""

    print(f"\n{SEP}")
    print(f"  MODULE 3.7  Co-author Collaboration Analysis")
    print(f"{SEP}\n")

    if not coauthor.get("applicable"):
        print(f"    Not applicable: {coauthor.get('reason', 'N/A')}")
        print()
        return

    style     = (coauthor["collaboration_style"] or "N/A").replace("_", " ").title()
    coll_type = (coauthor["collaboration_type"] or "N/A").replace("_", " ").title()
    div_score = coauthor["network_diversity_score"]
    intl_flag = "✓ Detected" if coauthor["international_flag"] else "✗ Not detected"

    print(f"  Unique Co-authors       {coauthor['unique_coauthors']:>5d}")
    print(f"  Collaborative Papers    {coauthor['total_collaborations']:>5d}")
    print(f"  Solo Papers             {coauthor['solo_papers']:>5d}")
    print(f"  Avg Authors / Paper     {coauthor['avg_authors_per_paper']:>8.2f}")
    print(f"  Max Authors (1 paper)   {coauthor['max_authors_in_one_paper']:>5d}")
    print(f"  Recurring Collaborators {coauthor['recurring_collaborators']:>5d}    (appeared in 2+ papers)")
    print()
    print(f"  Collaboration Style     {style}")
    print(f"  Network Type            {coll_type}")
    print(f"  Network Diversity Score {div_score:>5.1f} / 10.0   [{_bar(div_score, 10.0)}]")
    print(f"  International Collab    {intl_flag}")
    print()

    top = coauthor.get("top_collaborators", [])
    if top:
        print(f"  TOP COLLABORATORS")
        print(f"{DASH}")
        max_count = top[0]["count"] if top else 1
        for i, c in enumerate(top, 1):
            bar = _bar(c["count"], max_count)
            print(
                f"  {i}. {c['name']:<35s}  "
                f"{c['count']:>2d}x  [{bar}]"
            )
            for paper_title in c["papers"]:
                short = paper_title[:65] + "…" if len(paper_title) > 65 else paper_title
                print(f"        {short}")
        print()
    else:
        print(f"   ⚠ No co-authors detected.\n")

    print(f"  INTERPRETATION")
    print(f"{DASH}")
    words = coauthor["interpretation"].split()
    line  = "  "
    for word in words:
        if len(line) + len(word) + 1 > 72:
            print(line)
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)
    print()

    warnings = coauthor.get("_meta", {}).get("parse_warnings", [])
    if warnings:
        print(f"    PARSE WARNINGS ({len(warnings)} total)")
        print(f"{DASH}")
        for w in warnings:
            print(f"    {w}")
        print()

    print(f"{SEP}\n")


# ============================================================
# MAIN RUNNER (3.6 & 3.7)
# ============================================================

def run_36_37(candidate: dict) -> dict:
    """
    Run Module 3.6 (Topic Variability) and Module 3.7 (Co-author Analysis).
    
    Parameters
    ----------
    candidate : dict
        Must include: 'name', 'publications'.
    
    Returns
    -------
    {
        "topic_variability":    dict,   # Module 3.6 result
        "coauthor_analysis":    dict,   # Module 3.7 result
    }
    """
    # FIX: Use 'or' to catch None values even when the key exists
    name         = candidate.get("name") or "Unknown"
    publications = candidate.get("publications", [])

    print(f"\n{'─' * 60}")
    print(f"  RUNNING MODULES 3.6 & 3.7    {name}")
    print(f"{'─' * 60}")
    print(f"  Publications available: {len(publications)}")
    print()

    #  Step 1: Topic Variability (LLM call) 
    print("Step 3.6: Analysing topic variability...")
    topic_result = analyse_topic_variability(publications)

    if topic_result.get("applicable") and topic_result.get("themes"):
        print(
            f"   Themes found: {len(topic_result['themes'])} | "
            f"Diversity score: {topic_result['diversity_score']}/10 | "
            f"Type: {topic_result['focus_type']}"
        )
    else:
        print(f"    {topic_result.get('reason', 'N/A')}")

    #  Step 2: Co-author Analysis (direct, no LLM) 
    print("Step 3.7: Analysing co-author collaboration...")
    coauthor_result = analyse_coauthors(publications, name)

    if coauthor_result.get("applicable"):
        print(
            f"   Unique co-authors: {coauthor_result['unique_coauthors']} | "
            f"Diversity: {coauthor_result['network_diversity_score']}/10 | "
            f"Style: {coauthor_result['collaboration_style']}"
        )
    else:
        print(f"    {coauthor_result.get('reason', 'N/A')}")

    #  Step 3: Print reports 
    print_topic_variability_report(topic_result)
    print_coauthor_report(coauthor_result)

    return {
        "topic_variability": topic_result,
        "coauthor_analysis": coauthor_result,
    }


# ============================================================
# DATABASE SAVE FUNCTIONS
# ============================================================

def save_topic_variability_score(candidate_id: int, result: dict) -> bool:
    """Save Module 3.6 (Topic Variability) analysis results to the database."""
    # Import here to delay database engine creation until first use
    from db_connect import get_session
    
    session = get_session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            print(f"      Candidate {candidate_id} not found.")
            return False

        applicable            = result.get("applicable", False)
        reason                = result.get("reason", "")
        themes                = result.get("themes", [])
        dominant_theme        = result.get("dominant_theme")
        diversity_score       = result.get("diversity_score")
        focus_type            = result.get("focus_type")
        topic_trend           = result.get("topic_trend")
        trend_explanation     = result.get("trend_explanation", "")
        overall_interpretation = result.get("overall_interpretation", "")

        meta = result.get("_meta", {})

        tv_score = TopicVariabilityScore(
            candidate_id=candidate_id,
            applicable=applicable,
            reason=reason,
            dominant_theme=dominant_theme,
            diversity_score=diversity_score,
            focus_type=focus_type,
            topic_trend=topic_trend,
            trend_explanation=trend_explanation,
            overall_interpretation=overall_interpretation,
            themes=json.dumps(themes, default=str),
            total_publications=meta.get("total_publications", 0),
            themes_identified=meta.get("themes_identified", 0),
            id_coverage_ok=meta.get("id_coverage_ok", True),
            missing_pub_ids=json.dumps(meta.get("missing_pub_ids", []), default=str),
            extra_pub_ids=json.dumps(meta.get("extra_pub_ids", []), default=str),
            created_at=datetime.utcnow(),
        )

        session.add(tv_score)
        session.commit()

        print(f"     Module 3.6 saved")
        if applicable:
            print(f"       Diversity: {diversity_score}/10 | Focus: {focus_type}")
        return True

    except Exception as e:
        session.rollback()
        print(f"      Error saving Module 3.6: {e}")
        return False
    finally:
        session.close()


def save_coauthor_analysis_score(candidate_id: int, result: dict) -> bool:
    """Save Module 3.7 (Co-author Analysis) results to the database."""
    # Import here to delay database engine creation until first use
    from db_connect import get_session
    
    session = get_session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            print(f"      Candidate {candidate_id} not found.")
            return False

        applicable             = result.get("applicable", False)
        reason                 = result.get("reason", "")
        unique_coauthors       = result.get("unique_coauthors", 0)
        total_collaborations   = result.get("total_collaborations", 0)
        solo_papers            = result.get("solo_papers", 0)
        avg_authors_per_paper  = result.get("avg_authors_per_paper", 0.0)
        max_authors_in_one_paper = result.get("max_authors_in_one_paper", 0)
        top_collaborators      = result.get("top_collaborators", [])
        recurring_collaborators = result.get("recurring_collaborators", 0)
        collaboration_style    = result.get("collaboration_style")
        network_diversity_score = result.get("network_diversity_score", 0.0)
        collaboration_type     = result.get("collaboration_type")
        international_flag     = result.get("international_flag", False)
        interpretation         = result.get("interpretation", "")

        meta = result.get("_meta", {})

        ca_score = CoauthorAnalysisScore(
            candidate_id=candidate_id,
            applicable=applicable,
            reason=reason,
            unique_coauthors=unique_coauthors,
            total_collaborations=total_collaborations,
            solo_papers=solo_papers,
            avg_authors_per_paper=avg_authors_per_paper,
            max_authors_in_one_paper=max_authors_in_one_paper,
            recurring_collaborators=recurring_collaborators,
            collaboration_style=collaboration_style,
            network_diversity_score=network_diversity_score,
            collaboration_type=collaboration_type,
            international_flag=international_flag,
            interpretation=interpretation,
            top_collaborators=json.dumps(top_collaborators, default=str),
            all_coauthor_freq=json.dumps(meta.get("all_coauthor_freq", {}), default=str),
            total_publications=meta.get("total_publications", 0),
            candidate_name_used=meta.get("candidate_name_used", ""),
            parse_warnings=json.dumps(meta.get("parse_warnings", []), default=str),
            created_at=datetime.utcnow(),
        )

        session.add(ca_score)
        session.commit()

        print(f"     Module 3.7 saved")
        if applicable:
            print(f"       Co-authors: {unique_coauthors} | Diversity: {network_diversity_score}/10")
        return True

    except Exception as e:
        session.rollback()
        print(f"      Error saving Module 3.7: {e}")
        return False
    finally:
        session.close()


def save_topic_and_coauthor_scores(candidate_id: int, result: dict) -> bool:
    """Convenience function to save both Module 3.6 and 3.7 scores."""
    topic_result = result.get("topic_variability", {})
    coauthor_result = result.get("coauthor_analysis", {})

    success_36 = save_topic_variability_score(candidate_id, topic_result)
    success_37 = save_coauthor_analysis_score(candidate_id, coauthor_result)

    return success_36 and success_37