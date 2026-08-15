from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
import webbrowser
from concurrent.futures import Future
from tkinter import filedialog, messagebox, ttk
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
    ) -> None:
        self.root = root
        self.database = database
        self.settings = settings
        self.memory = memory
        self.brain = brain
        self.ollama = ollama
        self.logger = logger or logging.getLogger("angel.ui")
        self.speech = speech or WindowsSpeechService(self.logger.getChild("speech"))
        self.executor = BackgroundRunner(maximum=3)
        self.ui_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.closing = False
        self.busy = False
        self.current_conversation_id: int | None = None
        self.conversation_ids: list[int] = []
        self.pending_attachments: list[dict[str, Any]] = []
        self.last_assistant_text = ""
        self.speech_future: Future[bool] | None = None
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
        self.search_status = self._status_label(statuses, "Search · Enabled", 1)
        self.memory_status = self._status_label(statuses, "Memory · Enabled", 2)

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
        sidebar.grid_rowconfigure(2, weight=1)
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
        self.conversation_list.grid(row=2, column=0, sticky="nsew")
        self.conversation_list.bind("<<ListboxSelect>>", self._select_conversation)
        self.conversation_list.bind("<Delete>", lambda _event: self.delete_conversation())
        ttk.Button(
            sidebar,
            text="Delete Conversation",
            style="Danger.TButton",
            command=self.delete_conversation,
        ).grid(row=3, column=0, sticky="ew", pady=(10, 0))
        controls = tk.Frame(sidebar, bg=COLORS["charcoal"])
        controls.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        controls.grid_columnconfigure((0, 1), weight=1)
        ttk.Button(controls, text="Memory", style="Angel.TButton", command=self.show_memory).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(controls, text="Settings", style="Angel.TButton", command=self.show_settings).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        conversation = tk.Frame(body, bg=COLORS["panel"], padx=16, pady=12)
        conversation.grid(row=0, column=1, sticky="nsew")
        conversation.grid_rowconfigure(1, weight=1)
        conversation.grid_columnconfigure(0, weight=1)
        voice_controls = tk.Frame(conversation, bg=COLORS["panel"], pady=3)
        voice_controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 7))
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
        self.chat.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.chat.tag_configure("user_label", foreground=COLORS["gold"], font=("Segoe UI Semibold", 10))
        self.chat.tag_configure("angel_label", foreground=COLORS["electric"], font=("Segoe UI Semibold", 10))
        self.chat.tag_configure("user_text", foreground=COLORS["white"], lmargin1=16, lmargin2=16)
        self.chat.tag_configure("angel_text", foreground=COLORS["white"], lmargin1=16, lmargin2=16)
        self.chat.tag_configure("source_header", foreground=COLORS["gold"], font=("Segoe UI Semibold", 9))
        self.chat.tag_configure("muted", foreground=COLORS["muted"], font=("Segoe UI Italic", 9))

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
        self.clear_attachments_button.grid(row=0, column=2, sticky="e", padx=(10, 0))
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
        conversations = self.database.list_conversations()
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
        self.chat.insert("end", "You\n" if role == "user" else "Angel\n", "user_label" if role == "user" else "angel_label")
        self.chat.insert("end", content.strip() + "\n", "user_text" if role == "user" else "angel_text")
        if role == "user" and attachments:
            for attachment in attachments:
                name = str(attachment.get("name") or "unnamed file")
                kind = str(attachment.get("media_kind") or "file")
                size = format_size(int(attachment.get("size") or 0))
                status = str(attachment.get("parse_status") or "metadata_only")
                availability = "text available" if status == "text_extracted" else "attached · metadata only"
                self.chat.insert(
                    "end",
                    f"  📎 {name} — {kind}, {size} · {availability}\n",
                    "muted",
                )
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

    def _update_attachment_bar(self) -> None:
        if not self.pending_attachments:
            self.attachment_label.configure(
                text="Attach images, audio, video, documents, or any other file type",
                fg=COLORS["muted"],
            )
            self.clear_attachments_button.configure(state="disabled")
            return
        names = [str(item.get("name") or "unnamed file") for item in self.pending_attachments]
        preview = ", ".join(names[:3])
        if len(names) > 3:
            preview += f" +{len(names) - 3} more"
        self.attachment_label.configure(
            text=f"{len(names)} attached: {preview}", fg=COLORS["electric"]
        )
        self.clear_attachments_button.configure(state="normal")

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
    ) -> None:
        if self.current_conversation_id is None:
            self.new_conversation()
        conversation_id = int(self.current_conversation_id or 0)
        self.busy = True
        self.send_button.configure(state="disabled")
        prepared_attachments = attachments or []
        display = mode + (f" — {text}" if text else "") if mode else text
        if not display:
            display = "Uploaded file" if len(prepared_attachments) == 1 else "Uploaded files"
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
        )
        self._poll_future(
            future, lambda done: self._response_finished(done, conversation_id)
        )

    def _response_finished(self, future: Future[BrainResponse], conversation_id: int) -> None:
        if self.closing:
            return
        self.busy = False
        self.send_button.configure(state="normal")
        self._set_thinking("Enter to send · Shift+Enter for a new line")
        try:
            response = future.result()
        except Exception as exc:
            self.logger.exception("Background response failed")
            response = BrainResponse(f"I hit a safe error: {exc}", local_ai_available=False)
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
        self.search_status.configure(
            text=f"Search · {'Enabled' if current.internet_search_enabled else 'Disabled'}",
            fg=COLORS["good"] if current.internet_search_enabled else COLORS["muted"],
        )
        self.memory_status.configure(
            text=f"Memory · {'Enabled' if current.memory_enabled else 'Disabled'}",
            fg=COLORS["good"] if current.memory_enabled else COLORS["muted"],
        )
        self.ai_status.configure(text="Local AI · Checking", fg=COLORS["muted"])
        future = self.executor.submit(self.ollama.check, current.ollama_url)
        self._poll_future(future, self._status_finished)

    def _status_finished(self, future: Future[tuple[bool, list[str]]]) -> None:
        if self.closing:
            return
        try:
            online, models = future.result()
        except Exception:
            online, models = False, []
        text = "Local AI · Online" if online else "Local AI · Offline"
        if online and not models:
            text = "Local AI · No models"
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

        ttk.Button(search_row, text="Search", style="Angel.TButton", command=refresh).grid(row=0, column=1)
        ttk.Button(controls, text="Add Memory", style="Primary.TButton", command=add_memory).pack(side="left")
        ttk.Button(controls, text="Delete", style="Angel.TButton", command=delete_memory).pack(side="right")
        search_entry.bind("<Return>", lambda _event: refresh())
        refresh()

    def show_settings(self) -> None:
        current = self.settings.get()
        window = tk.Toplevel(self.root)
        window.title("Angel Settings")
        window.geometry("700x650")
        window.minsize(620, 580)
        window.configure(bg=COLORS["charcoal"])
        window.transient(self.root)
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=16, pady=16)
        local_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        user_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        angel_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        about_tab = tk.Frame(notebook, bg=COLORS["charcoal"], padx=18, pady=18)
        notebook.add(local_tab, text="Local AI")
        notebook.add(user_tab, text="User")
        notebook.add(angel_tab, text="Angel")
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

        labeled_entry(user_tab, "Display Name", variables["display_name"], 0)
        labeled_entry(user_tab, "City", variables["city"], 1)
        labeled_entry(user_tab, "State / Region", variables["region"], 2)
        labeled_entry(user_tab, "ZIP / Postal Code", variables["postal_code"], 3)
        tk.Label(user_tab, text="Location stays local unless it is needed in a web search query.", bg=COLORS["charcoal"], fg=COLORS["muted"], wraplength=520, justify="left").grid(row=8, column=0, sticky="w", pady=(14, 0))

        tk.Label(angel_tab, text="Response Style", bg=COLORS["charcoal"], fg=COLORS["muted"], anchor="w").pack(fill="x", pady=(4, 3))
        ttk.Combobox(angel_tab, textvariable=variables["response_style"], values=("Concise", "Balanced", "Detailed"), state="readonly", style="Angel.TCombobox").pack(fill="x", ipady=5)
        tk.Checkbutton(angel_tab, text="Enable Internet Search", variable=variables["internet_search_enabled"], bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).pack(anchor="w", pady=(18, 6))
        tk.Checkbutton(angel_tab, text="Enable Memory", variable=variables["memory_enabled"], bg=COLORS["charcoal"], fg=COLORS["white"], selectcolor=COLORS["panel_alt"], activebackground=COLORS["charcoal"], activeforeground=COLORS["white"]).pack(anchor="w", pady=6)
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
