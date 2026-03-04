"""Agent list screen — browse, select, and manage agents."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Static
from textual import work


class AgentListScreen(Screen):
    """Full agent list with row selection to view details."""

    BINDINGS = [
        ("n", "new_agent", "New Agent"),
        ("r", "refresh", "Refresh"),
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label(" AGENTS", classes="section-header"),
            Static("  [dim]Select an agent to view details. Press [bold]n[/bold] to create new.[/dim]"),
            DataTable(id="agents-table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#agents-table", DataTable)
        table.add_columns("ID", "Name", "Type", "Status", "Messages", "Tokens", "Plan", "Telegram")
        table.cursor_type = "row"
        self.load_agents()

    @work(thread=True)
    def load_agents(self) -> None:
        from humuter import api
        try:
            agents = api.list_agents()
        except Exception:
            agents = []
        self.app.call_from_thread(self._populate, agents)

    def _populate(self, agents: list) -> None:
        table = self.query_one("#agents-table", DataTable)
        table.clear()
        if not agents:
            return
        for a in agents:
            status = "active" if a.get("status") == "active" else a.get("status", "—")
            tg = "yes" if a.get("telegram_bot_token") else "no"
            table.add_row(
                a["id"][:12],
                a.get("name", "—"),
                a.get("agent_type", "—"),
                status,
                str(a.get("messages_handled", 0)),
                f"{a.get('tokens_used', 0):,}",
                a.get("plan", "free"),
                tg,
                key=a["id"],
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        agent_id = str(event.row_key.value)
        from humuter.tui.screens.agent_detail import AgentDetailScreen
        self.app.push_screen(AgentDetailScreen(agent_id))

    def action_new_agent(self) -> None:
        self.app.action_switch_screen("create")

    def action_refresh(self) -> None:
        self.load_agents()

    def action_go_back(self) -> None:
        self.app.action_switch_screen("dashboard")
