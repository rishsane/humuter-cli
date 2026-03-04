"""Chat screen — live conversation with an agent."""

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual import work


class ChatScreen(Screen):
    """Interactive chat with an agent via API."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, agent_id: str | None = None) -> None:
        super().__init__()
        self.agent_id = agent_id
        self._api_key: str | None = None
        self._messages: list[tuple[str, str]] = []  # (role, text)

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label(" CHAT", classes="section-header"),
            Static("", id="chat-status"),
            Static("", id="chat-log"),
        )
        yield Horizontal(
            Input(placeholder="Type a message...", id="chat-input"),
            Button("Send", id="chat-send", classes="primary"),
            id="chat-input-row",
        )
        yield Footer()

    def on_mount(self) -> None:
        if self.agent_id:
            self.resolve_key()
        else:
            self.query_one("#chat-status", Static).update(
                "  [yellow]No agent selected. Go to Agents and select one.[/yellow]"
            )

    @work(thread=True)
    def resolve_key(self) -> None:
        """Try to find or generate an API key for this agent."""
        from humuter import api
        try:
            keys = api.list_api_keys()
            agent_key = next((k for k in keys if k.get("agent_id") == self.agent_id), None)
            if agent_key and agent_key.get("key"):
                self._api_key = agent_key["key"]
                self.app.call_from_thread(self._set_status, f"  [dim]Connected to agent {self.agent_id[:12]}[/dim]")
            else:
                # Generate a new key
                result = api.generate_api_key(self.agent_id)
                self._api_key = result.get("api_key")
                self.app.call_from_thread(
                    self._set_status,
                    f"  [dim]Connected. Key: [yellow]{self._api_key}[/yellow] (save this)[/dim]"
                )
        except Exception as e:
            self.app.call_from_thread(
                self._set_status,
                f"  [yellow]Could not auto-resolve key. Enter your API key (hmt_...) as the first message.[/yellow]"
            )

    def _set_status(self, msg: str) -> None:
        self.query_one("#chat-status", Static).update(msg)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "chat-send":
            self.send_message()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            self.send_message()

    def send_message(self) -> None:
        inp = self.query_one("#chat-input", Input)
        text = inp.value.strip()
        if not text:
            return
        inp.value = ""

        # If no API key yet, treat first message as the key
        if not self._api_key and text.startswith("hmt_"):
            self._api_key = text
            self._set_status(f"  [dim]API key set. You can now chat.[/dim]")
            return

        if not self._api_key:
            self._set_status("  [red]No API key. Enter your key (hmt_...) first.[/red]")
            return

        self._messages.append(("you", text))
        self._render_log()
        self.do_chat(text)

    @work(thread=True)
    def do_chat(self, message: str) -> None:
        from humuter import api
        try:
            result = api.chat(self._api_key, message)
            reply = result.get("reply", result.get("text", ""))
            if isinstance(reply, dict):
                reply = reply.get("text", str(reply))
            tokens = result.get("tokens_used", 0)
            suffix = f" [dim]({tokens:,} tokens)[/dim]" if tokens else ""
            self._messages.append(("agent", f"{reply}{suffix}"))
        except Exception as e:
            self._messages.append(("error", str(e)))
        self.app.call_from_thread(self._render_log)

    def _render_log(self) -> None:
        lines = []
        for role, text in self._messages:
            if role == "you":
                lines.append(f"  [bold]You:[/bold] {text}")
            elif role == "agent":
                lines.append(f"  [bold cyan]Agent:[/bold cyan] {text}")
            else:
                lines.append(f"  [red]{text}[/red]")
            lines.append("")
        self.query_one("#chat-log", Static).update("\n".join(lines))

    def action_go_back(self) -> None:
        self.app.pop_screen()
