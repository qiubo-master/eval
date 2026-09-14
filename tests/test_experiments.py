import pytest

from llm_eval_system.experiments import Experiment


def test_assignment_is_stable():
    experiment = Experiment("support-v1", 50, "secret")
    assert experiment.assign("user-42") == experiment.assign("user-42")


def test_extreme_allocations():
    assert Experiment("x", 0, "s").assign("u") == "A"
    assert Experiment("x", 100, "s").assign("u") == "B"


def test_invalid_allocation_is_rejected():
    with pytest.raises(ValueError):
        Experiment("x", 101, "s")
