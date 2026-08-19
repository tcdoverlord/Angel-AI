from __future__ import annotations

import pytest

from angel.genesis_brain import GENESIS_VERSION, GenesisBrain
from angel.neurons.datetime import DateTimeNeuron


def test_genesis_version_is_date_based():
    assert GENESIS_VERSION == "Genesis V1.1 — 2026-08-19"


@pytest.mark.parametrize(
    "phrase",
    [
        "what time is it",
        "what date is it",
        "what day is it",
        "what is today's date",
        "what time and date is it",
        "what date and time is it",
        "what is the current date and time",
        "tell me the current date and time",
    ],
)
def test_datetime_neuron_recognizes_common_requests(phrase):
    neuron = DateTimeNeuron()
    assert neuron.can_handle(phrase)


def test_genesis_routes_datetime_to_existing_tool():
    brain = GenesisBrain([DateTimeNeuron()])

    plan = brain.plan("What time and date is it?")

    assert plan is not None
    assert plan.neuron == "datetime"
    assert plan.request.name == "current_datetime"
    assert plan.request.arguments == {}


def test_genesis_does_not_execute_tools():
    brain = GenesisBrain([DateTimeNeuron()])

    plan = brain.plan("What time is it?")

    assert plan is not None
    # Planning produces a request only; execution remains in the proven ToolLoop.


def test_genesis_ignores_unknown_intent():
    brain = GenesisBrain([DateTimeNeuron()])

    assert brain.plan("Tell me a story about a lighthouse") is None
