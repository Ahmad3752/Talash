# ============================================================================
# research_scores.py  FULL PIPELINE WITH TITLE-BASED METADATA RECOVERY
# ============================================================================
# Flow for each publication:
#   Step 0  Title Recovery   : Crossref title search  OpenAlex fallback
#                               Recovers: doi, issn, venue, year, pub_type
#   Step 1  API Enrichment   : WoS, OpenAlex, CrossRef (using recovered IDs)
#   Step 2  Scoring          : publication quality, authorship, collaboration,
#                               conference maturity, patents/books, supervision
#   Step 3  DB Save          : write ResearchScore row
#
# Entry point: async score_candidate_research(candidate_id: int) -> dict
# LangGraph node: async research_analysis(state: CVState) -> dict
# ============================================================================

import asyncio
import aiohttp
import pandas as pd
import re
import json
import time
from typing import Optional, Dict, List
from difflib import SequenceMatcher

from db_models import Candidate, ResearchScore

# 
# CONFIGURATION
# 

CONFIG = {
    "scimago_path": r"C:\Projects\Talash\datasets\scimagojr 2025.csv",
    "core_path":    r"C:\Projects\Talash\datasets\CORE.csv",
    "wos_path":     r"C:\Projects\Talash\datasets\wos_journals.csv",
    "current_year": 2026,
    "max_concurrent_requests": 10,

    # Title recovery thresholds
    "crossref_score_threshold": 85,   # Crossref API relevance score
    "title_sim_threshold":      0.82, # fuzzy string similarity gate
}

# Global dataset cache  loaded once per process lifetime
_DATASET_CACHE: Dict = {
    "issn_map": None,
    "core_df":  None,
    "loaded":   False,
}


# 
# HELPERS
# 

def normalize_issn(issn: str) -> str:
    return re.sub(r'[-\s"]', '', str(issn)).lower()

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# 
# DATASET LOADING
# 

def load_scimago(filepath: str) -> dict:
    try:
        df = pd.read_csv(filepath, sep=';', encoding='utf-8', on_bad_lines='skip')
        df['Issn'] = df['Issn'].astype(str).str.replace('"', '').str.strip()
        issn_map = {}
        for _, row in df.iterrows():
            q = row.get("SJR Best Quartile")
            if pd.isna(q):
                continue
            for raw in str(row['Issn']).split(","):
                norm = normalize_issn(raw)
                if norm:
                    issn_map[norm] = str(q).strip()
        print(f"   Scimago: {len(issn_map):,} ISSNs loaded")
        return issn_map
    except FileNotFoundError:
        print(f"    Scimago file not found: {filepath}")
        return {}
    except Exception as e:
        print(f"    Error loading Scimago: {e}")
        return {}


def load_core(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath, header=None, dtype=str, on_bad_lines='skip')
        col_names = ['ID', 'Conference', 'Acronym', 'Source', 'Rank',
                     'Open_Access', 'Paper_Count', 'C8', 'C9']
        df.columns = col_names[:len(df.columns)]
        for col in ['Conference', 'Acronym', 'Rank']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        print(f"   CORE: {len(df):,} conferences loaded")
        return df
    except FileNotFoundError:
        print(f"    CORE file not found: {filepath}")
        return pd.DataFrame(columns=['Conference', 'Acronym', 'Rank'])
    except Exception as e:
        print(f"    Error loading CORE: {e}")
        return pd.DataFrame(columns=['Conference', 'Acronym', 'Rank'])


def _ensure_datasets_loaded():
    global _DATASET_CACHE
    if _DATASET_CACHE["loaded"]:
        return
    print("  Loading research datasets (cached globally)...")
    _DATASET_CACHE["issn_map"] = load_scimago(CONFIG["scimago_path"])
    _DATASET_CACHE["core_df"]  = load_core(CONFIG["core_path"])
    _DATASET_CACHE["loaded"]   = True
    print()


# 
# 
#  STEP 0  TITLE-BASED METADATA RECOVERY
# 
# For every publication that is missing doi / issn / real venue name:
#   1. Search Crossref by title    recover doi, issn, venue, publisher, type
#   2. If confidence low           fallback to OpenAlex title search
#   3. Merge into pub dict         never overwrite existing real data
# 

# Venue strings that are effectively "unknown"  trigger title recovery
_GENERIC_VENUES = {
    "international journal", "international conference",
    "journal", "conference", "proceedings", "unknown", "",
}


def _is_generic_venue(venue: str) -> bool:
    return (venue or "").strip().lower() in _GENERIC_VENUES


def _best_crossref_item(items: list, query_title: str):
    """Pick the best Crossref result by API score + fuzzy title similarity."""
    if not items:
        return None, 0
    best_item, best_score = None, 0
    for item in items[:5]:
        api_score  = item.get("score", 0)
        titles     = item.get("title", [])
        item_title = titles[0] if titles else ""
        sim = similarity(query_title, item_title)
        combined   = api_score if sim >= 0.50 else 0   # reject dissimilar matches
        if combined > best_score:
            best_score, best_item = combined, item
    return best_item, best_score


def _extract_issn_from_crossref(item: dict) -> Optional[str]:
    issn_l = item.get("ISSN-L")
    if issn_l:
        return issn_l if isinstance(issn_l, str) else issn_l[0]
    issns = item.get("ISSN", [])
    return issns[0] if issns else None


def _extract_venue_from_crossref(item: dict) -> Optional[str]:
    container = item.get("container-title", [])
    if container:
        return container[0]
    event = item.get("event", {})
    if event.get("name"):
        return event["name"]
    return None


def _extract_year_from_crossref(item: dict) -> Optional[int]:
    for key in ("published", "published-print", "published-online"):
        dp = item.get(key, {}).get("date-parts", [[]])
        if dp and dp[0]:
            return int(dp[0][0])
    return None


async def _resolve_via_crossref(session: aiohttp.ClientSession, title: str) -> dict:
    """Search Crossref by title. Returns recovered metadata dict."""
    if not title:
        return {}
    try:
        params = {
            "query.title": title,
            "rows":        5,
            "select":      (
                "DOI,title,ISSN,ISSN-L,container-title,publisher,"
                "score,published,published-print,published-online,event,type"
            ),
        }
        headers = {"User-Agent": "ResearchProfiler/2.0 (research@uni.edu)"}
        async with session.get(
            "https://api.crossref.org/works",
            params=params, headers=headers,
            timeout=aiohttp.ClientTimeout(total=14),
        ) as r:
            if r.status != 200:
                return {}
            raw = await r.json(content_type=None)

        items = raw.get("message", {}).get("items", [])
        item, score = _best_crossref_item(items, title)

        if not item:
            return {}

        # Accept if API score is high enough OR fuzzy similarity alone is high
        titles_list = item.get("title", [])
        item_title  = titles_list[0] if titles_list else ""
        sim = similarity(title, item_title)

        if score < CONFIG["crossref_score_threshold"] and sim < CONFIG["title_sim_threshold"]:
            print(f"    [CR title] LOW CONFIDENCE score={score:.1f} sim={sim:.2f}: {title[:55]}")
            return {}

        result = {
            "doi":          item.get("DOI"),
            "issn":         _extract_issn_from_crossref(item),
            "venue":        _extract_venue_from_crossref(item),
            "year":         _extract_year_from_crossref(item),
            "publisher_cr": item.get("publisher", ""),
            "cr_type":      item.get("type", ""),
        }
        print(f"    [CR title]  score={score:.1f} sim={sim:.2f} "
              f"doi={result['doi']} issn={result['issn']}")
        return result

    except Exception as e:
        print(f"    [CR title error] {e}")
        return {}


async def _resolve_via_openalex(session: aiohttp.ClientSession, title: str) -> dict:
    """Fallback: search OpenAlex by title."""
    if not title:
        return {}
    try:
        params = {
            "search":   title,
            "per-page": 3,
            "select":   "doi,ids,primary_location,publication_year,title",
        }
        async with session.get(
            "https://api.openalex.org/works",
            params=params,
            timeout=aiohttp.ClientTimeout(total=12),
        ) as r:
            data = await r.json(content_type=None)

        results = data.get("results", [])
        if not results:
            return {}

        best, best_sim = None, 0.0
        for w in results:
            sim = similarity(title, w.get("title") or "")
            if sim > best_sim:
                best_sim, best = sim, w

        if best_sim < CONFIG["title_sim_threshold"]:
            print(f"    [OA title] LOW SIM {best_sim:.2f}: {title[:55]}")
            return {}

        doi = (best.get("doi") or "").replace("https://doi.org/", "") or None
        year = best.get("publication_year")
        src  = (best.get("primary_location") or {}).get("source") or {}
        issn_list = src.get("issn") or []
        issn  = issn_list[0] if issn_list else (src.get("issn_l") or None)
        venue = src.get("display_name") or None

        print(f"    [OA title]  sim={best_sim:.2f} doi={doi} issn={issn}")
        return {"doi": doi, "issn": issn, "venue": venue, "year": year}

    except Exception as e:
        print(f"    [OA title error] {e}")
        return {}


async def resolve_metadata_by_title(pub: dict,
                                     session: aiohttp.ClientSession) -> dict:
    """
    Master resolver  fills missing doi / issn / venue / year via title search.
    Only touches fields that are currently None / generic.
    """
    title = (pub.get("title") or "").strip()
    if not title:
        return pub

    needs_doi   = not pub.get("doi") or "XXXXX" in str(pub.get("doi", ""))
    needs_issn  = not pub.get("issn")
    needs_venue = _is_generic_venue(pub.get("venue", ""))

    if not (needs_doi or needs_issn or needs_venue):
        return pub   # nothing missing  skip entirely

    short = title[:65] + ("" if len(title) > 65 else "")
    print(f"\n  [Title recovery] '{short}'")
    print(f"    needs  doi:{needs_doi}  issn:{needs_issn}  venue:{needs_venue}")

    # Crossref first
    meta = await _resolve_via_crossref(session, title)

    # OpenAlex fallback if Crossref didn't return both doi + issn
    if not meta or (needs_issn and not meta.get("issn") and needs_doi and not meta.get("doi")):
        oa = await _resolve_via_openalex(session, title)
        for k, v in oa.items():
            if v and not meta.get(k):
                meta[k] = v

    # Apply  only fill gaps
    if meta.get("doi")   and needs_doi:
        pub["doi"]   = meta["doi"]
        print(f"     doi   : {meta['doi']}")

    if meta.get("issn")  and needs_issn:
        pub["issn"]  = meta["issn"]
        print(f"     issn  : {meta['issn']}")

    if meta.get("venue") and needs_venue:
        pub["venue"] = meta["venue"]
        print(f"     venue : {meta['venue']}")

    if meta.get("year")  and not pub.get("year"):
        pub["year"]  = meta["year"]
        print(f"     year  : {meta['year']}")

    # Auto-correct pub_type from Crossref type field
    cr_type = meta.get("cr_type", "")
    if cr_type == "proceedings-article" and pub.get("pub_type") != "conference":
        pub["pub_type"] = "conference"
        print(f"     pub_type corrected  conference")
    elif cr_type == "journal-article" and pub.get("pub_type") != "journal":
        pub["pub_type"] = "journal"
        print(f"     pub_type corrected  journal")

    # Store publisher hint for conference indexing detection later
    if meta.get("publisher_cr"):
        pub["_publisher_hint"] = meta["publisher_cr"]

    return pub


# 
# STEP 1  API ENRICHMENT  (journal-specific)
# 

async def _fetch_openalex_journal(session: aiohttp.ClientSession, issn: str) -> dict:
    if not issn:
        return {}
    try:
        url = f"https://api.openalex.org/sources?filter=issn:{issn}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
            data = await r.json(content_type=None)
        results = data.get("results", [])
        if not results:
            return {}
        stats   = results[0].get("summary_stats", {})
        raw_2yr = stats.get("2yr_mean_citedness")
        return {
            "found":             True,
            "avg_citations_2yr": round(raw_2yr, 3) if raw_2yr is not None else None,
            "h_index":           stats.get("h_index"),
            "scopus_proxy":      (stats.get("h_index") or 0) > 10,
        }
    except Exception:
        return {}


async def _check_wos(session: aiohttp.ClientSession, issn: str) -> dict:
    if not issn:
        return {"wos_indexed": False, "impact_factor": None}
    try:
        url = f"https://wos-journal.info/journalid/{issn}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as r:
            text = await r.text()
        if "Journal Citation Reports" not in text:
            return {"wos_indexed": False, "impact_factor": None}
        impact_factor = None
        patterns = [
            r'Impact\s+Factor[^\d]{0,30}?([\d]+[.,][\d]+)',
            r'JIF[^\d]{0,20}?([\d]+[.,][\d]+)',
            r'<td[^>]*>\s*([\d]+[.,][\d]+)\s*</td>(?=[^<]*Impact)',
            r'([\d]+[.,][\d]+)\s*(?:Impact Factor)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                try:
                    val = float(m.group(1).replace(',', '.'))
                    if 0.05 <= val <= 100:
                        impact_factor = val
                        break
                except ValueError:
                    continue
        return {"wos_indexed": True, "impact_factor": impact_factor}
    except Exception:
        return {"wos_indexed": False, "impact_factor": None}


def _merge_if(wos_if, oa_2yr) -> Optional[float]:
    return wos_if if wos_if is not None else oa_2yr


async def _fetch_crossref_doi(session: aiohttp.ClientSession,
                               doi: str, candidate: str) -> dict:
    """Fetch authorship / publisher via known DOI."""
    if not doi or "XXXXX" in str(doi):
        return {"found": False}
    try:
        url = f"https://api.crossref.org/works/{doi}"
        headers = {"User-Agent": "ResearchProfiler/2.0 (research@uni.edu)"}
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=12)) as r:
            if r.status != 200:
                return {"found": False}
            raw = await r.json(content_type=None)
        msg = raw.get("message") or {}
        return {
            "found":     True,
            "role":      _detect_role(msg.get("author") or [], candidate),
            "publisher": msg.get("publisher", ""),
        }
    except Exception:
        return {"found": False}


def _detect_role(authors: list, candidate: str) -> str:
    if not authors or not candidate:
        return "unknown"
    parts    = candidate.lower().split()
    last     = parts[-1]
    first    = parts[0] if len(parts) > 1 else ""
    is_first = is_corr = matched = False
    for i, a in enumerate(authors):
        family = a.get("family", "").lower()
        given  = a.get("given",  "").lower()
        if last not in family and last not in given:
            continue
        if first and first not in given and first not in family:
            continue
        matched = True
        if a.get("sequence") == "first" or i == 0:
            is_first = True
        for aff in a.get("affiliation", []):
            if "correspond" in str(aff).lower():
                is_corr = True
        break
    if not matched:          return "unknown"
    if is_first and is_corr: return "first_and_corresponding"
    if is_first:             return "first_author"
    if is_corr:              return "corresponding_author"
    return "co_author"


# 
# STEP 1  API ENRICHMENT  (conference-specific)
# 

PUBLISHER_RULES = [
    (["IEEE"],                                                 "IEEE",      ["IEEE Xplore", "Scopus"]),
    (["ACM ", " ACM", "(ACM)", "SIGCOMM", "SIGGRAPH",
      "SIGKDD", "CHI "],                                      "ACM",       ["ACM Digital Library", "Scopus"]),
    (["SPRINGER", "LECTURE NOTES", "LNCS", "LNAI", "LNEE"],  "Springer",  ["Springer", "Scopus"]),
    (["ELSEVIER", "PROCEDIA"],                                "Elsevier",  ["Elsevier", "Scopus"]),
    (["WILEY"],                                               "Wiley",     ["Wiley", "Scopus"]),
    (["USENIX"],                                              "USENIX",    ["USENIX"]),
    (["IFIP"],                                                "IFIP",      ["Springer", "Scopus"]),
    (["AAAI"],                                                "AAAI",      ["AAAI", "Scopus"]),
    (["ICLR", "NEURIPS", "NIPS", "ICML"],                     "ML Conf",   ["OpenReview/PMLR", "Scopus"]),
    (["INTERSPEECH", "ICASSP", "EUSIPCO"],                    "ISCA/IEEE", ["IEEE Xplore", "Scopus"]),
    (["MULTIMEDIA UNIVERSITY", "MMU"],                        "MMU",       ["IEEE Xplore"]),
]

SCOPUS_SIGNALS = [
    "INTERNATIONAL CONFERENCE", "ANNUAL CONFERENCE", "SYMPOSIUM ON",
    "WORKSHOP ON", "WORLD CONGRESS", "GLOBAL CONFERENCE",
]


def _detect_conference_indexing(venue: str,
                                 crossref_pub: str = "",
                                 publisher_hint: str = "") -> dict:
    combined = f"{venue} {crossref_pub} {publisher_hint}".upper()
    for keywords, label, databases in PUBLISHER_RULES:
        if any(kw in combined for kw in keywords):
            return {
                "publisher":           label,
                "proc_indexed_in":     databases,
                "proc_scopus_indexed": "Scopus" in databases,
            }
    possibly_scopus = any(sig in combined for sig in SCOPUS_SIGNALS)
    databases = ["Scopus (possible)"] if possibly_scopus else []
    return {
        "publisher":           "Unknown",
        "proc_indexed_in":     databases,
        "proc_scopus_indexed": possibly_scopus,
    }


def _determine_legitimacy(cr_found: bool, publisher: str,
                           core_rank, proc_indexed: list):
    if cr_found:                   return True
    if publisher != "Unknown":     return True
    if core_rank and str(core_rank).strip().upper() not in ("NONE", "NAN", ""):
        return True
    if proc_indexed:               return "uncertain"
    return "uncertain"


async def _fetch_openalex_conf_age(session: aiohttp.ClientSession,
                                    venue: str) -> dict:
    if not venue:
        return {}
    strategies = []
    m = re.search(r'\(([A-Z0-9\-]+)\)', venue)
    if m:
        strategies.append(m.group(1))
    clean = re.sub(r'^\d{4}\s+', '', venue)
    clean = re.sub(r'\([^)]*\)', '', clean).strip()
    words = [w for w in clean.split() if len(w) > 3][:5]
    if words:
        strategies.append(" ".join(words))
    strategies.append(" ".join(venue.split()[:3]))

    for q in strategies:
        try:
            url = (
                "https://api.openalex.org/works"
                f"?filter=primary_location.source.display_name.search:{q}"
                "&sort=publication_year:asc&per-page=1"
            )
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json(content_type=None)
            results = data.get("results", [])
            if results:
                yr = results[0].get("publication_year")
                if yr and int(yr) > 1950:
                    return {"earliest_year": int(yr)}
        except Exception:
            continue
    return {}


def _extract_ordinal(venue: str) -> Optional[str]:
    m = re.search(r'\b(\d+)\s*(st|nd|rd|th)\b', str(venue), re.I)
    return f"{m.group(1)}{m.group(2).lower()}" if m else None


def _build_maturity(ordinal: Optional[str], earliest_year: Optional[int],
                    current_year: int = CONFIG["current_year"]) -> dict:
    result = {
        "ordinal_edition": ordinal,
        "earliest_year":   earliest_year,
        "age_years":       None,
        "maturity_label":  "unknown",
    }
    if earliest_year:
        age = current_year - earliest_year
        result["age_years"] = age
        if age >= 20:   result["maturity_label"] = f"Mature ({age}+ yrs, est. {earliest_year})"
        elif age >= 10: result["maturity_label"] = f"Established ({age} yrs, est. {earliest_year})"
        elif age >= 5:  result["maturity_label"] = f"Growing ({age} yrs, est. {earliest_year})"
        else:           result["maturity_label"] = f"Newer venue ({age} yrs, est. {earliest_year})"
        return result
    if ordinal:
        nm = re.search(r'\d+', ordinal)
        if nm:
            num = int(nm.group())
            age = num - 1
            result["age_years"] = age
            if num >= 20:   result["maturity_label"] = f"Mature series ({ordinal} ed., ~{age}+ yrs)"
            elif num >= 10: result["maturity_label"] = f"Established series ({ordinal} ed., ~{age} yrs)"
            elif num >= 5:  result["maturity_label"] = f"Growing series ({ordinal} ed., ~{age} yrs)"
            else:           result["maturity_label"] = f"Newer series ({ordinal} ed., ~{age} yrs)"
        return result
    result["maturity_label"] = "Maturity unresolvable (no ordinal, no API data)"
    return result


def _get_core_rank(venue: str, core_df: pd.DataFrame):
    if not venue or core_df.empty:
        return None
    m = re.search(r'\(([A-Z0-9\-]+)\)', venue)
    if m:
        res = core_df[core_df['Acronym'].str.upper() == m.group(1).upper()]
        if not res.empty:
            return res.iloc[0]['Rank']
    res = core_df[core_df['Acronym'].str.upper() == venue.strip().upper()]
    if not res.empty:
        return res.iloc[0]['Rank']
    clean = re.sub(r'^\d{4}\s+', '', venue).strip()
    res = core_df[core_df['Conference'].str.contains(re.escape(clean), case=False, na=False)]
    if not res.empty:
        return res.iloc[0]['Rank']
    best_score, best_rank = 0.0, None
    for _, row in core_df.iterrows():
        s = similarity(clean, str(row['Conference']))
        if s > best_score:
            best_score, best_rank = s, row['Rank']
    return best_rank if best_score >= 0.72 else None


# 
# QUALITY NOTES (for logging)
# 

def _journal_note(p: dict) -> str:
    tier  = {"Q1": "Top-tier Q1", "Q2": "Good Q2",
             "Q3": "Mid-tier Q3", "Q4": "Lower-tier Q4"}
    parts = [f"{tier.get(p.get('quartile'), 'Unranked / not in Scimago')} journal"]
    if p.get("scopus_indexed"):                     parts.append("Scopus indexed")
    if p.get("wos_indexed"):                        parts.append("WoS indexed")
    if p.get("impact_factor") is not None:          parts.append(f"IF={p['impact_factor']}")
    if p.get("is_legitimate") is not True:          parts.append(" legitimacy uncertain")
    parts.append(f"Author: {p.get('author_role','unknown').replace('_',' ')}")
    return "; ".join(parts)


def _conf_note(p: dict) -> str:
    parts = []
    rank  = p.get("core_rank")
    if p.get("is_a_star"):
        parts.append("A* conference")
    elif rank and str(rank).upper() not in ("NONE", "NAN", ""):
        parts.append(f"CORE {rank}")
    else:
        parts.append("Not in CORE")
    mat = (p.get("maturity") or {})
    parts.append(f"Maturity: {mat.get('maturity_label','unknown')}")
    proc = p.get("proc_indexed_in") or []
    parts.append(f"Indexed: {', '.join(proc) or 'unknown'}")
    leg = p.get("is_legitimate")
    parts.append(f"Legit: {'confirmed' if leg is True else 'uncertain'}")
    parts.append(f"Author: {p.get('author_role','unknown').replace('_',' ')}")
    return "; ".join(parts)


# 
# ENRICH ONE PUBLICATION  (Step 0 + Step 1)
# 

async def enrich_one(pub: dict, session: aiohttp.ClientSession,
                     issn_map: dict, core_df: pd.DataFrame,
                     candidate_name: str) -> dict:

    #  STEP 0: recover missing metadata by title 
    pub = await resolve_metadata_by_title(pub, session)

    pub_type = pub.get("pub_type")
    issn     = pub.get("issn") or ""
    doi      = pub.get("doi")
    venue    = pub.get("venue") or ""
    pub["publication_year"] = pub.get("year") or pub.get("publication_year")

    #  JOURNAL 
    if pub_type == "journal":
        wos, oa, cr = await asyncio.gather(
            _check_wos(session, issn),
            _fetch_openalex_journal(session, issn),
            _fetch_crossref_doi(session, doi, candidate_name),
        )
        q = issn_map.get(normalize_issn(issn)) if issn else None
        impact_factor = _merge_if(wos.get("impact_factor"), oa.get("avg_citations_2yr"))
        pub.update({
            "quartile":          q,
            "scopus_indexed":    q is not None or oa.get("scopus_proxy", False),
            "wos_indexed":       wos.get("wos_indexed", False),
            "impact_factor":     impact_factor,
            "avg_citations_2yr": oa.get("avg_citations_2yr"),
            "h_index":           oa.get("h_index"),
            "author_role":       cr.get("role", "unknown"),
            "is_legitimate":     bool(q or oa.get("found") or cr.get("found")),
        })
        pub["quality_note"] = _journal_note(pub)

    #  CONFERENCE 
    elif pub_type == "conference":
        cr, age_data = await asyncio.gather(
            _fetch_crossref_doi(session, doi, candidate_name),
            _fetch_openalex_conf_age(session, venue),
        )
        rank     = _get_core_rank(venue, core_df)
        ordinal  = _extract_ordinal(venue)
        maturity = _build_maturity(ordinal, age_data.get("earliest_year"))
        indexing = _detect_conference_indexing(
            venue,
            cr.get("publisher", ""),
            pub.get("_publisher_hint", ""),
        )
        legitimacy = _determine_legitimacy(
            cr.get("found", False),
            indexing["publisher"],
            rank,
            indexing["proc_indexed_in"],
        )
        pub.update({
            "core_rank":           rank,
            "is_a_star":           str(rank or "").strip().upper() == "A*",
            "maturity":            maturity,
            "publisher":           indexing["publisher"],
            "proc_indexed_in":     indexing["proc_indexed_in"],
            "proc_scopus_indexed": indexing["proc_scopus_indexed"],
            "author_role":         cr.get("role", "unknown"),
            "is_legitimate":       legitimacy,
            # nullify journal-only fields
            "quartile":            None,
            "scopus_indexed":      None,
            "wos_indexed":         None,
            "impact_factor":       None,
        })
        pub["quality_note"] = _conf_note(pub)

    return pub


async def enrich_all(pubs: list, issn_map: dict,
                     core_df: pd.DataFrame, candidate_name: str) -> list:
    if not pubs:
        return []
    connector = aiohttp.TCPConnector(
        limit=CONFIG["max_concurrent_requests"], ssl=False
    )
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*[
            enrich_one(dict(p), session, issn_map, core_df, candidate_name)
            for p in pubs
        ])
    return list(results)


# 
# STEP 2  SCORING FUNCTIONS
# 

MAX_SCORES = {
    "publication_quality": 35,
    "authorship_strength": 20,
    "collaboration":       15,
    "conference_maturity": 12,
    "patents_books":       10,
    "supervision":         8,
}


def _get_quartile(pub: dict) -> Optional[str]:
    q = str(pub.get("quartile") or "").strip().upper()
    return q if q in ("Q1", "Q2", "Q3", "Q4") else None


def _norm_role(pub: dict) -> str:
    role = str(pub.get("author_role") or pub.get("authorship_role") or "unknown").lower().strip()
    mapping = {
        "first":                   "first_author",
        "first_author":            "first_author",
        "corresponding":           "corresponding_author",
        "corresponding_author":    "corresponding_author",
        "first_corresponding":     "first_and_corresponding",
        "first_and_corresponding": "first_and_corresponding",
        "co_author":               "co_author",
        "coauthor":                "co_author",
        "co-author":               "co_author",
    }
    return mapping.get(role, "unknown")


def score_publication_quality(pubs: list) -> dict:
    MAX = MAX_SCORES["publication_quality"]
    reasons, warnings, scores = [], [], []

    for pub in [p for p in pubs if p.get("pub_type") == "journal"]:
        title = (pub.get("title") or "Untitled")[:55]
        q   = _get_quartile(pub)
        wos = pub.get("wos_indexed")
        sc  = pub.get("scopus_indexed")
        pts, note = 0.0, ""

        if   q == "Q1" and wos:          pts, note = 8.0, "Q1 + WoS"
        elif q == "Q1" and sc:           pts, note = 7.0, "Q1 + Scopus"
        elif q == "Q1":                  pts, note = 5.5, "Q1 (indexing unverified)"
        elif q == "Q2" and (wos or sc):  pts, note = 5.0, "Q2 + indexed"
        elif q == "Q2":                  pts, note = 4.0, "Q2 (indexing unverified)"
        elif q == "Q3" and (wos or sc):  pts, note = 3.0, "Q3 + indexed"
        elif q == "Q3":                  pts, note = 2.0, "Q3 (indexing unverified)"
        elif q == "Q4":                  pts, note = 1.0, "Q4"
        elif pub.get("is_legitimate"):   pts, note = 1.5, "Unranked but verified"
        else:                            pts, note = 0.5, "Unranked/unverified"

        scores.append(pts)
        reasons.append(f"Journal '{title}': {pts}pts [{note}]")

    for pub in [p for p in pubs if p.get("pub_type") == "conference"]:
        conf  = (pub.get("venue") or "Unknown")[:55]
        rank  = str(pub.get("core_rank") or "").strip().upper()
        proc  = str(pub.get("publisher") or "").upper()
        pts, note = 0.0, ""
        known = ["IEEE", "ACM", "SPRINGER", "ELSEVIER", "WILEY"]

        if   rank == "A*":                             pts, note = 8.0, "A* CORE"
        elif rank == "A":                              pts, note = 7.0, "A CORE"
        elif rank == "B":                              pts, note = 5.0, "B CORE"
        elif rank == "C":                              pts, note = 2.0, "C CORE"
        elif any(k in proc for k in known):            pts, note = 2.5, f"{proc} publisher"
        else:                                          pts, note = 0.5, "Unranked, unknown pub."

        scores.append(pts)
        reasons.append(f"Conf '{conf}': {pts}pts [{note}]")

    raw   = sum(scores)
    final = min(raw, MAX)
    if raw > MAX:
        reasons.append(f"Capped at {MAX} (raw={raw:.1f})")
    reasons.append(f"{len(scores)} papers total "
                   f"({sum(1 for p in pubs if p.get('pub_type')=='journal')} journal, "
                   f"{sum(1 for p in pubs if p.get('pub_type')=='conference')} conf)")

    return {"score": round(final, 1), "max": MAX, "reasons": reasons, "warnings": warnings}


def score_authorship_strength(pubs: list) -> dict:
    MAX = MAX_SCORES["authorship_strength"]
    ROLE_PTS = {
        "first_and_corresponding": 5.0,
        "first_author":            4.0,
        "corresponding_author":    3.0,
        "co_author":               1.0,
        "unknown":                 2.0,
    }
    reasons, warnings = [], []
    role_counts: Dict[str, int] = {}
    total_pts = 0.0

    for pub in pubs:
        role = _norm_role(pub)
        pts  = ROLE_PTS.get(role, 1.0)
        total_pts += pts
        role_counts[role] = role_counts.get(role, 0) + 1
        if role == "unknown":
            warnings.append(f"'{(pub.get('title') or '')[:45]}': authorship unverified")

    # First-author bonus
    n = len(pubs)
    bonus, bonus_reason = 0.0, ""
    if n > 0:
        fa = role_counts.get("first_author", 0) + role_counts.get("first_and_corresponding", 0)
        r  = fa / n
        if   r == 1.0: bonus, bonus_reason = 3.0, f"All {n} papers as first author (+3)"
        elif r >= 0.6: bonus, bonus_reason = 2.0, f"{fa}/{n} first author (+2)"
        elif r >= 0.3: bonus, bonus_reason = 1.0, f"{fa}/{n} first author (+1)"

    raw   = total_pts + bonus
    final = min(raw, MAX)

    for role, count in sorted(role_counts.items()):
        pts   = ROLE_PTS.get(role, 1.0)
        label = role.replace("_", " ").title()
        note  = " [unverified  partial credit]" if role == "unknown" else ""
        reasons.append(f"{count} {label} = {count * pts:.0f}pts{note}")
    if bonus > 0:
        reasons.append(bonus_reason)
    if raw > MAX:
        reasons.append(f"Capped at {MAX} (raw={raw:.1f})")

    return {"score": round(final, 1), "max": MAX, "reasons": reasons, "warnings": warnings}


def score_collaboration(pubs: list, candidate_name: str) -> dict:
    MAX = MAX_SCORES["collaboration"]
    reasons, warnings = [], []

    if not pubs:
        return {"score": 2.0, "max": MAX,
                "reasons": ["No publications  grace 2 pts"],
                "warnings": ["No publication data"]}

    cand_last = (candidate_name or "").lower().split()[-1] if candidate_name else ""
    all_authors: set = set()
    for pub in pubs:
        for author in re.split(r'[;,]', pub.get("authors") or ""):
            author = author.strip()
            if author and not (cand_last and cand_last in author.lower()):
                all_authors.add(author.lower())

    unique_co = len(all_authors)
    totals    = []
    for pub in pubs:
        cnt = len([a for a in re.split(r'[;,]', pub.get("authors") or "") if a.strip()])
        totals.append(cnt)
    avg_authors = sum(totals) / len(totals) if totals else 1

    has_intl = any(
        len([a for a in re.split(r'[;,]', p.get("authors") or "") if a.strip()]) >= 5
        for p in pubs
    )

    if   unique_co >= 10: base, label = 13.0, "High"
    elif unique_co >= 6:  base, label = 10.0, "Good"
    elif unique_co >= 3:  base, label = 7.0,  "Moderate"
    elif unique_co >= 1:  base, label = 4.0,  "Limited"
    else:                 base, label = 2.0,  "Solo/minimal"

    intl_bonus = 2.0 if has_intl else 0.0
    raw   = base + intl_bonus
    final = min(raw, MAX)

    reasons.append(f"{label} collaboration: {unique_co} unique co-authors, "
                   f"avg {avg_authors:.1f} authors/paper")
    if has_intl:
        reasons.append("International collaboration detected (+2 pts)")
    if raw > MAX:
        reasons.append(f"Capped at {MAX} (raw={raw:.1f})")

    return {"score": round(final, 1), "max": MAX, "reasons": reasons, "warnings": warnings}


def score_conference_maturity(pubs: list) -> dict:
    MAX = MAX_SCORES["conference_maturity"]
    reasons, warnings = [], []
    conf_pubs = [p for p in pubs if p.get("pub_type") == "conference"]

    if not conf_pubs:
        return {"score": 0.0, "max": MAX,
                "reasons": ["No conference papers  0 pts"], "warnings": []}

    MATURITY_PTS = {
        "mature": 2.5, "established": 2.0,
        "growing": 1.5, "newer": 1.0, "unknown": 1.5,
    }
    total = 0.0
    for pub in conf_pubs:
        conf = (pub.get("venue") or "Unknown")[:55]
        mat_label = str(pub.get("maturity", {}).get("maturity_label") or "").lower()
        cat = next((k for k in MATURITY_PTS if k in mat_label), "unknown")
        if cat == "unknown":
            warnings.append(f"'{conf}': maturity unknown (partial 1.5 pts)")
        pts = MATURITY_PTS[cat]
        total += pts
        reasons.append(f"'{conf}': {mat_label or 'unknown'}  {pts}pts")

    final = min(total, MAX)
    if total > MAX:
        reasons.append(f"Capped at {MAX} (raw={total:.1f})")
    return {"score": round(final, 1), "max": MAX, "reasons": reasons, "warnings": warnings}


def score_patents_books(patents: list, books: list) -> dict:
    MAX = MAX_SCORES["patents_books"]
    reasons, warnings, total = [], [], 0.0

    for patent in (patents or []):
        num = patent.get("patent_number") or ""
        if num.strip():
            pts = 5.0; reasons.append(f"Granted patent '{num}': {pts}pts")
        else:
            pts = 2.0; reasons.append("Patent (pending/unverified): 2pts")
            warnings.append("Patent number missing  treated as pending")
        total += pts

    for book in (books or []):
        role = str(book.get("authorship_role") or "").lower()
        if "author" in role and "co" not in role:
            pts = 6.0; reasons.append(f"Authored book: {pts}pts")
        elif "edit" in role or "co" in role:
            pts = 4.0; reasons.append("Edited/co-authored book: 4pts")
        elif "chapter" in role:
            pts = 2.0; reasons.append("Book chapter: 2pts")
        else:
            pts = 2.0; reasons.append("Book (role unspecified): 2pts [partial]")
            warnings.append("Book authorship role not specified")
        total += pts

    if not patents and not books:
        reasons.append("No patents or books  0 pts")

    final = min(total, MAX)
    if total > MAX:
        reasons.append(f"Capped at {MAX}")
    return {"score": round(final, 1), "max": MAX, "reasons": reasons, "warnings": warnings}


def score_supervision(supervised_students: list) -> dict:
    MAX = MAX_SCORES["supervision"]
    LEVEL_PTS = {
        "phd": 1.5, "doctorate": 1.5,
        "ms": 1.0, "mphil": 1.0, "msc": 1.0, "postgrad": 1.0,
        "undergrad": 0.5, "bs": 0.5, "bsc": 0.5, "honors": 0.5,
    }
    reasons, warnings, total = [], [], 0.0
    level_counts: Dict[str, int] = {}

    if not supervised_students:
        return {"score": 0.0, "max": MAX,
                "reasons": ["No supervision records  0 pts (may be unrecorded)"],
                "warnings": ["No supervised students in database"]}

    for s in supervised_students:
        lvl = str(s.get("level") or "").lower()
        pts = LEVEL_PTS.get(lvl, 0.5)
        total += pts
        level_counts[lvl] = level_counts.get(lvl, 0) + 1

    for lvl, cnt in sorted(level_counts.items()):
        pts = LEVEL_PTS.get(lvl, 0.5)
        reasons.append(f"{cnt} {lvl.upper()} = {cnt*pts:.1f}pts")

    final = min(total, MAX)
    if total > MAX:
        reasons.append(f"Capped at {MAX}")
    return {"score": round(final, 1), "max": MAX, "reasons": reasons, "warnings": warnings}


def _build_recommendations(components: dict, pubs: list) -> list:
    recs = []
    if components.get("publication_quality", {}).get("score", 0) < 21:
        recs.append("Target Q1/Q2 Scopus-indexed journals to improve publication quality")
    missing_doi = sum(1 for p in pubs if not p.get("doi"))
    if missing_doi:
        recs.append(f"Add valid DOIs for {missing_doi} publication(s)  improves authorship detection")
    if components.get("authorship_strength", {}).get("score", 0) < 12:
        recs.append("Increase first-author publications to demonstrate research leadership")
    conf_pubs = [p for p in pubs if p.get("pub_type") == "conference"]
    if not conf_pubs:
        recs.append("Consider publishing in A/B-ranked CORE conferences")
    elif components.get("conference_maturity", {}).get("score", 0) < 4.8:
        recs.append("Target established/mature conference series (10+ year history)")
    if components.get("supervision_record", {}).get("score", 0) == 0:
        recs.append("Document supervised students (PhD/MS/BS) in the database")
    if components.get("patents_&_books", {}).get("score", 0) == 0:
        recs.append("Document patents or book chapters in the database")
    if components.get("research_collaboration", {}).get("score", 0) < 7.5:
        recs.append("Expand collaboration network  especially international partners")
    return recs

def score_research(candidate_data: dict) -> dict:
    """
    Master scoring function v2.0  82-point base + bonuses.
    
    Flow:
      1. Calculate 5 base components (35+20+15+12+8 = 82 max)
      2. Normalize to 100: (base / 82)  100
      3. Add +5 bonus for books (if present)
      4. Add +5 bonus for patents (if present)
      5. Assign grade based on final score
    """
    name  = candidate_data.get("name", "Unknown")
    pubs  = candidate_data.get("publications", [])
    pats  = candidate_data.get("patents", [])
    books = candidate_data.get("books", [])
    sup   = candidate_data.get("supervised_students", [])
 
    # 
    # STEP 1: Calculate all 5 base components
    # 
    pub_q  = score_publication_quality(pubs)
    auth_s = score_authorship_strength(pubs)
    collab = score_collaboration(pubs, name)
    conf_m = score_conference_maturity(pubs)
    sup_s  = score_supervision(sup)
    
    #  DO NOT INCLUDE: Patents & Books in base calculation
    # pb     = score_patents_books(pats, books)   Not in base anymore
 
    # 
    # STEP 2: Calculate BASE SCORE out of 82 (NOT 100)
    # 
    max_base = 82  # 35 + 20 + 15 + 12 + 8 (supervision)
    base_total = (
        pub_q["score"] +    # 0-35
        auth_s["score"] +   # 0-20
        collab["score"] +   # 0-15
        conf_m["score"] +   # 0-12
        sup_s["score"]      # 0-8
    )
    base_total = min(base_total, max_base)
 
    # 
    # STEP 3: NORMALIZE to 100 scale
    # 
    normalized_score = (base_total / max_base) * 100.0
    normalized_score = round(normalized_score, 1)
 
    # 
    # STEP 4: DETECT and ADD BONUSES
    # 
    has_books = len(books) > 0
    has_patents = len(pats) > 0
    
    bonus_books = 5.0 if has_books else 0.0
    bonus_patents = 5.0 if has_patents else 0.0
    total_bonuses = bonus_books + bonus_patents
 
    # 
    # STEP 5: CALCULATE FINAL SCORE with bonuses
    # 
    final_total = normalized_score + total_bonuses
    final_total = round(final_total, 1)
 
    # 
    # STEP 6: ASSIGN GRADE (updated thresholds for normalized scale)
    # 
    if   final_total >= 100: label = "EXCEPTIONAL"
    elif final_total >= 90:  label = "EXCELLENT"
    elif final_total >= 77:  label = "GOOD"
    elif final_total >= 65:  label = "SATISFACTORY"
    elif final_total >= 49:  label = "DEVELOPING"
    else:                    label = "WEAK"
 
    # 
    # STEP 7: Build full component breakdown (for reference & DB storage)
    # 
    pb = score_patents_books(pats, books)  # Calculate for info only, not in base
 
    all_warnings = []
    for c in [pub_q, auth_s, collab, conf_m, sup_s]:
        all_warnings.extend(c.get("warnings", []))
 
    components = {
        "publication_quality":    pub_q,
        "authorship_strength":    auth_s,
        "research_collaboration": collab,
        "conference_maturity":    conf_m,
        "patents_&_books":        pb,  # For reference/DB, not in calculation
        "supervision_record":     sup_s,
    }
 
    # 
    # STEP 8: Build recommendations
    # 
    recommendations = _build_recommendations(components, pubs)
 
    # 
    # STEP 9: Return complete result dict
    # 
    return {
        "candidate_id": candidate_data.get("candidate_id", ""),
        "name":         name,
        "id":           candidate_data.get("id", 0),
        "components":   components,
        
        #  Scoring breakdown (for transparency) 
        "base_score":         round(base_total, 1),
        "max_base":           max_base,
        "normalized_score":   normalized_score,
        
        #  Bonuses breakdown 
        "bonus_breakdown": {
            "books":         {"present": has_books, "count": len(books), "bonus": bonus_books},
            "patents":       {"present": has_patents, "count": len(pats), "bonus": bonus_patents},
            "total_bonuses": total_bonuses,
        },
        
        #  Final score & grade 
        "base_total":   base_total,      # Kept for backward compatibility
        "final_total":  final_total,     # This is the FINAL score with bonuses
        "label":        label,
        
        #  Metadata 
        "warnings":     all_warnings,
        "recommendations": recommendations,
        "counts": {
            "total_publications":      len(pubs),
            "total_journal_papers":    sum(1 for p in pubs if p.get("pub_type") == "journal"),
            "total_conference_papers": sum(1 for p in pubs if p.get("pub_type") == "conference"),
            "total_books":             len(books),
            "total_patents":           len(pats),
            "total_supervised_students": len(sup),
        },
    }
 
 
def save_research_score(candidate_id: int, result: dict) -> bool:
    """
    Save research score to database with v2.0 values:
      - normalized_score: 0-100 (before bonuses)
      - final_score:      0-110 (after bonuses)
      - grade:            EXCEPTIONAL | EXCELLENT | GOOD | SATISFACTORY | DEVELOPING | WEAK
    """
    # Import here to delay database engine creation until first use
    from db_connect import get_session
    
    session = get_session()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            print(f" Candidate ID {candidate_id} not found")
            return False
 
        scores = result.get("components", {})
        counts = result.get("counts", {})
        bonuses = result.get("bonus_breakdown", {})
 
        #  Extract component scores 
        pub_quality_score = float(scores.get("publication_quality", {}).get("score", 0))
        auth_strength_score = float(scores.get("authorship_strength", {}).get("score", 0))
        research_collab_score = float(scores.get("research_collaboration", {}).get("score", 0))
        conf_maturity_score = float(scores.get("conference_maturity", {}).get("score", 0))
        patents_books_score = float(scores.get("patents_&_books", {}).get("score", 0))
        supervision_score = float(scores.get("supervision_record", {}).get("score", 0))
 
        #  v2.0 SCORES 
        normalized_score = float(result.get("normalized_score", 0))  # 0-100 before bonuses
        final_score = float(result.get("final_total", 0))            # 0-110 after bonuses
        base_score = float(result.get("base_score", 0))              # 0-82 raw base
 
        # Create ResearchScore record
        rs = ResearchScore(
            candidate_id=candidate_id,
            
            #  Component scores (for breakdown) 
            publication_quality_score=pub_quality_score,
            authorship_strength_score=auth_strength_score,
            research_collaboration_score=research_collab_score,
            conference_maturity_score=conf_maturity_score,
            patents_books_score=patents_books_score,
            supervision_record_score=supervision_score,
            
            #  v2.0 FINAL SCORES 
            # raw_score is now the FINAL score with bonuses (0-110)
            raw_score=final_score,
            grade=result.get("label", "UNKNOWN"),
            
            #  Publication counts 
            total_publications=int(counts.get("total_publications", 0)),
            total_journal_papers=int(counts.get("total_journal_papers", 0)),
            total_conference_papers=int(counts.get("total_conference_papers", 0)),
            total_books=int(counts.get("total_books", 0)),
            total_patents=int(counts.get("total_patents", 0)),
            total_supervised_students=int(counts.get("total_supervised_students", 0)),
            
            #  JSON fields 
            reasons=json.dumps({k: v.get("reasons", []) for k, v in scores.items()}),
            warnings=json.dumps(result.get("warnings", [])),
            recommendations=json.dumps(result.get("recommendations", [])),
        )
 
        # Delete old record and insert new
        session.query(ResearchScore).filter_by(candidate_id=candidate_id).delete()
        session.add(rs)
        session.commit()
        
        #  Print summary 
        bonus_str = ""
        if bonuses.get("books", {}).get("present"):
            bonus_str += f" +{bonuses['books']['bonus']}(books)"
        if bonuses.get("patents", {}).get("present"):
            bonus_str += f" +{bonuses['patents']['bonus']}(patents)"
        
        print(f"   Saved research score: {rs.grade} | "
              f"Base: {base_score}/82  Normalized: {normalized_score:.1f}/100{bonus_str}  "
              f"Final: {final_score:.1f}/110 "
              f"(candidate={candidate.name})")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   Error saving research score: {e}")
        return False
    finally:
        session.close()
 
 


# 
# MAIN ASYNC ENTRY POINT
# 

async def score_candidate_research(candidate_id: int) -> dict:
    """
    Full pipeline for one candidate:
      1. Load datasets (cached)
      2. Load candidate + publications from DB
      3. Enrich publications (title recovery  API enrichment)
      4. Score
      5. Save to DB
      6. Return result dict
    """
    try:
        _ensure_datasets_loaded()
        issn_map = _DATASET_CACHE["issn_map"]
        core_df  = _DATASET_CACHE["core_df"]

        #  Load candidate from DB 
        # Import here to delay database engine creation until first use
        from db_connect import get_session
        
        session = get_session()
        cand = session.query(Candidate).filter_by(id=candidate_id).first()
        if not cand:
            session.close()
            print(f"    Candidate {candidate_id} not found in DB")
            return {"error": "Candidate not found"}

        candidate_name = cand.name
        print(f"   Candidate: {candidate_name}")

        #  Build raw publications list 
        pubs_raw = [
            {
                "id":                  p.id,
                "pub_type":            p.pub_type.value if p.pub_type else None,
                "title":               p.title,
                "venue":               p.venue,
                "issn":                p.issn,
                "year":                p.year,
                "authors":             p.authors,
                "authorship_role":     p.authorship_role.value if p.authorship_role else None,
                "doi":                 p.doi,
                "journal_name":        p.journal_name,
                "conference_name":     p.conference_name,
                "conference_maturity": p.conference_maturity,
                "proceedings_publisher": p.proceedings_publisher,
            }
            for p in cand.publications
        ]

        books_raw = [
            {"id": b.id, "title": b.title, "authors": b.authors,
             "publisher": b.publisher, "year": b.year,
             "authorship_role": b.authorship_role}
            for b in cand.books
        ]
        patents_raw = [
            {"id": pt.id, "patent_number": pt.patent_number,
             "title": pt.title, "year": pt.year, "inventors": pt.inventors}
            for pt in cand.patents
        ]
        supervised_raw = [
            {"id": ss.id, "student_name": ss.student_name,
             "level": ss.level.value if ss.level else None,
             "role":  ss.role.value  if ss.role  else None,
             "graduation_year": ss.graduation_year}
            for ss in cand.supervised_students
        ]
        session.close()

        #  Enrich (Step 0 + Step 1) 
        enriched_pubs = pubs_raw
        if pubs_raw:
            print(f"   Enriching {len(pubs_raw)} publications "
                  f"(title recovery + API)...")
            t0 = time.perf_counter()
            enriched_pubs = await enrich_all(
                pubs_raw, issn_map, core_df, candidate_name
            )
            print(f"   Enrichment done ({time.perf_counter() - t0:.1f}s)")
        else:
            print("    No publications found for this candidate")

        #  Score 
        candidate_data = {
            "id":                  cand.id,
            "candidate_id":        cand.candidate_id,
            "name":                candidate_name,
            "publications":        enriched_pubs,
            "books":               books_raw,
            "patents":             patents_raw,
            "supervised_students": supervised_raw,
        }
        result = score_research(candidate_data)
        print(f"   Score: {result['label']} ({result['final_total']}/100)")

        #  Save 
        if not save_research_score(cand.id, result):
            return {"error": "Failed to save to database"}

        #  Return summary 
        return {
            "score": result["final_total"],
            "grade": result["label"],
            "base_total": result["base_total"],
            "components": {
                "publication_quality":    result["components"]["publication_quality"]["score"],
                "authorship_strength":    result["components"]["authorship_strength"]["score"],
                "research_collaboration": result["components"]["research_collaboration"]["score"],
                "conference_maturity":    result["components"]["conference_maturity"]["score"],
                "patents_books":          result["components"]["patents_&_books"]["score"],
                "supervision_record":     result["components"]["supervision_record"]["score"],
            },
            "counts":          result["counts"],
            "warnings":        result["warnings"],
            "recommendations": result["recommendations"],
        }

    except Exception as e:
        import traceback
        print(f"   Research pipeline failed: {e}")
        traceback.print_exc()
        return {"error": str(e)}
    











""" Total Score: 100 points across 6 components

1. Publication Quality (35 pts max) 
For Journals:

Q1 + WoS indexed  8 pts
Q1 + Scopus indexed  7 pts
Q1 (unverified indexing)  5.5 pts 
Q2 + indexed  5 pts
Q2 (unverified)  4 pts 
Q3 + indexed  3 pts
Q3 (unverified)  2 pts 
Q4  1 pt
Unranked but verified  1.5 pts
Unranked/unverified  0.5 pts 

For Conferences:

A* CORE rank  8 pts
A CORE rank  7 pts
B CORE rank  5 pts
C CORE rank  2 pts
Not in CORE but IEEE/ACM/Springer/Elsevier/Wiley  2.5 pts
Unranked, unknown publisher  0.5 pts 

Sum all papers, cap at 35 pts

2. Authorship Strength (20 pts max) 
Per-paper base points:

First + Corresponding  5 pts
First author  4 pts
Corresponding author  3 pts
Co-author  1 pt
Unknown  2 pts  (partial credit, but flagged)

Bonus for leadership:

100% first-author  +3 pts
60% first-author  +2 pts
30% first-author  +1 pt

Sum all, cap at 20 pts

3. Research Collaboration (15 pts max) 
Unique co-authors count:

10 unique co-authors  13 pts (High)
6-9 co-authors  10 pts (Good)
3-5 co-authors  7 pts (Moderate)
1-2 co-authors  4 pts (Limited)
0 co-authors  2 pts (Solo/minimal) 

Bonus:

International collaboration detected (5 authors on any paper)  +2 pts

Sum, cap at 15 pts

4. Conference Maturity (12 pts max) 
Per conference paper:

"Mature" (20+ years / 20+ editions)  2.5 pts
"Established" (10-19 years / 10-19 editions)  2.0 pts
"Growing" (5-9 years / 5-9 editions)  1.5 pts
"Newer" (< 5 years / editions)  1.0 pt
Unknown maturity  1.5 pts (partial credit) 

Sum all conference papers, cap at 12 pts

5. Patents & Books (10 pts max) 
Patents:

Granted patent (has patent_number)  5 pts each
Pending/unverified patent (no patent_number)  2 pts each 

Books:

Authored book  6 pts
Edited/co-authored book  4 pts
Book chapter  2 pts
Book (role unspecified)  2 pts (partial) 

Sum all, cap at 10 pts

6. Supervision Record (8 pts max) 
Per supervised student:

PhD / Doctorate  1.5 pts each
MS / MPhil / MSc / Postgrad  1.0 pt each
Undergrad / BS / BSc / Honors  0.5 pts each

Sum all students, cap at 8 pts

 Final Grade Thresholds:
pythonfinal_total = sum(all 6 components)

if final_total >= 85:  grade = "EXCEPTIONAL"
elif final_total >= 75:  grade = "EXCELLENT"
elif final_total >= 60:  grade = "GOOD"
elif final_total >= 45:  grade = "SATISFACTORY"
elif final_total >= 30:  grade = "DEVELOPING"
else:                    grade = "WEAK"

 What Gets Flagged (Warnings):

Journals:

No Scimago quartile found
Quartile but indexing unverified
Legitimacy not confirmed


Conferences:

Not in CORE ranking + unknown publisher
Maturity unknown (no ordinal, no API data)
Legitimacy uncertain


Authorship:

DOI missing  authorship role = "unknown"
Each "unknown" role gets flagged


Collaboration:

No co-authors detected (solo research)


Patents/Books:

Patent number missing
Book authorship role not specified


Supervision:

No records in database




 Bonus: Recommendations System
After scoring, the system generates improvement recommendations based on weak areas:

publication_quality < 21 pts  "Target Q1/Q2 Scopus journals"
Missing DOIs  "Add DOIs to X publications"
authorship_strength < 12 pts  "Increase first-author publications"
No conference papers  "Publish in A/B CORE conferences"
conference_maturity < 4.8 pts  "Target established venues (10+ yrs)"
supervision = 0  "Document supervised students"
patents_books = 0  "Document patents/book chapters"
collaboration < 7.5 pts  "Expand international partnerships"


 Key Feature: Title Recovery Integration
Before scoring starts, the enrichment pipeline automatically:

Detects missing metadata (doi/issn/venue = None or generic like "International Journal")
Searches Crossref by title  recovers doi, issn, venue, publisher, year
Falls back to OpenAlex if Crossref confidence low
Merges recovered data into publication record
Then runs normal enrichment with the recovered ISSNs/DOIs

This means even if you only have titles, the system will:

Find the real journal name
Get the ISSN  match to Scimago quartile
Get the DOI  detect authorship role via CrossRef
Auto-correct pub_type (journal vs conference)"""
