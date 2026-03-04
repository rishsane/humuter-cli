"""Create agent screen — multi-step wizard form."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static
from textual.worker import work


AGENT_TYPES = [
    ("community_manager", "Community Manager"),
    ("community_analyst", "Community Analyst"),
    ("customer_service", "Customer Service"),
    ("protocol_onboarding", "Protocol Onboarding"),
    ("other", "Custom Agent"),
]

LLM_PROVIDERS = [
    ("anthropic", "Anthropic (Claude)"),
    ("openai", "OpenAI (GPT-4o)"),
]

BILLING_MODES = [
    ("credits", "Pay-as-you-go Credits"),
    ("subscription", "Subscription"),
]


class CreateAgentScreen(Screen):
    """Interactive agent creation wizard."""

    BINDINGS = [
        ("escape", "go_back", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label(" CREATE NEW AGENT", classes="section-header"),
            Static("  [dim]Fill in the details below. All training fields are optional.[/dim]\n"),

            # Basic info
            Label("  Agent Name *", classes="form-label"),
            Input(placeholder="My Support Bot", id="inp-name", classes="form-group"),

            Label("  Agent Type", classes="form-label"),
            Select(
                [(desc, type_id) for type_id, desc in AGENT_TYPES],
                value="community_manager",
                id="sel-type",
                classes="form-group",
            ),

            Label("  LLM Provider", classes="form-label"),
            Select(
                [(desc, pid) for pid, desc in LLM_PROVIDERS],
                value="anthropic",
                id="sel-llm",
                classes="form-group",
            ),

            Label("  Billing", classes="form-label"),
            Select(
                [(desc, bid) for bid, desc in BILLING_MODES],
                value="credits",
                id="sel-billing",
                classes="form-group",
            ),

            # Training data
            Static("\n  [bold #ff8c00]Training Data[/bold #ff8c00] [dim](optional — you can edit later)[/dim]\n"),

            Label("  Project Name", classes="form-label"),
            Input(placeholder="Acme Protocol", id="inp-project", classes="form-group"),

            Label("  Project Description", classes="form-label"),
            Input(placeholder="A DeFi lending protocol on Ethereum", id="inp-desc", classes="form-group"),

            Label("  Communication Tone", classes="form-label"),
            Input(placeholder="professional, friendly, casual", id="inp-tone", classes="form-group"),

            Label("  Key Topics (comma-separated)", classes="form-label"),
            Input(placeholder="staking, governance, tokenomics", id="inp-topics", classes="form-group"),

            Label("  Website URL", classes="form-label"),
            Input(placeholder="https://example.com", id="inp-website", classes="form-group"),

            Static(""),
            Horizontal(
                Button("Create Agent", id="btn-create", classes="primary"),
                Button("Cancel", id="btn-cancel"),
            ),
            Static("", id="create-result"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            self.do_create()
        elif event.button.id == "btn-cancel":
            self.action_go_back()

    @work(thread=True)
    def do_create(self) -> None:
        name = self.query_one("#inp-name", Input).value.strip()
        if not name:
            self.app.call_from_thread(self._show_result, "[red]Agent name is required.[/red]")
            return

        agent_type = self.query_one("#sel-type", Select).value
        llm_provider = self.query_one("#sel-llm", Select).value
        billing = self.query_one("#sel-billing", Select).value

        training_data = {}
        for field, inp_id in [
            ("project_name", "#inp-project"),
            ("project_description", "#inp-desc"),
            ("tone", "#inp-tone"),
            ("key_topics", "#inp-topics"),
            ("website_url", "#inp-website"),
        ]:
            val = self.query_one(inp_id, Input).value.strip()
            if val:
                training_data[field] = val

        self.app.call_from_thread(self._show_result, "[dim]Creating agent...[/dim]")

        from humuter import api
        try:
            result = api.create_agent({
                "name": name,
                "agent_type": agent_type,
                "plan": "free",
                "training_data": training_data,
            })
            agent = result.get("agent", {})
            api_key = result.get("apiKey")
            agent_id = agent.get("id", "")

            # Set billing + LLM
            try:
                api.update_agent(agent_id, {
                    "billing_mode": billing,
                    "llm_provider": llm_provider,
                })
            except Exception:
                pass

            msg = f"[green bold]Agent created![/green bold]\n\n"
            msg += f"  ID:   [cyan]{agent_id}[/cyan]\n"
            msg += f"  Name: {agent.get('name', '—')}\n"
            if api_key:
                msg += f"\n  API Key: [yellow]{api_key}[/yellow]\n"
                msg += "  [dim]Save this key — it won't be shown again.[/dim]\n"
            msg += "\n  [dim]Press [bold]escape[/bold] to go back, then select the agent to deploy.[/dim]"
            self.app.call_from_thread(self._show_result, msg)

        except Exception as e:
            self.app.call_from_thread(self._show_result, f"[red]{e}[/red]")

    def _show_result(self, msg: str) -> None:
        self.query_one("#create-result", Static).update(f"\n  {msg}\n")

    def action_go_back(self) -> None:
        self.app.action_switch_screen("dashboard")
