from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from nodes.llm_extractor import normalize_school_education_fields


def test_normalize_school_education_fields_moves_institution_to_board_for_ssc_hssc():
    education = [
        {
            "degree": "HSSC",
            "institution": "B.I.S.E Bannu",
            "board": None,
        },
        {
            "degree": "SSC",
            "institution": "Federal Board",
            "board": None,
        },
        {
            "degree": "BS",
            "institution": "NUST",
            "board": None,
        },
    ]

    out = normalize_school_education_fields(education)

    assert out[0]["board"] == "B.I.S.E Bannu"
    assert out[0]["institution"] is None
    assert out[1]["board"] == "Federal Board"
    assert out[1]["institution"] is None
    assert out[2]["institution"] == "NUST"
    assert out[2]["board"] is None
