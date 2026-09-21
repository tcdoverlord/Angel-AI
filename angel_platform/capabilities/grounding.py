
"""Small, dependency-free structures for source-grounded responses."""
from dataclasses import dataclass, asdict
from typing import Iterable

@dataclass(frozen=True)
class Evidence:
    title: str
    url: str
    snippet: str = ""

@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    evidence: tuple[Evidence, ...] = ()
    uncertainty: str = ""

    def to_dict(self):
        return asdict(self)

def make_grounded_answer(answer: str, evidence: Iterable[Evidence] = (), uncertainty: str = ""):
    return GroundedAnswer(answer=answer, evidence=tuple(evidence), uncertainty=uncertainty)
