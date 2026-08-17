
from pathlib import Path


def test_core_skills_exist():
    skills = Path("skills")

    required = [
        "truth_verification.md",
        "git_management.md",
        "backup_workflow.md",
        "development_workflow.md",
        "intent_routing.md",
        "tool_safety.md",
        "artifact_management.md",
        "memory_integrity.md",
        "constitutional_awareness.md",
        "reporting_standards.md",
    ]

    for skill in required:
        assert (skills / skill).exists()
