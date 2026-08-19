from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .synapses import SynapseMatch, SynapseRouter


GENESIS_VERSION = "Genesis V1.1 — 2026-08-19"


@dataclass(frozen=True)
class GenesisPlan:
    """A planned, allowlisted capability action. No tool is executed here."""

    match: SynapseMatch

    @property
    def neuron(self) -> str:
        return self.match.neuron

    @property
    def request(self):
        return self.match.request


class GenesisBrain:
    """Modular intent coordinator.

    This is intentionally not a replacement for AngelBrain yet.
    It only routes supported intent through small neurons and existing tools.
    """

    version = GENESIS_VERSION

    def __init__(self, neurons: Iterable[object]) -> None:
        self.router = SynapseRouter(neurons)

    def plan(self, user_text: str) -> GenesisPlan | None:
        clean = " ".join(user_text.split()).strip()
        if not clean:
            return None
        match = self.router.route(clean)
        return GenesisPlan(match) if match is not None else None
