"""Dashboard screen — overview with stats, agents, and usage chart."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Static
from textual import work

try:
    from textual_plotext import PlotextPlot
    HAS_PLOTEXT = True
except ImportError:
    HAS_PLOTEXT = False


class DashboardScreen(Screen):
    """Main dashboard with credits, usage stats, chart, and agent overview."""

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static(BANNER, classes="banner"),
            Static("Deploy AI agents from your terminal", classes="subtitle"),
            Horizontal(
                Vertical(
                    Label("CREDIT BALANCE", classes="stat-label"),
                    Label("—", id="balance-value", classes="stat-value-green"),
                    classes="stat-card",
                ),
                Vertical(
                    Label("MONTHLY SPEND", classes="stat-label"),
                    Label("—", id="spend-value", classes="stat-value"),
                    classes="stat-card",
                ),
                Vertical(
                    Label("REQUESTS", classes="stat-label"),
                    Label("—", id="requests-value", classes="stat-value"),
                    classes="stat-card",
                ),
                Vertical(
                    Label("TOKENS USED", classes="stat-label"),
                    Label("—", id="tokens-value", classes="stat-value"),
                    classes="stat-card",
                ),
                classes="stats-row",
            ),
            *(
                [PlotextPlot(id="usage-chart")]
                if HAS_PLOTEXT
                else [Static("  [dim]Install textual-plotext for usage charts[/dim]")]
            ),
            Label(" YOUR AGENTS", classes="section-header"),
            Static("  [dim]Select an agent to view details  ·  Press [bold]n[/bold] to create new[/dim]"),
            DataTable(id="agents-table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#agents-table", DataTable)
        table.add_columns("ID", "Name", "Type", "Status", "Messages", "Plan")
        table.cursor_type = "row"
        self.load_data()

    @work(thread=True)
    def load_data(self) -> None:
        from humuter import api
        try:
            stats = api.get_platform_stats()
        except Exception:
            stats = {}
        try:
            agents = api.list_agents()
        except Exception:
            agents = []
        self.app.call_from_thread(self._update_ui, stats, agents)

    def _update_ui(self, stats: dict, agents: list) -> None:
        bal = stats.get("balance", 0) / 1_000_000
        month = stats.get("month", {})
        spend = month.get("spent", 0) / 1_000_000
        requests = month.get("requests", 0)
        input_tok = month.get("input_tokens", 0)
        output_tok = month.get("output_tokens", 0)
        tokens = input_tok + output_tok

        self.query_one("#balance-value", Label).update(f"${bal:.2f}")
        self.query_one("#spend-value", Label).update(f"${spend:.4f}")
        self.query_one("#requests-value", Label).update(f"{requests:,}")
        self.query_one("#tokens-value", Label).update(f"{tokens:,}")

        # Update chart if available
        if HAS_PLOTEXT:
            try:
                chart = self.query_one("#usage-chart", PlotextPlot)
                plt = chart.plt
                plt.clear_data()
                plt.clear_figure()
                plt.theme("dark")
                plt.title("Token Usage")
                plt.xlabel("Category")

                categories = ["Input", "Output"]
                values = [input_tok, output_tok]
                plt.bar(categories, values, color=[255, 140, 0])

                chart.refresh()
            except Exception:
                pass

        table = self.query_one("#agents-table", DataTable)
        table.clear()
        if not agents:
            return
        for a in agents:
            status = "active" if a.get("status") == "active" else a.get("status", "—")
            table.add_row(
                a["id"][:12],
                a.get("name", "—"),
                a.get("agent_type", "—"),
                status,
                str(a.get("messages_handled", 0)),
                a.get("plan", "free"),
                key=a["id"],
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        agent_id = str(event.row_key.value)
        from humuter.tui.screens.agent_detail import AgentDetailScreen
        self.app.push_screen(AgentDetailScreen(agent_id))

    def action_refresh(self) -> None:
        self.load_data()


BANNER = """\
  ██   ██ ██    ██ ███    ███ ██    ██ ████████ ███████ ██████
  ██   ██ ██    ██ ████  ████ ██    ██    ██    ██      ██   ██
  ███████ ██    ██ ██ ████ ██ ██    ██    ██    █████   ██████
  ██   ██ ██    ██ ██  ██  ██ ██    ██    ██    ██      ██   ██
  ██   ██  ██████  ██      ██  ██████     ██    ███████ ██   ██\
"""
