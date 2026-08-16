from __future__ import annotations

import logging
import os
import queue
import threading
import tkinter as tk
import webbrowser
from concurrent.futures import Future
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Callable

from .attachments import MAX_ATTACHMENTS, format_size, prepare_attachments
from .brain import AngelBrain, BrainResponse
from .database import Database
from .memory import MEMORY_CATEGORIES, MemoryDisabledError, MemoryService
from .ollama_client import OllamaClient
from .recommendations import QUICK_ACTIONS
from .search import is_safe_public_url
from .settings import AngelSettings, SettingsService
from .speech import WindowsSpeechService


COLORS = {
    "black": "#09080D",
    "charcoal": "#15121D",
    "panel": "#1E1928",
    "panel_alt": "#262034",
    "violet": "#7447E8",
    "violet_hover": "#895EF4",
    "electric": "#A67CFF",
    "gold": "#D5AD62",
    "white": "#F5F1FF",
    "muted": "#AFA5C2",
    "good": "#79D6A3",
    "bad": "#E58B98",
}


class BackgroundRunner:
    """Bounded daemon tasks so network waits cannot hold the process open on exit."""

    def __init__(self, maximum: int = 3) -> None:
        self._semaphore = threading.BoundedSemaphore(maximum)
        self._lock = threading.Lock()
        self._closed = False
        self._futures: set[Future[Any]] = set()

    def submit(self, function: Callable[..., Any], *args: Any) -> Future[Any]:
        future: Future[Any] = Future()
        with self._lock:
            if self._closed:
                raise RuntimeError("Background runner is closed")
            self._futures.add(future)

        def run() -> None:
            try:
                with self._semaphore:
                    if not future.set_running_or_notify_cancel():
                        return
                    try:
                        future.set_result(function(*args))
                    except BaseException as exc:
                        future.set_exception(exc)
            finally:
                with self._lock:
                    self._futures.discard(future)

        threading.Thread(target=run, name="angel-worker", daemon=True).start()
        return future

    def shutdown(self, wait: bool = False, cancel_futures: bool = True) -> None:
        del wait  # Running daemon tasks intentionally do not delay window shutdown.
        with self._lock:
            self._closed = True
            futures = list(self._futures)
        if cancel_futures:
            for future in futures:
                future.cancel()


class AngelUI:
    def __init__(
        self,
        root: tk.Tk,
        database: Database,
        settings: SettingsService,
        memory: MemoryService,
        brain: AngelBrain,
        ollama: OllamaClient,
        logger: logging.Logger | None = None,
        speech: WindowsSpeechService | None = None,
        services: Any | None = None,
    ) -> None:
        self.root = root
        self.database = database
        self.settings = settings
        self.memory = memory
        self.brain = brain
        self.ollama = ollama
        self.logger = logger or logging.getLogger("angel.ui")
        self.speech = speech or WindowsSpeechService(self.logger.getChild("speech"))
        self.services = services
        self.executor = BackgroundRunner(maximum=3)
        self.ui_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.closing = False
        self.busy = False
        self.current_conversation_id: int | None = None
        self.conversation_ids: list[int] = []
        self.pending_attachments: list[dict[str, Any]] = []
        self.last_assistant_text = ""
        self.speech_future: Future[bool] | None = None
        self.cancel_event: threading.Event | None = None
        self.generation_id = 0
        self.last_user_text = ""
        self.last_user_attachments: list[dict[str, Any]] = []
        self.last_response_sources: list[dict[str, str]] = []
        self.source_tag_counter = 0
        self._configure_window()
        self._configure_style()
        self._build()
        self._load_initial_conversation()
        self.refresh_status()
        self.root.after(40, self._drain_ui_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _configure_window(self) -> None:
        self.root.title("ANGEL")
        self.root.geometry("1180x780")
        self.root.minsize(920, 650)
        self.root.configure(bg=COLORS["black"])

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Angel.TButton",
            background=COLORS["panel_alt"],
            foreground=COLORS["white"],
            bordercolor=COLORS["violet"],
            focusthickness=1,
            focuscolor=COLORS["violet"],
            padding=(12, 8),
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "Angel.TButton",
            background=[("active", COLORS["violet"]), ("pressed", COLORS["violet_hover"])],
        )
        style.configure(
            "Primary.TButton",
            background=COLORS["violet"],
            foreground=COLORS["white"],
            bordercolor=COLORS["violet"],
            padding=(18, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map("Primary.TButton", background=[("active", COLORS["violet_hover"])])
        style.configure(
            "Danger.TButton",
            background=COLORS["panel_alt"],
            foreground=COLORS["bad"],
            bordercolor=COLORS["bad"],
            padding=(12, 7),
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#512B38"), ("pressed", "#673344")],
            foreground=[("active", COLORS["white"])],
        )
        style.configure(
            "Angel.Treeview",
            background=COLORS["panel"],
            fieldbackground=COLORS["panel"],
            foreground=COLORS["white"],
            rowheight=28,
            borderwidth=0,
        )
        style.map("Angel.Treeview", background=[("selected", COLORS["violet"])])
        style.configure(
            "Angel.Treeview.Heading",
            background=COLORS["panel_alt"],
            foreground=COLORS["gold"],
            relief="flat",
            font=("Segoe UI Semibold", 9),
        )
        style.configure("TNotebook", background=COLORS["charcoal"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=COLORS["panel_alt"],
            foreground=COLORS["white"],
            padding=(14, 8),
        )
        style.map("TNotebook.Tab", background=[("selected", COLORS["violet"])])
        style.configure(
            "Angel.TCombobox",
            fieldbackground=COLORS["panel_alt"],
            background=COLORS["panel_alt"],
            foreground=COLORS["white"],
        )

    def _build(self) -> None:
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_body()
        self._build_quick_actions()
        self._build_input()

    def _build_header(self) -> None:
        frame = tk.Frame(self.root, bg=COLORS["charcoal"], padx=24, pady=13)
        frame.grid(row=0, column=0, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        brand = tk.Frame(frame, bg=COLORS["charcoal"])
        brand.grid(row=0, column=0, sticky="w")
        tk.Label(
            brand,
            text="ANGEL",
            bg=COLORS["charcoal"],
            fg=COLORS["white"],
            font=("Segoe UI Semibold", 22),
        ).pack(side="left")
        tk.Label(
            brand,
            text="  Local Personal AI",
            bg=COLORS["charcoal"],
            fg=COLORS["gold"],
            font=("Segoe UI", 10),
        ).pack(side="left", anchor="s", pady=(0, 4))
        statuses = tk.Frame(frame, bg=COLORS["charcoal"])
        statuses.grid(row=0, column=2, sticky="e")
        self.ai_status = self._status_label(statuses, "Local AI · Checking", 0)
        self.search_status = self._status_label(statuses, "Internet · Checking", 1)
        self.memory_status = self._status_label(statuses, "Memory · Enabled", 2)
        self.mode_status = self._status_label(statuses, "Mode · Auto", 3)

    def _status_label(self, parent: tk.Widget, text: str, column: int) -> tk.Label:
        label = tk.Label(
            parent,
            text=text,
            bg=COLORS["panel_alt"],
            fg=COLORS["muted"],
            padx=10,
            pady=5,
            font=("Segoe UI", 9),
        )
        label.grid(row=0, column=column, padx=(7, 0))
        return label

    def _build_body(self) -> None:
        body = tk.Frame(self.root, bg=COLORS["black"], padx=14, pady=12)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        sidebar = tk.Frame(body, bg=COLORS["charcoal"], width=245, padx=10, pady=10)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(3, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)
        ttk.Button(
            sidebar, text="＋  New Conversation", style="Primary.TButton", command=self.new_conversation
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))
        tk.Label(
            sidebar,
            text="CONVERSATIONS",
            bg=COLORS["charcoal"],
            fg=COLORS["gold"],
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.conversation_search_var = tk.StringVar()
        conversation_search = tk.Entry(
            sidebar,
            textvariable=self.conversation_search_var,
            bg=COLORS["panel_alt"],
            fg=COLORS["white"],
            insertbackground=COLORS["white"],
            relief="flat",
            font=("Segoe UI", 9),
        )
        conversation_search.grid(row=2, column=0, sticky="ew", ipady=6, pady=(0, 7))
        conversation_search.bind("<KeyRelease>", lambda _event: self.refresh_conversations())
        self.conversation_list = tk.Listbox(
            sidebar,
            bg=COLORS["charcoal"],
            fg=COLORS["white"],
            selectbackground=COLORS["violet"],
            selectforeground=COLORS["white"],
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            font=("Segoe UI", 10),
        )
        self.conversation_list.grid(row=3, column=0, sticky="nsew")
        self.conversation_list.bind("<<ListboxSelect>>", self._select_conversation)
        self.conversation_list.bind("<Delete>", lambda _event: self.delete_conversation())
        ttk.Button(
            sidebar,
            text="Rename Conversation",
            style="Angel.TButton",
            command=self.rename_conversation,
        ).grid(row=4, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(
            sidebar,
            text="Delete Conversation",
            style="Danger.TButton",
            command=self.delete_conversation,
        ).grid(row=5, column=0, sticky="ew", pady=(7, 0))
        controls = tk.Frame(sidebar, bg=COLORS["charcoal"])
        controls.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        controls.grid_columnconfigure((0, 1), weight=1)
        ttk.Button(controls, text="Memory", style="Angel.TButton", command=self.show_memory).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(controls, text="Settings", style="Angel.TButton", command=self.show_settings).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        features = tk.Frame(sidebar, bg=COLORS["charcoal"])
        features.grid(row=7, column=0, sticky="ew", pady=(8, 0))
        features.grid_columnconfigure((0, 1), weight=1)
        feature_buttons = (
            ("Projects", self.show_projects),
            ("Knowledge", self.show_knowledge),
            ("Creator", self.show_creator),
            ("Setup", self.show_setup),
            ("Backups", self.show_data_protection),
            ("Diagnostics", self.show_diagnostics),
        )
        for index, (label, command) in enumerate(feature_buttons):
            ttk.Button(features, text=label, style="Angel.TButton", command=command).grid(
                row=index // 2,
                column=index % 2,
                sticky="ew",
                padx=(0, 4) if index % 2 == 0 else (4, 0),
                pady=(0, 6),
            )

        conversation = tk.Frame(body, bg=COLORS["panel"], padx=16, pady=12)
        conversation.grid(row=0, column=1, sticky="nsew")
        conversation.grid_rowconfigure(2, weight=1)
        conversation.grid_columnconfigure(0, weight=1)
        chat_actions = tk.Frame(conversation, bg=COLORS["panel"], pady=3)
        chat_actions.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        chat_actions.grid_columnconfigure(4, weight=1)
        ttk.Button(chat_actions, text="Copy Reply", style="Angel.TButton", command=self.copy_last_reply).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(chat_actions, text="Reuse Prompt", style="Angel.TButton", command=self.reuse_last_prompt).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(chat_actions, text="Regenerate", style="Angel.TButton", command=self.regenerate_response).grid(row=0, column=2, padx=(0, 6))
        self.stop_button = ttk.Button(chat_actions, text="Stop Generating", style="Danger.TButton", command=self.stop_generation, state="disabled")
        self.stop_button.grid(row=0, column=3, padx=(0, 8))
        tk.Label(chat_actions, text="Local-first · your history stays on this PC", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).grid(row=0, column=4, sticky="e")
        voice_controls = tk.Frame(conversation, bg=COLORS["panel"], pady=3)
        voice_controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 7))
        voice_controls.grid_columnconfigure(3, weight=1)
        ttk.Button(
            voice_controls,
            text="Read Last Reply",
            style="Angel.TButton",
            command=self.read_last_reply,
        ).grid(row=0, column=0, padx=(0, 7))
        ttk.Button(
            voice_controls,
            text="Stop Voice",
            style="Angel.TButton",
            command=self.stop_speaking,
        ).grid(row=0, column=1, padx=(0, 10))
        self.auto_read_var = tk.BooleanVar(
            value=self.settings.get().read_aloud_enabled
        )
        tk.Checkbutton(
            voice_controls,
            text="Automatically read Angel replies",
            variable=self.auto_read_var,
            command=self._toggle_auto_read,
            bg=COLORS["panel"],
            fg=COLORS["white"],
            selectcolor=COLORS["panel_alt"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["white"],
        ).grid(row=0, column=2, sticky="w")
        self.voice_status = tk.Label(
            voice_controls,
            text="Voice · Windows",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="e",
        )
        self.voice_status.grid(row=0, column=3, sticky="e")
        self.chat = tk.Text(
            conversation,
            bg=COLORS["panel"],
            fg=COLORS["white"],
            insertbackground=COLORS["white"],
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=10,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 11),
            spacing1=3,
            spacing3=7,
        )
        scrollbar = ttk.Scrollbar(conversation, orient="vertical", command=self.chat.yview)
        self.chat.configure(yscrollcommand=scrollbar.set)
        self.chat.grid(row=2, column=0, sticky="nsew")
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.chat.tag_configure("user_label", foreground=COLORS["gold"], font=("Segoe UI Semibold", 10))
        self.chat.tag_configure("angel_label", foreground=COLORS["electric"], font=("Segoe UI Semibold", 10))
        self.chat.tag_configure("user_text", foreground=COLORS["white"], lmargin1=16, lmargin2=16)
        self.chat.tag_configure("angel_text", foreground=COLORS["white"], lmargin1=16, lmargin2=16)
        self.chat.tag_configure("source_header", foreground=COLORS["gold"], font=("Segoe UI Semibold", 9))
        self.chat.tag_configure("muted", foreground=COLORS["muted"], font=("Segoe UI Italic", 9))
        self.chat.tag_configure("code", foreground="#D6F5E3", background="#111820", font=("Cascadia Mono", 10), lmargin1=24, lmargin2=24, spacing1=4, spacing3=4)

    def _build_quick_actions(self) -> None:
        frame = tk.Frame(self.root, bg=COLORS["black"], padx=14, pady=0)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 9))
        for index, mode in enumerate(QUICK_ACTIONS):
            frame.grid_columnconfigure(index, weight=1)
            ttk.Button(
                frame,
                text=mode,
                style="Angel.TButton",
                command=lambda value=mode: self.send_quick_action(value),
            ).grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 4, 0))

    def _build_input(self) -> None:
        frame = tk.Frame(self.root, bg=COLORS["charcoal"], padx=14, pady=12)
        frame.grid(row=3, column=0, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        attachments = tk.Frame(frame, bg=COLORS["charcoal"])
        attachments.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        attachments.grid_columnconfigure(1, weight=1)
        ttk.Button(
            attachments,
            text="Upload Files",
            style="Angel.TButton",
            command=self.upload_files,
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.attachment_label = tk.Label(
            attachments,
            text="Attach images, audio, video, documents, or any other file type",
            bg=COLORS["charcoal"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.attachment_label.grid(row=0, column=1, sticky="ew")
        self.clear_attachments_button = ttk.Button(
            attachments,
            text="Clear",
            style="Angel.TButton",
            command=self.clear_attachments,
            state="disabled",
        )
        self.add_attachments_project_button = ttk.Button(
            attachments,
            text="Add to Project",
            style="Angel.TButton",
            command=self.add_attachments_to_project,
            state="disabled",
        )
        self.add_attachments_project_button.grid(row=0, column=2, sticky="e", padx=(10, 0))
        self.clear_attachments_button.grid(row=0, column=3, sticky="e", padx=(7, 0))
        self.input_box = tk.Text(
            frame,
            height=3,
            wrap="word",
            bg=COLORS["panel_alt"],
            fg=COLORS["white"],
            insertbackground=COLORS["white"],
            relief="flat",
            padx=12,
            pady=10,
            font=("Segoe UI", 11),
        )
        self.input_box.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.input_box.bind("<Return>", self._send_on_enter)
        self.input_box.bind("<KP_Enter>", self._send_on_enter)
        self.input_box.bind("<Control-Return>", self._send_shortcut)
        self.send_button = ttk.Button(
            frame, text="Send", style="Primary.TButton", command=self.send_message
        )
        self.send_button.grid(row=1, column=1, sticky="ns")
        self.thinking_label = tk.Label(
            frame,
            text="Enter to send · Shift+Enter for a new line",
            bg=COLORS["charcoal"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.thinking_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

    def _load_initial_conversation(self) -> None:
        conversations = self.database.list_conversations()
        if conversations:
            self.current_conversation_id = int(conversations[0]["id"])
        else:
            self.current_conversation_id = self.database.create_conversation()
        self.refresh_conversations(select_id=self.current_conversation_id)
        self.load_conversation(self.current_conversation_id)

    def refresh_conversations(self, select_id: int | None = None) -> None:
        query = self.conversation_search_var.get() if hasattr(self, "conversation_search_var") else ""
        conversations = self.database.search_conversations(query)
        self.conversation_ids = [int(item["id"]) for item in conversations]
        self.conversation_list.delete(0, "end")
        for item in conversations:
            self.conversation_list.insert("end", f"  {item['title']}")
        target = select_id if select_id is not None else self.current_conversation_id
        if target in self.conversation_ids:
            index = self.conversation_ids.index(target)
            self.conversation_list.selection_set(index)
            self.conversation_list.activate(index)

    def new_conversation(self) -> None:
        if self.busy:
            return
        conversation_id = self.database.create_conversation()
        self.current_conversation_id = conversation_id
        self.refresh_conversations(select_id=conversation_id)
        self.load_conversation(conversation_id)
        self.input_box.focus_set()

    def rename_conversation(self) -> None:
        if self.busy or self.current_conversation_id is None:
            return
        conversation = next(
            (
                item
                for item in self.database.list_conversations()
                if int(item["id"]) == self.current_conversation_id
            ),
            None,
        )
        if conversation is None:
            return
        title = simpledialog.askstring(
            "Rename Conversation",
            "Conversation name:",
            initialvalue=str(conversation["title"]),
            parent=self.root,
        )
        if title is None:
            return
        clean_title = " ".join(title.split()).strip()[:120]
        if not clean_title:
            messagebox.showerror(
                "Rename Conversation", "The conversation name cannot be empty.", parent=self.root
            )
            return
        self.database.rename_conversation(self.current_conversation_id, clean_title)
        self.refresh_conversations(select_id=self.current_conversation_id)

    def delete_conversation(self) -> None:
        if self.busy or self.current_conversation_id is None:
            return
        conversation_id = self.current_conversation_id
        conversation = next(
            (
                item
                for item in self.database.list_conversations()
                if int(item["id"]) == conversation_id
            ),
            None,
        )
        if conversation is None:
            return
        title = str(conversation["title"])
        confirmed = messagebox.askyesno(
            "Delete Conversation",
            f'Delete "{title}" and all of its messages?\n\nThis cannot be undone.',
            icon="warning",
            parent=self.root,
        )
        if not confirmed:
            return
        if not self.database.delete_conversation(conversation_id):
            messagebox.showerror(
                "Delete Conversation",
                "That conversation could not be found.",
                parent=self.root,
            )
            return
        remaining = self.database.list_conversations()
        if remaining:
            self.current_conversation_id = int(remaining[0]["id"])
        else:
            self.current_conversation_id = self.database.create_conversation()
        self.refresh_conversations(select_id=self.current_conversation_id)
        self.load_conversation(self.current_conversation_id)

    def _select_conversation(self, _event: tk.Event[Any]) -> None:
        selection = self.conversation_list.curselection()
        if not selection or self.busy:
            return
        conversation_id = self.conversation_ids[int(selection[0])]
        self.current_conversation_id = conversation_id
        self.load_conversation(conversation_id)

    def load_conversation(self, conversation_id: int) -> None:
        self.stop_speaking(update_status=False)
        self.last_assistant_text = ""
        self.last_user_text = ""
        self.last_user_attachments = []
        self.last_response_sources = []
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        messages = self.database.get_messages(conversation_id, limit=200)
        if not messages:
            self.chat.insert(
                "end",
                "Angel\n",
                "angel_label",
            )
            self.chat.insert(
                "end",
                "I’m here. Talk to me, use a quick action, or open Memory and Settings.\n\n",
                "muted",
            )
        for message in messages:
            self._insert_message(
                message["role"],
                message["content"],
                message.get("sources", []),
                message.get("attachments", []),
            )
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _insert_message(
        self,
        role: str,
        content: str,
        sources: list[dict[str, str]] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> None:
        if role == "assistant":
            self.last_assistant_text = content.strip()
            self.last_response_sources = list(sources or [])
        elif role == "user":
            self.last_user_text = content.strip()
            self.last_user_attachments = list(attachments or [])
        self.chat.insert("end", "You\n" if role == "user" else "Angel\n", "user_label" if role == "user" else "angel_label")
        if role == "assistant":
            self._insert_assistant_content(content.strip())
        else:
            self.chat.insert("end", content.strip() + "\n", "user_text")
        if role == "user" and attachments:
            for attachment in attachments:
                name = str(attachment.get("name") or "unnamed file")
                kind = str(attachment.get("media_kind") or "file")
                size = format_size(int(attachment.get("size") or 0))
                status = str(attachment.get("parse_status") or "metadata_only")
                availability = "text available" if status == "text_extracted" else "attached · metadata only"
                path = str(attachment.get("path") or "")
                self.source_tag_counter += 1
                tag = f"attachment_{self.source_tag_counter}"
                self.chat.tag_configure(tag, foreground=COLORS["muted"], underline=bool(path))
                if path:
                    self.chat.tag_bind(tag, "<Button-1>", lambda _event, target=path: self._open_local_path(target))
                    self.chat.tag_bind(tag, "<Enter>", lambda _event: self.chat.configure(cursor="hand2"))
                    self.chat.tag_bind(tag, "<Leave>", lambda _event: self.chat.configure(cursor="xterm"))
                self.chat.insert("end", f"  📎 {name} — {kind}, {size} · {availability}\n", tag)
        if role == "assistant" and sources:
            self.chat.insert("end", f"Searched the web · {len(sources)} sources\n", "source_header")
            for source in sources:
                url = str(source.get("url", ""))
                if not is_safe_public_url(url):
                    continue
                self.source_tag_counter += 1
                tag = f"source_{self.source_tag_counter}"
                title = str(source.get("title") or source.get("domain") or "Source")
                domain = str(source.get("domain") or "")
                self.chat.tag_configure(tag, foreground=COLORS["electric"], underline=True, lmargin1=16, lmargin2=16)
                self.chat.tag_bind(tag, "<Button-1>", lambda _event, target=url: webbrowser.open(target))
                self.chat.tag_bind(tag, "<Enter>", lambda _event: self.chat.configure(cursor="hand2"))
                self.chat.tag_bind(tag, "<Leave>", lambda _event: self.chat.configure(cursor="xterm"))
                self.chat.insert("end", f"  {title} — {domain}\n", tag)
        self.chat.insert("end", "\n")

    def _insert_assistant_content(self, content: str) -> None:
        parts = content.split("```")
        for index, part in enumerate(parts):
            if index % 2:
                code = part
                first_line, separator, remainder = code.partition("\n")
                if separator and len(first_line.strip()) < 30 and " " not in first_line.strip():
                    code = remainder
                self.chat.insert("end", code.rstrip() + "\n", "code")
            else:
                if part:
                    self.chat.insert("end", part, "angel_text")
        if not content.endswith("\n"):
            self.chat.insert("end", "\n", "angel_text")

    def _open_local_path(self, value: str) -> None:
        try:
            path = os.path.abspath(value)
            if os.path.exists(path):
                os.startfile(path)  # type: ignore[attr-defined]
        except OSError as exc:
            messagebox.showerror("Open File", str(exc), parent=self.root)

    def _play_local_audio(self, value: str) -> None:
        path = os.path.abspath(value) if value else ""
        if not path or not os.path.isfile(path):
            return
        try:
            import winsound

            if Path(path).suffix.lower() == ".wav":
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                os.startfile(path)  # type: ignore[attr-defined]
        except (OSError, RuntimeError) as exc:
            messagebox.showerror("Play Audio", str(exc), parent=self.root)

    @staticmethod
    def _stop_local_audio() -> None:
        try:
            import winsound

            winsound.PlaySound(None, winsound.SND_PURGE)
        except (ImportError, RuntimeError):
            pass

    def copy_last_reply(self) -> None:
        if not self.last_assistant_text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.last_assistant_text)
        self._set_thinking("Latest reply copied")

    def reuse_last_prompt(self) -> None:
        if not self.last_user_text or self.busy:
            return
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", self.last_user_text)
        self.input_box.focus_set()

    def regenerate_response(self) -> None:
        if self.busy or self.current_conversation_id is None:
            return
        user = self.database.last_message(self.current_conversation_id, "user")
        if not user:
            return
        assistant = self.database.last_message(self.current_conversation_id, "assistant")
        if assistant and int(assistant["id"]) > int(user["id"]):
            self.database.delete_message(int(assistant["id"]))
        self.load_conversation(self.current_conversation_id)
        self._begin_response(
            str(user["content"]),
            None,
            list(user.get("attachments", [])),
            display_user=False,
            record_user=False,
        )

    def stop_generation(self) -> None:
        if not self.busy:
            return
        if self.cancel_event is not None:
            self.cancel_event.set()
        self.generation_id += 1
        self.busy = False
        self.send_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._set_thinking("Generation stopped · your saved history is intact")

    def _toggle_auto_read(self) -> None:
        self.settings.update(read_aloud_enabled=bool(self.auto_read_var.get()))

    def read_last_reply(self) -> None:
        if not self.last_assistant_text:
            self.voice_status.configure(text="Voice · No reply yet", fg=COLORS["muted"])
            return
        self.read_aloud(self.last_assistant_text)

    def read_aloud(
        self,
        text: str,
        voice_name: str | None = None,
        rate: int | None = None,
    ) -> None:
        if not text.strip() or self.closing:
            return
        self.stop_speaking(update_status=False)
        current = self.settings.get()
        selected_voice = current.voice_name if voice_name is None else voice_name
        selected_rate = current.speech_rate if rate is None else rate
        self.voice_status.configure(text="Voice · Speaking…", fg=COLORS["electric"])
        future = self.executor.submit(
            self.speech.speak, text, selected_voice, selected_rate
        )
        self.speech_future = future
        self._poll_future(future, self._speech_finished)

    def _speech_finished(self, future: Future[bool]) -> None:
        if self.closing or future is not self.speech_future:
            return
        self.speech_future = None
        try:
            successful = bool(future.result())
        except Exception:
            self.logger.exception("Read aloud failed")
            successful = False
        self.voice_status.configure(
            text="Voice · Ready" if successful else "Voice · Unavailable",
            fg=COLORS["good"] if successful else COLORS["bad"],
        )

    def stop_speaking(self, update_status: bool = True) -> None:
        self.speech_future = None
        self.speech.stop()
        if update_status and hasattr(self, "voice_status") and not self.closing:
            self.voice_status.configure(text="Voice · Stopped", fg=COLORS["muted"])

    def send_message(self) -> None:
        text = self.input_box.get("1.0", "end").strip()
        if (not text and not self.pending_attachments) or self.busy:
            return
        attachments = list(self.pending_attachments)
        self.input_box.delete("1.0", "end")
        self.clear_attachments()
        self._begin_response(text, None, attachments)

    def send_quick_action(self, mode: str) -> None:
        if self.busy:
            return
        attachments = list(self.pending_attachments)
        self.clear_attachments()
        self._begin_response("", mode, attachments)

    def upload_files(self) -> None:
        selected = filedialog.askopenfilenames(
            parent=self.root,
            title="Upload files to Angel",
            filetypes=(
                ("All files", "*.*"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tif *.tiff *.svg"),
                ("Audio", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.wma"),
                ("Video", "*.mp4 *.mov *.mkv *.avi *.webm *.wmv *.m4v"),
                ("Documents", "*.txt *.md *.pdf *.doc *.docx *.rtf *.csv *.json"),
            ),
        )
        if not selected:
            return
        combined_paths = [item["path"] for item in self.pending_attachments] + list(selected)
        self.pending_attachments = prepare_attachments(combined_paths)
        self._update_attachment_bar()
        if len(combined_paths) > MAX_ATTACHMENTS:
            messagebox.showinfo(
                "Angel Uploads",
                f"Angel attached the first {MAX_ATTACHMENTS} unique files for this message.",
                parent=self.root,
            )

    def clear_attachments(self) -> None:
        self.pending_attachments = []
        self._update_attachment_bar()

    def add_attachments_to_project(self) -> None:
        if not self.pending_attachments or self.services is None:
            return
        project = self.services.projects.active()
        if project is None:
            messagebox.showinfo(
                "Add to Project",
                "Choose an active project in Projects first, then try again.",
                parent=self.root,
            )
            return
        added = 0
        for attachment in self.pending_attachments:
            path = str(attachment.get("path") or "")
            name = str(attachment.get("name") or "Attached file")
            details = (
                f"{attachment.get('media_kind', 'file')} · "
                f"{format_size(int(attachment.get('size') or 0))} · "
                f"{attachment.get('parse_status', 'metadata_only')}"
            )
            self.services.projects.add_item(
                int(project["id"]), "file", name, details, file_path=path
            )
            added += 1
        messagebox.showinfo(
            "Add to Project",
            f"Added {added} file reference(s) to {project['name']}.",
            parent=self.root,
        )

    def _update_attachment_bar(self) -> None:
        if not self.pending_attachments:
            self.attachment_label.configure(
                text="Attach images, audio, video, documents, or any other file type",
                fg=COLORS["muted"],
            )
            self.clear_attachments_button.configure(state="disabled")
            self.add_attachments_project_button.configure(state="disabled")
            return
        names = [str(item.get("name") or "unnamed file") for item in self.pending_attachments]
        preview = ", ".join(names[:3])
        if len(names) > 3:
            preview += f" +{len(names) - 3} more"
        self.attachment_label.configure(
            text=f"{len(names)} attached: {preview}", fg=COLORS["electric"]
        )
        self.clear_attachments_button.configure(state="normal")
        self.add_attachments_project_button.configure(
            state="normal" if self.services is not None else "disabled"
        )

    def _send_on_enter(self, event: tk.Event[Any]) -> str | None:
        if event.state & 0x0001:
            return None
        self.send_message()
        return "break"

    def _send_shortcut(self, _event: tk.Event[Any]) -> str:
        self.send_message()
        return "break"

    def _begin_response(
        self,
        text: str,
        mode: str | None,
        attachments: list[dict[str, Any]] | None = None,
        *,
        display_user: bool = True,
        record_user: bool = True,
    ) -> None:
        if self.current_conversation_id is None:
            self.new_conversation()
        conversation_id = int(self.current_conversation_id or 0)
        self.busy = True
        self.generation_id += 1
        generation_id = self.generation_id
        self.cancel_event = threading.Event()
        self.send_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        prepared_attachments = attachments or []
        display = mode + (f" — {text}" if text else "") if mode else text
        if not display:
            display = "Uploaded file" if len(prepared_attachments) == 1 else "Uploaded files"
        if display_user:
            self.chat.configure(state="normal")
            self._insert_message("user", display, attachments=prepared_attachments)
            self.chat.configure(state="disabled")
            self.chat.see("end")
        self._set_thinking("Thinking…")
        event_queue = self.ui_queue
        future = self.executor.submit(
            self.brain.respond,
            text,
            conversation_id,
            mode,
            lambda value: event_queue.put(("thinking", value)),
            prepared_attachments,
            self.cancel_event,
            record_user,
        )
        self._poll_future(
            future, lambda done: self._response_finished(done, conversation_id, generation_id)
        )

    def _response_finished(
        self, future: Future[BrainResponse], conversation_id: int, generation_id: int
    ) -> None:
        if self.closing or generation_id != self.generation_id:
            return
        self.busy = False
        self.cancel_event = None
        self.send_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._set_thinking("Enter to send · Shift+Enter for a new line")
        try:
            response = future.result()
        except Exception as exc:
            self.logger.exception("Background response failed")
            response = BrainResponse(f"I hit a safe error: {exc}", local_ai_available=False)
        if response.cancelled:
            self._set_thinking("Generation stopped · your saved history is intact")
            return
        if self.current_conversation_id == conversation_id:
            self.chat.configure(state="normal")
            self._insert_message("assistant", response.content, response.sources)
            self.chat.configure(state="disabled")
            self.chat.see("end")
            if self.settings.get().read_aloud_enabled:
                self.read_aloud(response.content)
        self.refresh_conversations(select_id=self.current_conversation_id)
        self.ai_status.configure(
            text="Local AI · Online" if response.local_ai_available else "Local AI · Offline",
            fg=COLORS["good"] if response.local_ai_available else COLORS["bad"],
        )

    def _set_thinking(self, value: str) -> None:
        if not self.closing:
            self.thinking_label.configure(text=value)

    def refresh_status(self) -> None:
        current = self.settings.get()
        self.mode_status.configure(text=f"Mode · {current.connectivity_mode}", fg=COLORS["electric"])
        if current.connectivity_mode == "Offline":
            self.search_status.configure(text="Internet · Blocked", fg=COLORS["muted"])
        elif not current.internet_search_enabled:
            self.search_status.configure(text="Internet · Disabled", fg=COLORS["muted"])
        else:
            self.search_status.configure(text="Internet · Checking", fg=COLORS["muted"])
            if self.services is not None:
                internet_future = self.executor.submit(self.services.diagnostics._internet_online)
                self._poll_future(internet_future, self._internet_finished)
        self.memory_status.configure(
            text=f"Memory · {'Enabled' if current.memory_enabled else 'Disabled'}",
            fg=COLORS["good"] if current.memory_enabled else COLORS["muted"],
        )
        self.ai_status.configure(text="Local AI · Checking", fg=COLORS["muted"])
        future = self.executor.submit(self._check_local_ai, current)
        self._poll_future(future, self._status_finished)

    def _check_local_ai(self, current: AngelSettings) -> tuple[bool, list[str]]:
        online, models = self.ollama.check(current.ollama_url)
        if not online and current.auto_start_ollama and self.services is not None:
            self.services.local_ai.ensure_running(current.ollama_url)
            online, models = self.ollama.check(current.ollama_url)
        if online and current.model in models and self.services is not None:
            inference_ok, _message = self.services.local_ai.test_inference(
                current.ollama_url, current.model
            )
            online = inference_ok
        return online, models

    def _internet_finished(self, future: Future[bool]) -> None:
        if self.closing or self.settings.get().connectivity_mode == "Offline":
            return
        try:
            online = bool(future.result())
        except Exception:
            online = False
        self.search_status.configure(
            text="Internet · Online" if online else "Internet · Offline",
            fg=COLORS["good"] if online else COLORS["bad"],
        )

    def _status_finished(self, future: Future[tuple[bool, list[str]]]) -> None:
        if self.closing:
            return
        try:
            online, models = future.result()
        except Exception:
            online, models = False, []
        text = "Angel Local AI · READY" if online else "Angel Local AI · OFFLINE"
        if online and not models:
            text = "Angel Local AI · NO MODELS"
        self.ai_status.configure(text=text, fg=COLORS["good"] if online and models else COLORS["bad"])

    def show_memory(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("Angel Memory")
        window.geometry("760x500")
        window.minsize(620, 400)
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        window.grid_rowconfigure(2, weight=1)
        window.grid_columnconfigure(0, weight=1)
        tk.Label(
            window,
            text="MEMORY",
            bg=COLORS["charcoal"],
            fg=COLORS["white"],
            font=("Segoe UI Semibold", 18),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 8))
        search_row = tk.Frame(window, bg=COLORS["charcoal"])
        search_row.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        search_row.grid_columnconfigure(0, weight=1)
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_row,
            textvariable=search_var,
            bg=COLORS["panel_alt"],
            fg=COLORS["white"],
            insertbackground=COLORS["white"],
            relief="flat",
            font=("Segoe UI", 10),
        )
        search_entry.grid(row=0, column=0, sticky="ew", ipady=7, padx=(0, 8))
        tree = ttk.Treeview(
            window,
            columns=("category", "memory"),
            show="headings",
            style="Angel.Treeview",
            selectmode="browse",
        )
        tree.heading("category", text="Category")
        tree.heading("memory", text="Memory")
        tree.column("category", width=120, anchor="w", stretch=False)
        tree.column("memory", width=560, anchor="w")
        tree.grid(row=2, column=0, sticky="nsew", padx=18)
        controls = tk.Frame(window, bg=COLORS["charcoal"])
        controls.grid(row=3, column=0, sticky="ew", padx=18, pady=14)

        def refresh() -> None:
            for child in tree.get_children():
                tree.delete(child)
            try:
                items = self.memory.list(search_var.get(), limit=200)
            except MemoryDisabledError:
                messagebox.showinfo("Angel Memory", "Memory is disabled in Settings.", parent=window)
                return
            for item in items:
                tree.insert("", "end", iid=str(item["id"]), values=(item["category"], item["text"]))

        def add_memory() -> None:
            dialog = tk.Toplevel(window)
            dialog.title("Add Memory")
            dialog.geometry("520x210")
            dialog.configure(bg=COLORS["charcoal"])
            dialog.transient(window)
            tk.Label(dialog, text="What should Angel remember?", bg=COLORS["charcoal"], fg=COLORS["white"]).pack(anchor="w", padx=16, pady=(16, 5))
            text_box = tk.Text(dialog, height=4, bg=COLORS["panel_alt"], fg=COLORS["white"], insertbackground=COLORS["white"], relief="flat", wrap="word")
            text_box.pack(fill="x", padx=16)
            category_var = tk.StringVar(value="general")
            category = ttk.Combobox(dialog, textvariable=category_var, values=MEMORY_CATEGORIES, state="readonly", style="Angel.TCombobox")
            category.pack(anchor="w", padx=16, pady=8)

            def save() -> None:
                try:
                    self.memory.add(text_box.get("1.0", "end"), category_var.get())
                except Exception as exc:
                    messagebox.showerror("Angel Memory", str(exc), parent=dialog)
                    return
                dialog.destroy()
                refresh()

            ttk.Button(dialog, text="Save Memory", style="Primary.TButton", command=save).pack(anchor="e", padx=16, pady=(0, 12))
            text_box.focus_set()

        def delete_memory() -> None:
            selection = tree.selection()
            if not selection:
                return
            if messagebox.askyesno("Delete Memory", "Forget the selected memory?", parent=window):
                try:
                    self.memory.delete(int(selection[0]))
                except Exception as exc:
                    messagebox.showerror("Angel Memory", str(exc), parent=window)
                refresh()

        def edit_memory() -> None:
            selection = tree.selection()
            if not selection:
                return
            item = self.memory.get(int(selection[0]))
            text = simpledialog.askstring("Edit Memory", "Memory content:", initialvalue=item["text"], parent=window)
            if text is None:
                return
            category = simpledialog.askstring("Edit Memory", "Category:", initialvalue=item["category"], parent=window)
            if not category:
                return
            try:
                self.memory.update(int(item["id"]), text=text, category=category)
                refresh()
            except Exception as exc:
                messagebox.showerror("Angel Memory", str(exc), parent=window)

        ttk.Button(search_row, text="Search", style="Angel.TButton", command=refresh).grid(row=0, column=1)
        ttk.Button(controls, text="Add Memory", style="Primary.TButton", command=add_memory).pack(side="left")
        ttk.Button(controls, text="Edit", style="Angel.TButton", command=edit_memory).pack(side="left", padx=7)
        ttk.Button(controls, text="Delete", style="Angel.TButton", command=delete_memory).pack(side="right")
        search_entry.bind("<Return>", lambda _event: refresh())
        refresh()

    def show_projects(self) -> None:
        if self.services is None:
            messagebox.showinfo("Projects", "Project Memory is unavailable in this runtime.", parent=self.root)
            return
        projects = self.services.projects
        window = tk.Toplevel(self.root)
        window.title("Angel Projects")
        window.geometry("920x620")
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        window.grid_rowconfigure(2, weight=1)
        window.grid_columnconfigure(0, weight=1)
        tk.Label(window, text="PROJECT MEMORY", bg=COLORS["charcoal"], fg=COLORS["white"], font=("Segoe UI Semibold", 18)).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 6))
        active_label = tk.Label(window, text="", bg=COLORS["charcoal"], fg=COLORS["gold"], anchor="w")
        active_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 8))
        pane = tk.PanedWindow(window, orient="horizontal", bg=COLORS["charcoal"], sashwidth=6)
        pane.grid(row=2, column=0, sticky="nsew", padx=18)
        project_tree = ttk.Treeview(pane, columns=("status", "state"), show="tree headings", style="Angel.Treeview", selectmode="browse")
        project_tree.heading("#0", text="Project")
        project_tree.heading("status", text="Status")
        project_tree.heading("state", text="Current State")
        project_tree.column("#0", width=180)
        project_tree.column("status", width=80)
        project_tree.column("state", width=250)
        item_tree = ttk.Treeview(pane, columns=("type", "status", "record"), show="headings", style="Angel.Treeview", selectmode="browse")
        item_tree.heading("type", text="Type")
        item_tree.heading("status", text="Status")
        item_tree.heading("record", text="Project Record")
        item_tree.column("type", width=80)
        item_tree.column("status", width=80)
        item_tree.column("record", width=320)
        pane.add(project_tree, minsize=350)
        pane.add(item_tree, minsize=350)

        def selected_project_id() -> int | None:
            selection = project_tree.selection()
            return int(selection[0]) if selection else None

        def refresh_items(_event: Any = None) -> None:
            for child in item_tree.get_children():
                item_tree.delete(child)
            project_id = selected_project_id()
            if project_id is None:
                return
            for item in projects.items(project_id):
                detail = item["title"] + (f" — {item['content']}" if item["content"] else "")
                item_tree.insert("", "end", iid=str(item["id"]), values=(item["kind"], item["status"], detail))

        def refresh_projects(select_id: int | None = None) -> None:
            for child in project_tree.get_children():
                project_tree.delete(child)
            active = projects.active()
            active_label.configure(text=f"Active project: {active['name']}" if active else "Active project: none selected")
            for project in projects.list():
                project_tree.insert("", "end", iid=str(project["id"]), text=project["name"], values=(project["status"], project["current_state"] or project["description"]))
            target = str(select_id or (active["id"] if active else ""))
            if target and project_tree.exists(target):
                project_tree.selection_set(target)
                project_tree.see(target)
            refresh_items()

        def add_project() -> None:
            name = simpledialog.askstring("New Project", "Project name:", parent=window)
            if not name:
                return
            description = simpledialog.askstring("New Project", "Short description (optional):", parent=window) or ""
            try:
                project = projects.create(name, description)
                projects.set_active(int(project["id"]))
                refresh_projects(int(project["id"]))
            except Exception as exc:
                messagebox.showerror("Projects", str(exc), parent=window)

        def edit_state() -> None:
            project_id = selected_project_id()
            if project_id is None:
                return
            project = projects.get(project_id)
            state = simpledialog.askstring("Current Project State", "Where did you leave off?", initialvalue=project["current_state"], parent=window)
            if state is not None:
                projects.update(project_id, current_state=state)
                refresh_projects(project_id)

        def add_record() -> None:
            project_id = selected_project_id()
            if project_id is None:
                return
            kind = simpledialog.askstring("Project Record", "Type: decision, todo, completed, idea, note, file, or activity", initialvalue="note", parent=window)
            title = simpledialog.askstring("Project Record", "Title:", parent=window)
            if not kind or not title:
                return
            content = simpledialog.askstring("Project Record", "Details (optional):", parent=window) or ""
            try:
                projects.add_item(project_id, kind, title, content)
                refresh_projects(project_id)
            except Exception as exc:
                messagebox.showerror("Projects", str(exc), parent=window)

        controls = tk.Frame(window, bg=COLORS["charcoal"])
        controls.grid(row=3, column=0, sticky="ew", padx=18, pady=14)
        for label, command in (("New Project", add_project), ("Set Active", lambda: projects.set_active(selected_project_id()) if selected_project_id() else None), ("Update State", edit_state), ("Add Record", add_record)):
            ttk.Button(controls, text=label, style="Angel.TButton", command=lambda cmd=command: (cmd(), refresh_projects(selected_project_id()))).pack(side="left", padx=(0, 7))
        ttk.Button(controls, text="Delete Project", style="Danger.TButton", command=lambda: self._delete_project_from_window(window, project_tree, refresh_projects)).pack(side="right")
        project_tree.bind("<<TreeviewSelect>>", refresh_items)
        refresh_projects()

    def _delete_project_from_window(self, window: tk.Toplevel, tree: ttk.Treeview, refresh: Callable[..., None]) -> None:
        if self.services is None or not tree.selection():
            return
        project_id = int(tree.selection()[0])
        project = self.services.projects.get(project_id)
        if messagebox.askyesno("Delete Project", f"Delete project '{project['name']}' and its project records?", icon="warning", parent=window):
            self.services.projects.delete(project_id)
            refresh()

    def show_knowledge(self) -> None:
        if self.services is None:
            messagebox.showinfo("Knowledge", "Knowledge Library is unavailable.", parent=self.root)
            return
        knowledge = self.services.knowledge
        window = tk.Toplevel(self.root)
        window.title("Angel Knowledge Library")
        window.geometry("900x600")
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        window.grid_rowconfigure(2, weight=1)
        window.grid_columnconfigure(0, weight=1)
        tk.Label(window, text="KNOWLEDGE LIBRARY", bg=COLORS["charcoal"], fg=COLORS["white"], font=("Segoe UI Semibold", 18)).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 6))
        tk.Label(window, text="Documents are copied and indexed locally. This is separate from Angel Memory.", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 8))
        tree = ttk.Treeview(window, columns=("status", "chunks", "path"), show="tree headings", style="Angel.Treeview", selectmode="browse")
        tree.heading("#0", text="Document")
        tree.heading("status", text="Parsing")
        tree.heading("chunks", text="Chunks")
        tree.heading("path", text="Stored Local Copy")
        tree.column("#0", width=220)
        tree.column("status", width=110)
        tree.column("chunks", width=70)
        tree.column("path", width=430)
        tree.grid(row=2, column=0, sticky="nsew", padx=18)

        def refresh() -> None:
            for child in tree.get_children():
                tree.delete(child)
            for document in knowledge.list():
                tree.insert("", "end", iid=str(document["id"]), text=document["title"], values=(document["parse_status"], document["chunk_count"], document["stored_path"]))

        def add_files() -> None:
            selected = filedialog.askopenfilenames(parent=window, title="Add documents to Angel Knowledge", filetypes=(("Supported documents", "*.txt *.md *.json *.csv *.html *.htm *.pdf *.docx *.xlsx *.py *.js *.ps1"), ("All files", "*.*")))
            for path in selected:
                try:
                    knowledge.add(path)
                except Exception as exc:
                    messagebox.showerror("Knowledge", f"{Path(path).name}: {exc}", parent=window)
            refresh()

        def selected_id() -> int | None:
            return int(tree.selection()[0]) if tree.selection() else None

        def search_library() -> None:
            query = simpledialog.askstring("Search Knowledge", "What should Angel find?", parent=window)
            if not query:
                return
            results = knowledge.search(query, 8)
            text = "\n\n".join(f"{item['title']} (chunk {int(item['chunk_index']) + 1})\n{item['content'][:1000]}" for item in results) or "No local knowledge matched."
            messagebox.showinfo("Knowledge Search", text[:7000], parent=window)

        controls = tk.Frame(window, bg=COLORS["charcoal"])
        controls.grid(row=3, column=0, sticky="ew", padx=18, pady=14)
        ttk.Button(controls, text="Add Documents", style="Primary.TButton", command=add_files).pack(side="left", padx=(0, 7))
        ttk.Button(controls, text="Search", style="Angel.TButton", command=search_library).pack(side="left", padx=(0, 7))
        ttk.Button(controls, text="Reindex", style="Angel.TButton", command=lambda: (knowledge.reindex(selected_id()), refresh()) if selected_id() else None).pack(side="left", padx=(0, 7))
        ttk.Button(controls, text="Open File", style="Angel.TButton", command=lambda: self._open_local_path(knowledge.get(selected_id())["stored_path"]) if selected_id() else None).pack(side="left")
        ttk.Button(controls, text="Remove", style="Danger.TButton", command=lambda: (knowledge.remove(selected_id()), refresh()) if selected_id() and messagebox.askyesno("Remove Knowledge", "Remove the selected document and its local index?", parent=window) else None).pack(side="right")
        refresh()

    def show_data_protection(self) -> None:
        if self.services is None:
            return
        window = tk.Toplevel(self.root)
        window.title("Angel Storage & Data Protection")
        window.geometry("720x480")
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        report = tk.Text(window, bg=COLORS["panel"], fg=COLORS["white"], relief="flat", wrap="word", font=("Segoe UI", 10), padx=14, pady=12)
        report.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        def refresh() -> None:
            status = self.services.backups.status()
            text = (
                f"Database: {'Healthy' if status['database_healthy'] else status['database_detail']}\n"
                "Persistent Memory: Protected in Angel's data directory\n"
                f"Last Backup: {status['last_backup']}\nAvailable Backups: {status['backup_count']}\n"
                "Cache: Safe to delete; Angel recreates it automatically\n\n"
                f"Data Directory: {status['data_directory']}\nBackup Directory: {status['backup_directory']}\n"
                f"Cache Directory: {status['cache_directory']}"
            )
            report.delete("1.0", "end")
            report.insert("1.0", text)

        def backup_now() -> None:
            try:
                info = self.services.backups.create("manual UI backup")
                messagebox.showinfo("Backup Angel", f"Backup created:\n{info.path}", parent=window)
                refresh()
            except Exception as exc:
                messagebox.showerror("Backup Angel", str(exc), parent=window)

        def restore() -> None:
            selected = filedialog.askopenfilename(parent=window, initialdir=str(self.services.layout.backups), title="Restore Angel Backup", filetypes=(("Angel backups", "angel-backup-*.zip"),))
            if not selected or not messagebox.askyesno("Restore Angel", "Restore this backup? Angel will first create a safety backup. Restart Angel afterward.", icon="warning", parent=window):
                return
            try:
                safety = self.services.backups.restore(selected)
                messagebox.showinfo("Restore Angel", f"Restore completed. Safety backup:\n{safety.path}\n\nPlease restart Angel.", parent=window)
                refresh()
            except Exception as exc:
                messagebox.showerror("Restore Angel", str(exc), parent=window)

        controls = tk.Frame(window, bg=COLORS["charcoal"])
        controls.pack(fill="x", padx=16, pady=(0, 16))
        for label, command in (("Backup Now", backup_now), ("Restore", restore), ("Open Data Folder", lambda: self._open_local_path(str(self.services.layout.data))), ("Open Backups", lambda: self._open_local_path(str(self.services.layout.backups)))):
            ttk.Button(controls, text=label, style="Angel.TButton", command=command).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Clear Disposable Cache", style="Danger.TButton", command=lambda: (self.services.backups.clear_cache(), refresh()) if messagebox.askyesno("Clear Cache", "Delete only Angel's disposable cache? Conversations, memory, projects, knowledge, settings, and creations will remain.", parent=window) else None).pack(side="right")
        refresh()

    def show_diagnostics(self) -> None:
        if self.services is None:
            return
        window = tk.Toplevel(self.root)
        window.title("Angel Diagnostics")
        window.geometry("820x650")
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        text_box = tk.Text(window, bg=COLORS["panel"], fg=COLORS["white"], relief="flat", wrap="word", font=("Cascadia Mono", 9), padx=12, pady=12)
        text_box.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        text_box.insert("1.0", "Collecting non-sensitive diagnostics…")

        def finished(future: Future[str]) -> None:
            try:
                value = future.result()
            except Exception as exc:
                value = f"Diagnostics failed safely: {exc}"
            text_box.delete("1.0", "end")
            text_box.insert("1.0", value)

        future = self.executor.submit(self.services.diagnostics.report, True)
        self._poll_future(future, finished)
        controls = tk.Frame(window, bg=COLORS["charcoal"])
        controls.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(controls, text="Copy Diagnostic Report", style="Primary.TButton", command=lambda: (self.root.clipboard_clear(), self.root.clipboard_append(text_box.get("1.0", "end").strip()))).pack(side="right")

    def show_setup(self) -> None:
        if self.services is None:
            return
        window = tk.Toplevel(self.root)
        window.title("Angel Local AI & Setup Center")
        window.geometry("850x650")
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        text_box = tk.Text(window, bg=COLORS["panel"], fg=COLORS["white"], relief="flat", wrap="word", font=("Cascadia Mono", 9), padx=12, pady=12)
        text_box.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        def render(status: Any) -> None:
            hardware = status.hardware
            names = [item["name"] for item in status.models]
            lines = [
                f"Angel Local AI: {'READY' if status.running and status.configured_model_installed else 'NEEDS ATTENTION'}",
                f"Ollama installed: {status.installed}",
                f"Ollama running: {status.running}",
                f"Executable: {status.executable or 'Not found'}",
                f"Active chat model: {status.configured_model}",
                f"Configured model installed: {status.configured_model_installed}",
                f"Model storage: {status.model_storage}",
                f"Model storage used: {format_size(status.model_storage_bytes)}",
                "",
                f"CPU: {hardware.cpu} ({hardware.cpu_threads} threads)",
                f"System RAM: {format_size(hardware.ram_bytes)}",
                f"GPU: {hardware.gpu}",
                f"VRAM: {format_size(hardware.vram_bytes)}",
                f"Free disk: {format_size(hardware.free_disk_bytes)}",
                "",
                "Installed chat models:",
            ]
            for model in status.models:
                recommendation = self.services.local_ai.model_recommendation(model["name"], hardware.ram_bytes)
                lines.append(f"  {model['name']} · {format_size(model['size'])} · {recommendation}")
            if not names:
                lines.append("  None detected. Angel never downloads a large model without your approval.")
            lines.extend(("", "Optional local capabilities:"))
            for capability in self.services.router.statuses(status.running and status.configured_model_installed, names):
                lines.append(f"  {capability.role}: {'READY' if capability.installed else 'NOT INSTALLED'} · {capability.backend} · {capability.model or 'no model'}")
                lines.append(f"    {capability.message}")
            text_box.delete("1.0", "end")
            text_box.insert("1.0", "\n".join(lines))

        def refresh() -> None:
            text_box.delete("1.0", "end")
            text_box.insert("1.0", "Inspecting local services and hardware…")
            current = self.settings.get()
            future = self.executor.submit(self.services.local_ai.status, current.ollama_url, current.model)
            self._poll_future(future, lambda done: render(done.result()))

        def start_ai() -> None:
            current = self.settings.get()
            future = self.executor.submit(self.services.local_ai.ensure_running, current.ollama_url)
            self._poll_future(future, lambda done: (messagebox.showinfo("Start Local AI", done.result()[1], parent=window), refresh(), self.refresh_status()))

        def restart_ai() -> None:
            if not messagebox.askyesno("Restart Local AI", "Stop and restart the local Ollama process? Active model work will stop.", icon="warning", parent=window):
                return
            current = self.settings.get()
            future = self.executor.submit(self.services.local_ai.restart, current.ollama_url)
            self._poll_future(future, lambda done: (messagebox.showinfo("Restart Local AI", done.result()[1], parent=window), refresh(), self.refresh_status()))

        def test_ai() -> None:
            current = self.settings.get()
            future = self.executor.submit(self.services.local_ai.test_inference, current.ollama_url, current.model)
            self._poll_future(future, lambda done: messagebox.showinfo("Test Local AI", done.result()[1], parent=window))

        controls = tk.Frame(window, bg=COLORS["charcoal"])
        controls.pack(fill="x", padx=16, pady=(0, 16))
        for label, command in (("Start Local AI", start_ai), ("Restart Local AI", restart_ai), ("Test Local AI", test_ai), ("Refresh Models", refresh), ("Open Model Manager", lambda: self._open_local_path(str(self.services.local_ai.model_storage_path())))):
            ttk.Button(controls, text=label, style="Angel.TButton", command=command).pack(side="left", padx=(0, 6))
        refresh()

    def show_creator(self) -> None:
        if self.services is None:
            return
        window = tk.Toplevel(self.root)
        window.title("Angel Creator")
        window.geometry("940x720")
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=14, pady=14)
        image_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=14, pady=14)
        music_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=14, pady=14)
        library_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=14, pady=14)
        notebook.add(image_tab, text="Images")
        notebook.add(music_tab, text="Music Studio")
        notebook.add(library_tab, text="Creator Library")

        def entry(parent: tk.Widget, label: str, row: int, default: str = "") -> tk.Entry:
            tk.Label(parent, text=label, bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").grid(row=row, column=0, sticky="w", pady=3)
            box = tk.Entry(parent, bg=COLORS["panel_alt"], fg=COLORS["white"], insertbackground=COLORS["white"], relief="flat")
            box.grid(row=row, column=1, sticky="ew", ipady=6, pady=3)
            box.insert(0, default)
            parent.grid_columnconfigure(1, weight=1)
            return box

        image_status = tk.Label(image_tab, text=self.services.images.status().message, bg=COLORS["charcoal"], fg=COLORS["gold"], anchor="w", wraplength=780, justify="left")
        image_status.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        image_prompt = entry(image_tab, "Prompt", 1)
        image_negative = entry(image_tab, "Negative Prompt", 2)
        image_width = entry(image_tab, "Width", 3, "1024")
        image_height = entry(image_tab, "Height", 4, "1024")
        image_steps = entry(image_tab, "Steps / Quality", 5, "20")
        image_seed = entry(image_tab, "Seed (blank = random)", 6)
        image_last: dict[str, Any] = {}

        def generate_image() -> None:
            try:
                seed = int(image_seed.get()) if image_seed.get().strip() else None
                args = (image_prompt.get(), image_negative.get(), int(image_width.get()), int(image_height.get()), seed, int(image_steps.get()), "")
            except ValueError:
                messagebox.showerror("Angel Images", "Width, height, steps, and seed must be numbers.", parent=window)
                return
            image_status.configure(text="Generating locally with ComfyUI…", fg=COLORS["electric"])
            future = self.executor.submit(self.services.images.generate, *args)
            def done(result: Future[dict[str, Any]]) -> None:
                try:
                    item = result.result()
                    image_last.clear(); image_last.update(item)
                    image_status.configure(text=f"Saved: {item['output_path']}", fg=COLORS["good"])
                    refresh_library()
                except Exception as exc:
                    image_status.configure(text=str(exc), fg=COLORS["bad"])
            self._poll_future(future, done)

        image_controls = tk.Frame(image_tab, bg=COLORS["charcoal"])
        image_controls.grid(row=7, column=0, columnspan=2, sticky="ew", pady=12)
        ttk.Button(image_controls, text="Generate", style="Primary.TButton", command=generate_image).pack(side="left", padx=(0, 7))
        ttk.Button(image_controls, text="Regenerate", style="Angel.TButton", command=generate_image).pack(side="left", padx=(0, 7))
        ttk.Button(image_controls, text="Open Output Folder", style="Angel.TButton", command=lambda: self._open_local_path(str(self.services.layout.generated_images))).pack(side="left")

        music_status = tk.Label(music_tab, text=self.services.music.status().message, bg=COLORS["charcoal"], fg=COLORS["gold"], anchor="w", wraplength=780, justify="left")
        music_status.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        song_title = entry(music_tab, "Song Title", 1)
        song_description = entry(music_tab, "Description", 2)
        song_genre = entry(music_tab, "Genre", 3)
        song_mood = entry(music_tab, "Mood", 4)
        vocal_style = entry(music_tab, "Vocal Style", 5)
        duration = entry(music_tab, "Duration (10-600 seconds)", 6, "30")
        song_seed = entry(music_tab, "Seed (blank = random)", 7)
        instrumental = tk.BooleanVar(value=False)
        tk.Checkbutton(music_tab, text="Instrumental (no vocals)", variable=instrumental, bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).grid(row=8, column=1, sticky="w", pady=4)
        tk.Label(music_tab, text="Lyrics", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="nw").grid(row=9, column=0, sticky="nw", pady=3)
        lyrics = tk.Text(music_tab, height=9, bg=COLORS["panel_alt"], fg=COLORS["white"], insertbackground=COLORS["white"], relief="flat", wrap="word")
        lyrics.grid(row=9, column=1, sticky="nsew", pady=3)
        music_tab.grid_rowconfigure(9, weight=1)
        music_last: dict[str, Any] = {}

        def generate_music() -> None:
            try:
                seed = int(song_seed.get()) if song_seed.get().strip() else None
                seconds = int(duration.get())
            except ValueError:
                messagebox.showerror("Music Studio", "Duration and seed must be numbers.", parent=window)
                return
            music_status.configure(text="Generating locally with ACE-Step…", fg=COLORS["electric"])
            future = self.executor.submit(self.services.music.generate, song_title.get(), song_description.get(), song_genre.get(), song_mood.get(), lyrics.get("1.0", "end").strip(), instrumental.get(), vocal_style.get(), seconds, seed)
            def done(result: Future[dict[str, Any]]) -> None:
                try:
                    item = result.result(); music_last.clear(); music_last.update(item)
                    music_status.configure(text=f"Saved: {item['output_path']}", fg=COLORS["good"])
                    refresh_library()
                except Exception as exc:
                    music_status.configure(text=str(exc), fg=COLORS["bad"])
            self._poll_future(future, done)

        music_controls = tk.Frame(music_tab, bg=COLORS["charcoal"])
        music_controls.grid(row=10, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(music_controls, text="Generate", style="Primary.TButton", command=generate_music).pack(side="left", padx=(0, 7))
        ttk.Button(music_controls, text="Regenerate", style="Angel.TButton", command=generate_music).pack(side="left", padx=(0, 7))
        ttk.Button(music_controls, text="Play", style="Angel.TButton", command=lambda: self._play_local_audio(music_last.get("output_path", ""))).pack(side="left", padx=(0, 7))
        ttk.Button(music_controls, text="Stop", style="Angel.TButton", command=self._stop_local_audio).pack(side="left", padx=(0, 7))
        ttk.Button(music_controls, text="Open Output Folder", style="Angel.TButton", command=lambda: self._open_local_path(str(self.services.layout.generated_music))).pack(side="left")

        library = ttk.Treeview(library_tab, columns=("type", "backend", "date", "path"), show="tree headings", style="Angel.Treeview", selectmode="browse")
        for column, label, width in (("#0", "Title", 200), ("type", "Type", 80), ("backend", "Backend", 120), ("date", "Created", 150), ("path", "Persistent Output", 300)):
            library.heading(column, text=label); library.column(column, width=width)
        library.pack(fill="both", expand=True)
        def refresh_library() -> None:
            for child in library.get_children(): library.delete(child)
            for item in self.services.creator_library.list():
                library.insert("", "end", iid=str(item["id"]), text=item["title"], values=(item["kind"], item["backend"], item["created_at"], item["output_path"]))
        lib_controls = tk.Frame(library_tab, bg=COLORS["charcoal"]); lib_controls.pack(fill="x", pady=(10, 0))
        ttk.Button(lib_controls, text="Open Creation", style="Angel.TButton", command=lambda: self._open_local_path(self.services.creator_library.get(int(library.selection()[0]))["output_path"]) if library.selection() else None).pack(side="left")
        refresh_library()

    def show_settings(self) -> None:
        current = self.settings.get()
        window = tk.Toplevel(self.root)
        window.title("Angel Settings")
        window.geometry("780x760")
        window.minsize(680, 650)
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=16, pady=16)
        local_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        user_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        angel_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        setup_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        storage_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        about_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        notebook.add(local_tab, text="Local AI")
        notebook.add(user_tab, text="User")
        notebook.add(angel_tab, text="Angel")
        notebook.add(setup_tab, text="Local Services")
        notebook.add(storage_tab, text="Storage / Data Protection")
        notebook.add(about_tab, text="About & Privacy")
        variables = {
            "ollama_url": tk.StringVar(value=current.ollama_url),
            "model": tk.StringVar(value=current.model),
            "display_name": tk.StringVar(value=current.display_name),
            "city": tk.StringVar(value=current.city),
            "region": tk.StringVar(value=current.region),
            "postal_code": tk.StringVar(value=current.postal_code),
            "response_style": tk.StringVar(value=current.response_style),
            "internet_search_enabled": tk.BooleanVar(value=current.internet_search_enabled),
            "memory_enabled": tk.BooleanVar(value=current.memory_enabled),
            "read_aloud_enabled": tk.BooleanVar(value=current.read_aloud_enabled),
            "voice_name": tk.StringVar(value=current.voice_name or "System default"),
            "speech_rate": tk.StringVar(value=str(current.speech_rate)),
            "connectivity_mode": tk.StringVar(value=current.connectivity_mode),
            "resource_profile": tk.StringVar(value=current.resource_profile),
            "technical_level": tk.StringVar(value=current.technical_level),
            "formatting_preference": tk.StringVar(value=current.formatting_preference),
            "workflow_preferences": tk.StringVar(value=current.workflow_preferences),
            "auto_start_ollama": tk.BooleanVar(value=current.auto_start_ollama),
            "coding_model": tk.StringVar(value=current.coding_model),
            "vision_model": tk.StringVar(value=current.vision_model),
            "comfyui_url": tk.StringVar(value=current.comfyui_url),
            "comfyui_model": tk.StringVar(value=current.comfyui_model),
            "acestep_url": tk.StringVar(value=current.acestep_url),
            "acestep_model": tk.StringVar(value=current.acestep_model),
            "knowledge_enabled": tk.BooleanVar(value=current.knowledge_enabled),
        }

        def labeled_entry(parent: tk.Widget, label: str, variable: tk.StringVar, row: int) -> tk.Entry:
            tk.Label(parent, text=label, bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").grid(row=row * 2, column=0, sticky="ew", pady=(6, 3))
            entry = tk.Entry(parent, textvariable=variable, bg=COLORS["panel_alt"], fg=COLORS["white"], insertbackground=COLORS["white"], relief="flat", font=("Segoe UI", 10))
            entry.grid(row=row * 2 + 1, column=0, sticky="ew", ipady=7)
            parent.grid_columnconfigure(0, weight=1)
            return entry

        labeled_entry(local_tab, "Ollama URL", variables["ollama_url"], 0)
        tk.Label(local_tab, text="Model", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").grid(row=2, column=0, sticky="ew", pady=(12, 3))
        model_box = ttk.Combobox(local_tab, textvariable=variables["model"], values=(current.model,), style="Angel.TCombobox")
        model_box.grid(row=3, column=0, sticky="ew", ipady=5)
        connection_label = tk.Label(local_tab, text="", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w")
        connection_label.grid(row=5, column=0, sticky="ew", pady=8)

        def check_models() -> None:
            connection_label.configure(text="Checking Ollama…", fg=COLORS["muted"])
            future = self.executor.submit(self.ollama.check, variables["ollama_url"].get().strip())

            def done() -> None:
                try:
                    online, models = future.result()
                except Exception:
                    online, models = False, []
                model_box.configure(values=models or (variables["model"].get(),))
                connection_label.configure(
                    text=(f"Connected · {len(models)} installed model(s)" if online else "Ollama is offline"),
                    fg=COLORS["good"] if online else COLORS["bad"],
                )

            self._poll_future(future, lambda _future: done())

        button_row = tk.Frame(local_tab, bg=COLORS["charcoal"])
        button_row.grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Button(button_row, text="Refresh Models", style="Angel.TButton", command=check_models).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="Recheck Connection", style="Angel.TButton", command=check_models).pack(side="left")
        tk.Checkbutton(local_tab, text="Automatically start local Ollama when Angel opens", variable=variables["auto_start_ollama"], bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).grid(row=6, column=0, sticky="w", pady=(8, 4))
        ttk.Button(local_tab, text="Open Full Local AI Manager", style="Primary.TButton", command=self.show_setup).grid(row=7, column=0, sticky="w", pady=(10, 0))

        labeled_entry(user_tab, "Display Name", variables["display_name"], 0)
        labeled_entry(user_tab, "City", variables["city"], 1)
        labeled_entry(user_tab, "State / Region", variables["region"], 2)
        labeled_entry(user_tab, "ZIP / Postal Code", variables["postal_code"], 3)
        labeled_entry(user_tab, "Technical Explanation Preference", variables["technical_level"], 4)
        labeled_entry(user_tab, "Formatting Preference", variables["formatting_preference"], 5)
        labeled_entry(user_tab, "Workflow Preferences", variables["workflow_preferences"], 6)
        tk.Label(user_tab, text="These editable preferences are separate from factual long-term memory. Location stays local unless needed in a permitted web search.", bg=COLORS["charcoal"], fg=COLORS["muted"], wraplength=620, justify="left").grid(row=14, column=0, sticky="w", pady=(14, 0))

        tk.Label(angel_tab, text="Response Style", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").pack(fill="x", pady=(4, 3))
        ttk.Combobox(angel_tab, textvariable=variables["response_style"], values=("Concise", "Balanced", "Detailed"), state="readonly", style="Angel.TCombobox").pack(fill="x", ipady=5)
        tk.Label(angel_tab, text="Connectivity Mode", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").pack(fill="x", pady=(12, 3))
        ttk.Combobox(angel_tab, textvariable=variables["connectivity_mode"], values=("Offline", "Local + Internet Tools", "Auto"), state="readonly", style="Angel.TCombobox").pack(fill="x", ipady=5)
        tk.Label(angel_tab, text="Resource Profile", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").pack(fill="x", pady=(12, 3))
        ttk.Combobox(angel_tab, textvariable=variables["resource_profile"], values=("Low Resource", "Balanced", "Maximum Quality"), state="readonly", style="Angel.TCombobox").pack(fill="x", ipady=5)
        tk.Checkbutton(angel_tab, text="Enable Internet Search", variable=variables["internet_search_enabled"], bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).pack(anchor="w", pady=(18, 6))
        tk.Checkbutton(angel_tab, text="Enable Memory", variable=variables["memory_enabled"], bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).pack(anchor="w", pady=6)
        tk.Checkbutton(angel_tab, text="Enable Local Knowledge Library", variable=variables["knowledge_enabled"], bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).pack(anchor="w", pady=6)
        tk.Checkbutton(angel_tab, text="Automatically read Angel replies", variable=variables["read_aloud_enabled"], bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).pack(anchor="w", pady=(12, 6))
        tk.Label(angel_tab, text="Windows Voice", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").pack(fill="x", pady=(8, 3))
        voice_box = ttk.Combobox(
            angel_tab,
            textvariable=variables["voice_name"],
            values=("System default",),
            state="readonly",
            style="Angel.TCombobox",
        )
        voice_box.pack(fill="x", ipady=5)
        tk.Label(angel_tab, text="Speaking Speed (-10 slow to 10 fast)", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").pack(fill="x", pady=(12, 3))
        ttk.Combobox(
            angel_tab,
            textvariable=variables["speech_rate"],
            values=tuple(str(value) for value in range(-10, 11)),
            state="readonly",
            style="Angel.TCombobox",
        ).pack(fill="x", ipady=5)
        voice_row = tk.Frame(angel_tab, bg=COLORS["charcoal"])
        voice_row.pack(fill="x", pady=(10, 0))
        voice_message = tk.Label(
            voice_row,
            text="Loading voices…",
            bg=COLORS["charcoal"],
            fg=COLORS["muted"],
        )
        voice_message.pack(side="right")

        def preview_voice() -> None:
            selected = str(variables["voice_name"].get())
            voice = "" if selected == "System default" else selected
            try:
                rate = int(str(variables["speech_rate"].get()))
            except ValueError:
                rate = 0
            self.read_aloud("Hello. I am Angel, using a Windows voice.", voice, rate)

        ttk.Button(
            voice_row,
            text="Test Voice",
            style="Angel.TButton",
            command=preview_voice,
        ).pack(side="left")

        def voices_finished(future: Future[list[str]]) -> None:
            try:
                voices = future.result()
            except Exception:
                voices = []
            values = ("System default", *voices)
            voice_box.configure(values=values)
            selected = str(variables["voice_name"].get())
            if selected not in values:
                variables["voice_name"].set("System default")
            voice_message.configure(
                text=f"{len(voices)} installed voice(s)" if voices else "Windows voice unavailable",
                fg=COLORS["good"] if voices else COLORS["bad"],
            )

        voices_future = self.executor.submit(self.speech.list_voices)
        self._poll_future(voices_future, voices_finished)

        labeled_entry(setup_tab, "Coding Model (optional Ollama model)", variables["coding_model"], 0)
        labeled_entry(setup_tab, "Vision Model (optional Ollama vision model)", variables["vision_model"], 1)
        labeled_entry(setup_tab, "ComfyUI Local URL", variables["comfyui_url"], 2)
        labeled_entry(setup_tab, "ComfyUI Checkpoint (blank = first installed)", variables["comfyui_model"], 3)
        labeled_entry(setup_tab, "ACE-Step 1.5 Local URL", variables["acestep_url"], 4)
        labeled_entry(setup_tab, "ACE-Step Model (optional)", variables["acestep_model"], 5)
        tk.Label(setup_tab, text="Angel only connects these creator services through localhost. Models are never downloaded automatically.", bg=COLORS["charcoal"], fg=COLORS["muted"], wraplength=620, justify="left").grid(row=12, column=0, sticky="w", pady=(12, 0))
        ttk.Button(setup_tab, text="Open Setup Center", style="Primary.TButton", command=self.show_setup).grid(row=13, column=0, sticky="w", pady=(14, 0))

        if self.services is not None:
            protection = self.services.backups.status()
            storage_text = (
                f"Database: {'Healthy' if protection['database_healthy'] else protection['database_detail']}\n\n"
                "Persistent Memory: Protected\n"
                f"Last Backup: {protection['last_backup']}\nAvailable Backups: {protection['backup_count']}\n"
                "Cache: Safe to Delete\n\n"
                f"Data Directory: {protection['data_directory']}\n"
                f"Backup Directory: {protection['backup_directory']}\n"
                f"Cache Directory: {protection['cache_directory']}"
            )
            tk.Label(storage_tab, text=storage_text, bg=COLORS["charcoal"], fg=COLORS["white"], justify="left", anchor="nw", wraplength=640, font=("Segoe UI", 10)).pack(fill="x", pady=(4, 18))
            ttk.Button(storage_tab, text="Open Storage & Data Protection", style="Primary.TButton", command=self.show_data_protection).pack(anchor="w")

        about_text = (
            "ANGEL\nLocal Personal AI\n\n"
            "A local-first personal assistant built to help you think, remember, search, decide, and figure out what to do next.\n\n"
            "PRIVACY\nConversations are stored locally. Memories are stored locally. Ollama requests go to your configured Ollama service. "
            "Web searches necessarily send the search query to the public search provider. Angel has no telemetry, analytics, or tracking."
        )
        tk.Label(about_tab, text=about_text, bg=COLORS["charcoal"], fg=COLORS["white"], justify="left", anchor="nw", wraplength=570, font=("Segoe UI", 10)).pack(fill="both", expand=True)

        def save() -> None:
            try:
                values = {key: variable.get() for key, variable in variables.items()}
                if values["voice_name"] == "System default":
                    values["voice_name"] = ""
                updated = self.settings.update(**values)
            except Exception as exc:
                messagebox.showerror("Angel Settings", str(exc), parent=window)
                return
            self.auto_read_var.set(updated.read_aloud_enabled)
            window.destroy()
            self.refresh_status()

        ttk.Button(window, text="Save Settings", style="Primary.TButton", command=save).pack(anchor="e", padx=16, pady=(0, 16))
        check_models()

    def _drain_ui_queue(self) -> None:
        if self.closing:
            return
        while True:
            try:
                event, value = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                if event == "thinking":
                    self._set_thinking(str(value))
            except Exception:
                self.logger.exception("Queued UI callback failed")
        try:
            self.root.after(40, self._drain_ui_queue)
        except tk.TclError:
            pass

    def _poll_future(
        self, future: Future[Any], callback: Callable[[Future[Any]], None]
    ) -> None:
        if self.closing:
            return
        if future.done():
            callback(future)
            return
        try:
            self.root.after(50, lambda: self._poll_future(future, callback))
        except tk.TclError:
            pass

    def close(self) -> None:
        if self.closing:
            return
        self.closing = True
        self.logger.info("Angel shutdown requested")
        self.speech.close()
        self.executor.shutdown(wait=False, cancel_futures=True)
        try:
            self.root.destroy()
        except tk.TclError:
            pass
