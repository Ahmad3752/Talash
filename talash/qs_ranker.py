import pandas as pd
import difflib
import re
from dataclasses import dataclass
from typing import Optional

QS_CSV_PATH = r'C:\Projects\Talash\QS World University Rankings 2025 (Top global universities).csv'

@dataclass
class InstitutionScore:
    score: int        # 4–20
    tier: int         # 1, 2, or 3
    method: str       # "qs_matrix" or "llm_fallback"
    reason: str


class InstitutionQualityScorer:
    """
    Scores a university on a 4–20 scale using:
      Step 1 → QS Rankings CSV (fuzzy match)
      Step 2 → LLM fallback (if not found in CSV)
    """

    TIER1_SCORE = 18   # rank ≤ 500
    TIER2_SCORE = 12   # rank 501–1000
    TIER3_SCORE = 6    # rank 1001+

    def __init__(self, llm_caller=None):
        """
        llm_caller: a callable that takes (system_prompt: str, user_prompt: str) -> str
                    Pass your own LLM function here.
        """
        self._qs_df: Optional[pd.DataFrame] = None
        self.llm_caller = llm_caller
        self._load_qs_data()

    # ──────────────────────────────────────────────
    # Data Loading
    # ──────────────────────────────────────────────

    def _load_qs_data(self):
        try:
            df = pd.read_csv(QS_CSV_PATH, encoding='latin1')
            df['_normalized'] = df['Institution_Name'].apply(self._normalize)
            self._qs_df = df
        except Exception as e:
            print(f"[InstitutionQualityScorer] Warning: Could not load QS CSV: {e}")
            self._qs_df = None

    # ──────────────────────────────────────────────
    # Public Method
    # ──────────────────────────────────────────────

    def score(self, institution_name: str) -> int:
        """Main entry point. Returns score as int (4–20)."""
        result = self._score_full(institution_name)
        return result.score

    def score_full(self, institution_name: str) -> InstitutionScore:
        """Returns full InstitutionScore dataclass."""
        return self._score_full(institution_name)

    # ──────────────────────────────────────────────
    # Step 1: QS Matrix
    # ──────────────────────────────────────────────

    def _score_full(self, institution_name: str) -> InstitutionScore:
        try:
            result = self._try_qs_matrix(institution_name)
            if result is not None:
                return result
        except Exception as e:
            print(f"[QS Matrix] Error: {e}")

        # Step 2: LLM fallback
        try:
            return self._try_llm_fallback(institution_name)
        except Exception as e:
            print(f"[LLM Fallback] Error: {e}")
            return InstitutionScore(
                score=6, tier=3,
                method="default_fallback",
                reason="Both QS matrix and LLM failed — defaulted to Tier 3"
            )

    def _try_qs_matrix(self, institution_name: str) -> Optional[InstitutionScore]:
        if self._qs_df is None:
            return None

        normalized_input = self._normalize(institution_name)
        best_match_row = self._fuzzy_match(normalized_input)

        if best_match_row is None:
            return None

        rank = self._parse_rank(str(best_match_row.get('RANK_2025', '')))
        matched_name = best_match_row.get('Institution_Name', institution_name)

        if rank is None:
            return None

        score, tier = self._rank_to_score(rank)
        return InstitutionScore(
            score=score,
            tier=tier,
            method="qs_matrix",
            reason=f"QS 2025 rank {rank} → Tier {tier} | Matched: {matched_name}"
        )

    def _fuzzy_match(self, normalized_input: str) -> Optional[dict]:
        if self._qs_df is None:
            return None

        input_tokens = normalized_input[:30]

        # Match 1: QS name contains input substring
        mask1 = self._qs_df['_normalized'].str.contains(input_tokens[:20], na=False)
        # Match 2: input contains QS name substring
        mask2 = self._qs_df['_normalized'].apply(
            lambda qs: qs[:20] in normalized_input if isinstance(qs, str) else False
        )

        candidates = self._qs_df[mask1 | mask2]

        if not candidates.empty:
            return candidates.iloc[0].to_dict()

        # Match 3: difflib ratio ≥ 0.75
        qs_names = self._qs_df['_normalized'].tolist()
        matches = difflib.get_close_matches(normalized_input, qs_names, n=1, cutoff=0.75)
        if matches:
            row = self._qs_df[self._qs_df['_normalized'] == matches[0]]
            if not row.empty:
                return row.iloc[0].to_dict()

        return None

    def _parse_rank(self, rank_str: str) -> Optional[int]:
        """Parses rank strings like '=401', '1001-1200', '1501+' → int"""
        rank_str = rank_str.strip().replace('=', '').replace('+', '')
        # Range like "1001-1200" → take upper bound
        if '-' in rank_str:
            try:
                return int(rank_str.split('-')[-1])
            except:
                return None
        try:
            return int(rank_str)
        except:
            return None

    def _rank_to_score(self, rank: int) -> tuple[int, int]:
        if rank <= 500:
            return self.TIER1_SCORE, 1
        elif rank <= 1000:
            return self.TIER2_SCORE, 2
        else:
            return self.TIER3_SCORE, 3

    # ──────────────────────────────────────────────
    # Step 2: LLM Fallback
    # ──────────────────────────────────────────────

    def _try_llm_fallback(self, institution_name: str) -> InstitutionScore:
        if self.llm_caller is None:
            return InstitutionScore(
                score=6, tier=3,
                method="llm_unavailable",
                reason="No LLM caller provided — defaulted to Tier 3"
            )

        system_prompt = (
            "You are an academic quality evaluator. You know universities worldwide "
            "especially in Pakistan, Asia, and the Middle East. "
            "Always respond ONLY with valid JSON, no extra text, no markdown."
        )

        user_prompt = f"""Score this university for academic quality/prestige on a scale of 4-20.
University: '{institution_name}'

Scoring tiers:
  Tier 1 (16-20): World-class, internationally recognized, strong global research 
                   reputation (e.g., MIT, Oxford, NUST Islamabad, LUMS)
  Tier 2 (9-15):  Nationally recognized, government-chartered, HEC-recognized in 
                   Pakistan, decent research output (e.g., COMSATS, IIU Islamabad, 
                   UET Lahore)
  Tier 3 (4-8):   Regional or lesser-known, HEC-recognized but minimal research 
                   presence (e.g., Qurtuba University, small private universities)

Consider: HEC recognition, research output, global presence, age/reputation.

Respond ONLY with this exact JSON (no markdown, no extra text):
{{"score": <int 4-20>, "tier": <1 or 2 or 3>, "reason": "<one sentence>", "method": "llm_fallback"}}"""

        raw = self.llm_caller(system_prompt, user_prompt)
        return self._parse_llm_response(raw)

    def _parse_llm_response(self, raw: str) -> InstitutionScore:
        import json
        try:
            # Strip markdown fences if present
            clean = re.sub(r'```(?:json)?|```', '', raw).strip()
            data = json.loads(clean)
            return InstitutionScore(
                score=int(data['score']),
                tier=int(data['tier']),
                method="llm_fallback",
                reason=data.get('reason', 'LLM scored')
            )
        except Exception:
            return InstitutionScore(
                score=6, tier=3,
                method="llm_parse_error",
                reason="LLM response could not be parsed — defaulted to Tier 3"
            )

    # ──────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────

    @staticmethod
    def _normalize(name: str) -> str:
        if not isinstance(name, str):
            return ''
        name = name.lower().strip()
        name = re.sub(r'[^\w\s]', '', name)   # remove punctuation
        name = re.sub(r'\s+', ' ', name)       # collapse whitespace
        return name