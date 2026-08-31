"""
TC2 — Submit Guard Test
Verifies that the /submit route rejects incomplete filled_fields
and only saves when all 16 fields are populated.
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
from app import app


def test_submit_rejects_incomplete_fields():
    """TC2a — /submit should return status=incomplete when fields have None values."""
    # Reset filled_fields to all None (simulates server restart mid-conversation)
    for key in app_module.filled_fields:
        app_module.filled_fields[key] = None

    client = app.test_client()
    response = client.post("/submit", content_type="application/json")
    data = json.loads(response.data)

    assert data["status"] == "incomplete", "FAIL: Expected status=incomplete for empty fields"
    assert "missing_fields" in data, "FAIL: missing_fields key not returned"
    assert len(data["missing_fields"]) == 16, f"FAIL: Expected 16 missing fields, got {len(data['missing_fields'])}"
    print("PASS — /submit correctly rejected incomplete fields")


def test_submit_returns_missing_field_names():
    """TC2b — /submit should return the exact names of missing fields."""
    for key in app_module.filled_fields:
        app_module.filled_fields[key] = None

    # Partially fill a few fields
    app_module.filled_fields["age_hair_loss_began"] = 25
    app_module.filled_fields["duration"] = "6-12 months"

    client = app.test_client()
    response = client.post("/submit", content_type="application/json")
    data = json.loads(response.data)

    assert data["status"] == "incomplete", "FAIL: Expected incomplete status"
    assert "age_hair_loss_began" not in data["missing_fields"], "FAIL: Filled field listed as missing"
    assert "duration" not in data["missing_fields"], "FAIL: Filled field listed as missing"
    assert len(data["missing_fields"]) == 14, f"FAIL: Expected 14 missing, got {len(data['missing_fields'])}"
    print("PASS — /submit correctly identified missing field names")


def test_submit_saves_when_all_fields_filled():
    """TC2c — /submit should save the file when all 16 fields are populated."""
    # Fill all fields with dummy data
    app_module.filled_fields.update({
        "age_hair_loss_began": 25, "duration": "6-12 months",
        "family_history": ["None"], "pattern": ["Thinning at crown"],
        "diagnosed_conditions": ["None"], "menstrual_cycle": "Not applicable",
        "pregnancy_related": "Not applicable", "adult_acne_oily_skin": "no",
        "excess_body_facial_hair": "no", "past_6_months": ["High stress"],
        "habits": {"smoking": "no"}, "products": ["None"],
        "procedures": ["None"], "past_treatment_side_effects": "no",
        "sample_type": "saliva", "consent": "yes"
    })

    client = app.test_client()
    response = client.post("/submit", content_type="application/json")
    data = json.loads(response.data)

    assert data["status"] == "saved", f"FAIL: Expected status=saved, got {data['status']}"
    assert os.path.exists("intake_result.json"), "FAIL: intake_result.json was not created"
    print("PASS — /submit saved file when all fields complete")

    # Cleanup test file
    if os.path.exists("intake_result.json"):
        os.remove("intake_result.json")


if __name__ == "__main__":
    print("\n── TC2: Submit Guard Tests ──")
    test_submit_rejects_incomplete_fields()
    test_submit_returns_missing_field_names()
    test_submit_saves_when_all_fields_filled()
    print("── All TC2 tests passed ──\n")
