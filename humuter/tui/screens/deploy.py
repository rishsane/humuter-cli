"""Deploy screen — connect agent to Telegram/Discord."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual.worker import work


class DeployScreen(Screen):
    """Deploy agent to a messaging channel."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, agent_id: str | None = None) -> None:
        super().__init__()
        self.agent_id = agent_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label(" DEPLOY TO TELEGRAM", classes="section-header"),
            Static(
                "\n  [bold]Steps:[/bold]\n"
                "  1. Open [cyan]@BotFather[/cyan] on Telegram\n"
                "  2. Send [cyan]/newbot[/cyan] and follow the prompts\n"
                "  3. Copy the bot token and paste it below\n"
            ),
            Label("  Bot Token", classes="form-label"),
            Input(placeholder="1234567890:ABCdefGhIJKlmNoPQRsTUVwxyz", id="inp-token", classes="form-group"),
            Button("Connect", id="btn-connect", classes="primary"),
            Static("", id="deploy-result"),
            Static(
                "\n  [dim]Discord deployment coming soon.[/dim]\n"
            ),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-connect":
            self.do_connect()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "inp-token":
            self.do_connect()

    @work(thread=True)
    def do_connect(self) -> None:
        token = self.query_one("#inp-token", Input).value.strip()
        if not token:
            self.app.call_from_thread(self._show_result, "[red]Bot token is required.[/red]")
            return
        if not self.agent_id:
            self.app.call_from_thread(self._show_result, "[red]No agent selected.[/red]")
            return

        self.app.call_from_thread(self._show_result, "[dim]Connecting...[/dim]")

        from humuter import api
        try:
            api.connect_telegram(self.agent_id, token)
            self.app.call_from_thread(
                self._show_result,
                "[green bold]Telegram connected![/green bold]\n  Your agent is now live. Send it a message on Telegram."
            )
        except Exception as e:
            self.app.call_from_thread(self._show_result, f"[red]{e}[/red]")

    def _show_result(self, msg: str) -> None:
        self.query_one("#deploy-result", Static).update(f"\n  {msg}\n")

    def action_go_back(self) -> None:
        self.app.pop_screen()
