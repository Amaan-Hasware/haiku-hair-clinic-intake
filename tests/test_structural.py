"""
TC1 — Structural Integrity Test
Verifies that every Gemini response contains a valid [FIELDS]...[/FIELDS] block
with parseable JSON covering all 16 required keys.
"""

import json
import sys
import os

# Allow importing from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import client, MODEL, SYSTEM_PROMPT
from google.genai import types

REQUIRED_KEYS = [
    "age_hair_loss_began", "duration", "family_history", "pattern",
    "diagnosed_conditions", "menstrual_cycle", "pregnancy_related",
    "adult_acne_oily_skin", "excess_body_facial_hair", "past_6_months",
    "habits", "products", "procedures", "past_treatment_side_effects",
    "sample_type", "consent"
]

def get_gemini_reply(user_message):
    """Send a single message to Gemini and return the raw reply text."""
    history = [types.Content(role="user", parts=[types.Part(text=user_message)])]
    response = client.models.generate_content(
        model=MODEL,
        contents=history,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    return response.text


def test_fields_block_present():
    """TC1a — [FIELDS] block must be present in every Gemini reply."""
    reply = get_gemini_reply("Hi, I'm here for my intake.")
    assert "[FIELDS]" in reply, "FAIL: [FIELDS] block missing from Gemini response"
    assert "[/FIELDS]" in reply, "FAIL: [/FIELDS] closing tag missing from Gemini response"
    print("PASS — [FIELDS] block present")


def test_fields_block_is_valid_json():
    """TC1b — Content between [FIELDS] tags must be valid JSON."""
    reply = get_gemini_reply("I'm 25 years old and my hair started falling 6 months ago.")
    assert "[FIELDS]" in reply, "FAIL: [FIELDS] block missing"

    raw_json = reply.split("[FIELDS]")[1].replace("[/FIELDS]", "").strip()
    try:
        parsed = json.loads(raw_json)
        print("PASS — [FIELDS] content is valid JSON")
    except json.JSONDecodeError as e:
        assert False, f"FAIL: [FIELDS] content is not valid JSON — {e}"


def test_fields_block_has_all_16_keys():
    """TC1c — The JSON in [FIELDS] must contain all 16 required keys."""
    reply = get_gemini_reply("I'm 25 years old and my hair started falling 6 months ago.")
    raw_json = reply.split("[FIELDS]")[1].replace("[/FIELDS]", "").strip()
    parsed = json.loads(raw_json)

    missing_keys = [k for k in REQUIRED_KEYS if k not in parsed]
    assert not missing_keys, f"FAIL: Missing keys in [FIELDS] JSON — {missing_keys}"
    print("PASS — All 16 keys present in [FIELDS] JSON")


if __name__ == "__main__":
    print("\n── TC1: Structural Integrity Tests ──")
    test_fields_block_present()
    test_fields_block_is_valid_json()
    test_fields_block_has_all_16_keys()
    print("── All TC1 tests passed ──\n")
