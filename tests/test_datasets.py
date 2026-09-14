from pathlib import Path

from scripts.validate_datasets import validate


def test_all_datasets_follow_contract():
    count, errors = validate(Path("evals/datasets"))
    assert count >= 28
    assert errors == []
