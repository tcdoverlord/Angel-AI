from angel_platform.webui.server import (
    asks_for_sys_chat,
    asks_for_live_unintegrated_data,
    sys_chat_guidance,
    live_data_guidance,
)

def test_sys_chat_is_deterministic_and_not_claimed_executed():
    assert asks_for_sys_chat("run a PowerShell command")
    text = sys_chat_guidance("run a PowerShell command")
    assert "not executed" in text.lower()
    assert "no command was run" in text.lower()

def test_live_data_does_not_fabricate():
    assert asks_for_live_unintegrated_data("what is the weather today?")
    text = live_data_guidance("what is the weather today?")
    assert "will not invent" in text.lower()
    assert "no live lookup was performed" in text.lower()


def test_sys_chat_discussion_stays_normal_chat():
    assert not asks_for_sys_chat(
        "Explain why separating Normal Chat from Sys Chat makes Angel safer."
    )


def test_sys_chat_action_still_routes():
    assert asks_for_sys_chat("Switch to Sys Chat and check whether Ollama is running.")


def test_approval_executes_only_pending_safe_diagnostic():
    from angel_platform.webui.server import sys_chat_guidance, execute_pending_approved
    text = sys_chat_guidance("check Python version")
    assert "NOT EXECUTED" in text
    result = execute_pending_approved()
    assert "VERIFIED EXECUTION RESULT" in result
    assert "Command: python --version" in result
    assert "Return code:" in result


def test_approval_without_pending_command_is_honest():
    from angel_platform.webui.server import execute_pending_approved
    assert "No pending command" in execute_pending_approved()
