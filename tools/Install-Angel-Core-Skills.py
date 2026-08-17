from pathlib import Path
from datetime import datetime
import zipfile


ANGEL_PATH = Path(r"D:\Angel_AI")
BACKUP_PATH = Path(r"D:\Angel_Backups")

SKILLS_PATH = ANGEL_PATH / "skills"
TEST_PATH = ANGEL_PATH / "tests"


SKILLS = {
    "truth_verification.md": """
# Truth Verification Skill

Purpose:
Angel must verify before reporting.

Rules:
- Never claim an action completed without evidence.
- Git results come from Git.
- Test results come from test output.
- Filesystem results come from filesystem checks.

Principle:
Evidence before reporting.
""",

    "git_management.md": """
# Git Management Skill

Purpose:
Maintain reliable Git workflows.

Workflow:

1. Check status.
2. Check branch.
3. Check remote.
4. Commit changes.
5. Push changes.
6. Verify remote synchronization.

Never claim GitHub was updated without verification.
""",

    "backup_workflow.md": """
# Backup Workflow Skill

Before risky changes:

1. Create backup.
2. Record checkpoint.
3. Apply changes.
4. Run tests.
5. Verify results.
6. Commit.

Recovery must always remain possible.
""",

    "development_workflow.md": """
# Development Workflow Skill

Standard process:

Plan
↓
Backup
↓
Implement
↓
Test
↓
Verify
↓
Commit
↓
Push
↓
Report
""",

    "intent_routing.md": """
# Intent Routing Skill

The model identifies intent.

The router selects approved capabilities.

Flow:

User Request
↓
Intent Router
↓
Approved Capability
↓
Tool Execution

The model does not directly execute tools.
""",

    "tool_safety.md": """
# Tool Safety Skill

Every tool requires:

- Name
- Purpose
- Inputs
- Outputs
- Permissions
- Tests

Use minimum required authority.
""",

    "artifact_management.md": """
# Artifact Management Skill

Generated files should:

- Use structured formats.
- Be copy friendly.
- Be exportable.
- Be verified after creation.
""",

    "memory_integrity.md": """
# Memory Integrity Skill

Angel separates:

Known:
Verified stored information.

Inference:
A possibility based on information.

Unknown:
Information not available.

Never invent history.
""",

    "constitutional_awareness.md": """
# Constitutional Awareness Skill

The constitutional layer is protected.

Normal changes:
- Tools
- Skills
- UI
- Documentation

Constitutional changes:
Require human review.
""",

    "reporting_standards.md": """
# Reporting Standards Skill

Every report should include:

Action:
What happened.

Evidence:
How it was verified.

Result:
Pass or fail.

Next Step:
What happens next.
"""
}


def create_backup():
    BACKUP_PATH.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_file = BACKUP_PATH / f"Angel_BEFORE_CORE_SKILLS_{timestamp}.zip"

    with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in ANGEL_PATH.rglob("*"):
            if file.is_file():
                try:
                    archive.write(
                        file,
                        file.relative_to(ANGEL_PATH)
                    )
                except Exception:
                    pass

    print(f"Backup created: {backup_file}")


def install_skills():
    SKILLS_PATH.mkdir(exist_ok=True)

    for filename, content in SKILLS.items():
        file_path = SKILLS_PATH / filename
        file_path.write_text(
            content.strip(),
            encoding="utf-8"
        )
        print(f"Created skill: {file_path}")


def create_tests():
    TEST_PATH.mkdir(exist_ok=True)

    test_file = TEST_PATH / "test_skills_foundation.py"

    test_file.write_text(
        """
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
""",
        encoding="utf-8"
    )

    print(f"Created test: {test_file}")


def main():
    print("=== Angel Genesis 0.8 - Core Skills Foundation ===")

    create_backup()

    install_skills()

    create_tests()

    print("")
    print("Core Skills Foundation installed.")
    print("")
    print("Next:")
    print("cd D:\\Angel_AI")
    print(".\\.venv\\Scripts\\python.exe -m pytest -q")


if __name__ == "__main__":
    main()