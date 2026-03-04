"""Credits and billing screen."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Static
from textual import work


class CreditsScreen(Screen):
    """Credit balance, usage breakdown, and per-agent costs."""

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("t", "topup", "Top Up"),
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label(" BILLING & CREDITS", classes="section-header"),

            Horizontal(
                Vertical(
                    Label("BALANCE", classes="stat-label"),
                    Label("loading...", id="bal-value", classes="stat-value-green"),
                    classes="stat-card",
                ),
                Vertical(
                    Label("MONTHLY SPEND", classes="stat-label"),
                    Label("loading...", id="spend-value", classes="stat-value"),
                    classes="stat-card",
                ),
                Vertical(
                    Label("REQUESTS", classes="stat-label"),
                    Label("loading...", id="req-value", classes="stat-value"),
                    classes="stat-card",
                ),
                classes="stats-row",
            ),

            Static("\n  [bold]Token Breakdown[/bold]"),
            Static("  loading...", id="token-info"),

            Label("\n USAGE BY AGENT", classes="section-header"),
            DataTable(id="agent-usage-table"),

            Static("\n  [dim]Press [bold]t[/bold] to top up credits in your browser.[/dim]\n"),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#agent-usage-table", DataTable)
        table.add_columns("Agent", "Requests", "Cost")
        self.load_data()

    @work(thread=True)
    def load_data(self) -> None:
        from humuter import api
        try:
            stats = api.get_platform_stats()
        except Exception:
            stats = {}
        self.app.call_from_thread(self._update, stats)

    def _update(self, stats: dict) -> None:
        bal = stats.get("balance", 0) / 1_000_000
        month = stats.get("month", {})
        spend = month.get("spent", 0) / 1_000_000
        requests = month.get("requests", 0)
        input_tok = month.get("input_tokens", 0)
        output_tok = month.get("output_tokens", 0)

        self.query_one("#bal-value", Label).update(f"${bal:.2f}")
        self.query_one("#spend-value", Label).update(f"${spend:.4f}")
        self.query_one("#req-value", Label).update(f"{requests:,}")

        self.query_one("#token-info", Static).update(
            f"  Input tokens:  {input_tok:,}\n"
            f"  Output tokens: {output_tok:,}\n"
            f"  Total:         {input_tok + output_tok:,}"
        )

        table = self.query_one("#agent-usage-table", DataTable)
        table.clear()
        for a in stats.get("agent_breakdown", []):
            table.add_row(
                a.get("agent_name", "—"),
                str(a.get("requests", 0)),
                f"${a.get('cost_micro_credits', 0) / 1_000_000:.4f}",
            )

    def action_refresh(self) -> None:
        self.load_data()

    def action_topup(self) -> None:
        import webbrowser
        from humuter.config import API_BASE
        webbrowser.open(f"{API_BASE}/platform/dashboard/billing")

    def action_go_back(self) -> None:
        self.app.action_switch_screen("dashboard")
