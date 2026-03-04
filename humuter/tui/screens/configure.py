"""Configure agent screen — edit training data."""

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual import work


class ConfigureScreen(Screen):
    """Edit agent training data."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, agent_id: str, agent: dict) -> None:
        super().__init__()
        self.agent_id = agent_id
        self._agent = agent
        self._td = agent.get("training_data", {})

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label(f" CONFIGURE: {self._agent.get('name', 'Agent')}", classes="section-header"),
            Static("  [dim]Edit training data. Leave blank to keep current value.[/dim]\n"),

            Label("  Project Name", classes="form-label"),
            Input(
                value=self._td.get("project_name", ""),
                placeholder="Project name",
                id="inp-project",
                classes="form-group",
            ),

            Label("  Project Description", classes="form-label"),
            Input(
                value=self._td.get("project_description", ""),
                placeholder="Description",
                id="inp-desc",
                classes="form-group",
            ),

            Label("  Communication Tone", classes="form-label"),
            Input(
                value=self._td.get("tone", ""),
                placeholder="professional, friendly, etc.",
                id="inp-tone",
                classes="form-group",
            ),

            Label("  Key Topics", classes="form-label"),
            Input(
                value=self._td.get("key_topics", ""),
                placeholder="topic1, topic2",
                id="inp-topics",
                classes="form-group",
            ),

            Label("  Website URL", classes="form-label"),
            Input(
                value=self._td.get("website_url", ""),
                placeholder="https://...",
                id="inp-website",
                classes="form-group",
            ),

            Label("  FAQ (one per line, format: Q: ... | A: ...)", classes="form-label"),
            Input(
                value=self._td.get("faq_items", ""),
                placeholder="Q: What is this? | A: An AI agent platform",
                id="inp-faq",
                classes="form-group",
            ),

            Static(""),
            Horizontal(
                Button("Save", id="btn-save", classes="primary"),
                Button("Cancel", id="btn-cancel"),
            ),
            Static("", id="config-result"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.do_save()
        elif event.button.id == "btn-cancel":
            self.action_go_back()

    @work(thread=True)
    def do_save(self) -> None:
        new_td = dict(self._td)
        changed = False

        for field, inp_id in [
            ("project_name", "#inp-project"),
            ("project_description", "#inp-desc"),
            ("tone", "#inp-tone"),
            ("key_topics", "#inp-topics"),
            ("website_url", "#inp-website"),
            ("faq_items", "#inp-faq"),
        ]:
            val = self.query_one(inp_id, Input).value.strip()
            if val != self._td.get(field, ""):
                new_td[field] = val
                changed = True

        if not changed:
            self.app.call_from_thread(self._show_result, "[dim]No changes.[/dim]")
            return

        self.app.call_from_thread(self._show_result, "[dim]Saving...[/dim]")

        from humuter import api
        try:
            api.update_agent(self.agent_id, {"training_data": new_td})
            self.app.call_from_thread(self._show_result, "[green]Updated![/green]")
        except Exception as e:
            self.app.call_from_thread(self._show_result, f"[red]{e}[/red]")

    def _show_result(self, msg: str) -> None:
        self.query_one("#config-result", Static).update(f"\n  {msg}\n")

    def action_go_back(self) -> None:
        self.app.pop_screen()
