from __future__ import annotations

import argparse
import json
import logging
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .brain import AngelBrain
from .context import ContextBuilder
from .database import Database
from .logging_setup import configure_logging
from .memory import MemoryService
from .ollama_client import OllamaClient
from .paths import app_data_dir, database_path
from .recommendations import QUICK_ACTIONS, RecommendationService
from .search import SearchService
from .settings import SettingsService
from .speech import WindowsSpeechService
from .tools import create_tool_registry
from .ui import AngelUI


@dataclass
class AppServices:
    data_dir: Path
    logger: logging.Logger
    database: Database
    settings: SettingsService
    memory: MemoryService
    search: SearchService
    ollama: OllamaClient
    recommendations: RecommendationService
    context: ContextBuilder
    brain: AngelBrain
    speech: WindowsSpeechService


def create_services(data_dir: str | Path | None = None) -> AppServices:
    resolved_data_dir = app_data_dir(data_dir)
    logger = configure_logging(resolved_data_dir)
    database = Database(database_path(resolved_data_dir), logger.getChild("database"))
    settings = SettingsService(database)
    memory = MemoryService(database, settings)
    search = SearchService(logger=logger.getChild("search"))
    ollama = OllamaClient(logger.getChild("ollama"))
    recommendations = RecommendationService(database, settings)
    context = ContextBuilder(database, settings, memory)
    tools = create_tool_registry(
        database, settings, memory, search, logger.getChild("tools")
    )
    brain = AngelBrain(
        database,
        settings,
        context,
        tools,
        ollama,
        recommendations,
        logger.getChild("brain"),
    )
    speech = WindowsSpeechService(logger.getChild("speech"))
    return AppServices(
        resolved_data_dir,
        logger,
        database,
        settings,
        memory,
        search,
        ollama,
        recommendations,
        context,
        brain,
        speech,
    )


def acceptance_checks(
    services: AppServices, live_search: bool = False, live_model: bool = False
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "database": False,
        "conversation_persistence": False,
        "settings": False,
        "memory": False,
        "quick_actions": False,
        "ollama_detected": False,
        "models": [],
        "live_model": "NOT TESTED",
        "web_search": "NOT TESTED",
        "sources": 0,
        "ui_opened": False,
        "windows_speech_available": False,
        "windows_voices": [],
    }
    conversation_id = services.database.create_conversation("Acceptance Check")
    services.database.add_message(conversation_id, "user", "Persistence check")
    reopened = Database(services.database.path, services.logger.getChild("acceptance.database"))
    report["database"] = reopened.conversation_exists(conversation_id)
    report["conversation_persistence"] = (
        reopened.get_messages(conversation_id)[-1]["content"] == "Persistence check"
    )
    services.settings.update(display_name="Angel Acceptance", response_style="Concise")
    saved_settings = SettingsService(reopened).get()
    report["settings"] = (
        saved_settings.display_name == "Angel Acceptance"
        and saved_settings.response_style == "Concise"
    )
    memory = services.memory.add("I prefer purple acceptance checks.", "preference")
    found = services.memory.search("purple")
    deleted = services.memory.delete(int(memory["id"]))
    report["memory"] = bool(found and deleted)
    report["quick_actions"] = all(
        mode in services.recommendations.build_prompt(mode) for mode in QUICK_ACTIONS
    )
    online, models = services.ollama.check(saved_settings.ollama_url)
    report["ollama_detected"] = online
    report["models"] = models
    voices = services.speech.list_voices()
    report["windows_speech_available"] = bool(voices)
    report["windows_voices"] = voices
    if live_model and online and models:
        try:
            response = services.ollama.chat(
                saved_settings.ollama_url,
                models[0],
                [
                    {"role": "system", "content": "Reply with exactly ANGEL_OK."},
                    {"role": "user", "content": "Runtime check."},
                ],
            )
            report["live_model"] = models[0] if response else "FAIL"
        except Exception as exc:
            report["live_model"] = f"FAIL: {type(exc).__name__}"
    if live_search:
        try:
            results = services.search.search("Angel local personal AI current date", limit=3)
            report["web_search"] = "PASS"
            report["sources"] = len(results)
        except Exception as exc:
            report["web_search"] = f"FAIL: {type(exc).__name__}"
    return report


def _write_report(path: str | None, report: dict[str, Any]) -> None:
    if path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Angel local personal AI")
    parser.add_argument("--data-dir", help="Override Angel's local data directory")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--acceptance-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--live-search", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--live-model", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--smoke-ms", type=int, default=1200, help=argparse.SUPPRESS)
    parser.add_argument("--diagnostics-output", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    services = create_services(args.data_dir)
    services.logger.info("Angel startup")
    report: dict[str, Any] = {}
    if args.acceptance_test:
        report = acceptance_checks(services, args.live_search, args.live_model)
    try:
        root = tk.Tk()
        ui = AngelUI(
            root,
            services.database,
            services.settings,
            services.memory,
            services.brain,
            services.ollama,
            services.logger.getChild("ui"),
            services.speech,
        )
    except Exception as exc:
        services.logger.exception("Angel UI startup failed")
        if report is not None:
            report["ui_error"] = f"{type(exc).__name__}: {exc}"
            _write_report(args.diagnostics_output, report)
        return 1

    if args.smoke_test or args.acceptance_test:
        report["ui_opened"] = True

        def finish_smoke() -> None:
            _write_report(args.diagnostics_output, report)
            ui.close()

        root.after(max(250, args.smoke_ms), finish_smoke)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        ui.close()
    finally:
        services.logger.info("Angel shutdown complete")
        _write_report(args.diagnostics_output, report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
