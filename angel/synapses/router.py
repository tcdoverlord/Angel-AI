from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..tools import ToolRequest


@dataclass(frozen=True)
class SynapseMatch:
    neuron: str
    request: ToolRequest


class SynapseRouter:
    """Small allowlisted router connecting user intent to specialized neurons."""

    def __init__(self, neurons: Iterable[object]) -> None:
        self._neurons = tuple(neurons)

    def route(self, text: str) -> SynapseMatch | None:
        for neuron in self._neurons:
            can_handle = getattr(neuron, "can_handle", None)
            activate = getattr(neuron, "activate", None)
            name = getattr(neuron, "name", neuron.__class__.__name__)
            if not callable(can_handle) or not callable(activate):
                continue
            if can_handle(text):
                request = activate()
                if not isinstance(request, ToolRequest):
                    raise TypeError(
                        f"Genesis neuron {name!r} returned an invalid tool request"
                    )
                return SynapseMatch(str(name), request)
        return None
