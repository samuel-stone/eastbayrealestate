import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prospect_model.score_prospects import score_feature_row, tier_for_score


def test_parcel_only_score_is_insufficient_evidence():
    score, reasons = score_feature_row({"verified_parcel": 1, "fresh_observation": 1})

    assert score == 15
    assert reasons == ["verified parcel", "current public-source observation"]
    assert tier_for_score(score) == "insufficient_evidence"


def test_public_activity_score_is_prioritized_for_review():
    score, reasons = score_feature_row({
        "verified_parcel": 1,
        "fresh_observation": 1,
        "building_permit_count_24m": 2,
        "planning_application_count_24m": 1,
        "major_project_type": "ADU",
    })

    assert score == 85
    assert "public project: ADU" in reasons
    assert tier_for_score(score) == "high_review_priority"
