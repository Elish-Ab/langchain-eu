import importlib.util
from pathlib import Path

import pytest


_MODULE_PATH = Path(__file__).with_name("experience.py")
_SPEC = importlib.util.spec_from_file_location("experience", _MODULE_PATH)
experience = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(experience)

split_tags_and_experience = experience.split_tags_and_experience
derive_experience_level = experience.derive_experience_level


def test_split_tags_removes_experience_variants():
    cleaned, level = split_tags_and_experience([
        "Python",
        " 1 - 3 Years ",
        "3–5 yrs",
        "Remote",
    ])

    assert cleaned == ["Python", "Remote"]
    # most senior level should win
    assert level == "mid-level"


def test_derive_experience_level_handles_plus_variation():
    level = derive_experience_level(["5 + YEARS", "python", "iso 27001-2013"])

    assert level == "senior"


def test_split_tags_returns_empty_for_no_matches():
    cleaned, level = split_tags_and_experience(["Python", "Django"])

    assert cleaned == ["Python", "Django"]
    assert level == ""


def test_split_tags_handles_trailing_experience_wording():
    cleaned, level = split_tags_and_experience([
        "3-5 years of experience",
        "Django",
    ])

    assert cleaned == ["Django"]
    assert level == "mid-level"
