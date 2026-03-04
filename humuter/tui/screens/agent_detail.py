"""Agent detail screen — view stats, deploy, configure, chat, delete."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual import work


class AgentDetailScreen(Screen):
    """Detailed view of a single agent with actions."""

    BINDINGS = [
        ("c", "chat_agent", "Chat"),
        ("t", "deploy_telegram", "Deploy TG"),
        ("e", "configure", "Configure"),
        ("k", "gen_key", "API Key"),
        ("backspace", "go_back", "Back"),
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, agent_id: str) -> None:
        super().__init__()
        self.agent_id = agent_id
        self._agent: dict = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Label(" AGENT DETAILS", classes="section-header"),
            Static("  Loading...", id="agent-info"),
            Horizontal(
                Button("Chat", id="btn-chat", classes="primary"),
                Button("Deploy Telegram", id="btn-deploy"),
                Button("Configure", id="btn-configure"),
                Button("Generate API Key", id="btn-apikey"),
                Button("Delete", id="btn-delete", classes="danger"),
            ),
            Static("", id="action-result"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.load_agent()

    @work(thread=True)
    def load_agent(self) -> None:
        from humuter import api
        try:
            agent = api.get_agent(self.agent_id)
        except Exception as e:
            self.app.call_from_thread(self._show_error, str(e))
            return
        self.app.call_from_thread(self._display, agent)

    def _display(self, agent: dict) -> None:
        self._agent = agent
        name = agent.get("name", "Unknown")
        self.sub_title = name

        tg = "connected" if agent.get("telegram_bot_token") else "not connected"
        dc = "connected" if agent.get("discord_server_id") else "not connected"
        status = agent.get("status", "—")
        status_fmt = f"[green]{status}[/green]" if status == "active" else f"[yellow]{status}[/yellow]"

        info = f"""
  [bold]{name}[/bold]

  ID:            [cyan]{agent.get('id', '—')}[/cyan]
  Type:          {agent.get('agent_type', '—')}
  Status:        {status_fmt}
  Plan:          {agent.get('plan', 'free')}
  Billing:       {agent.get('billing_mode', 'subscription')}
  LLM Provider:  {agent.get('llm_provider', 'anthropic')}
  Messages:      {agent.get('messages_handled', 0):,}
  Tokens Used:   {agent.get('tokens_used', 0):,}
  API Key:       {agent.get('api_key_prefix', 'none')}
  Telegram:      {tg}
  Discord:       {dc}
"""
        td = agent.get("training_data", {})
        if td:
            info += "\n  [bold]Training Data[/bold]\n"
            for k, v in td.items():
                info += f"  {k}: [dim]{str(v)[:60]}[/dim]\n"

        self.query_one("#agent-info", Static).update(info)

    def _show_error(self, msg: str) -> None:
        self.query_one("#agent-info", Static).update(f"  [red]{msg}[/red]")

    def _show_result(self, msg: str) -> None:
        self.query_one("#action-result", Static).update(f"\n  {msg}\n")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id
        if btn == "btn-chat":
            self.action_chat_agent()
        elif btn == "btn-deploy":
            self.action_deploy_telegram()
        elif btn == "btn-configure":
            self.action_configure()
        elif btn == "btn-apikey":
            self.gen_api_key()
        elif btn == "btn-delete":
            self.delete_agent()

    def action_chat_agent(self) -> None:
        from humuter.tui.screens.chat import ChatScreen
        self.app.push_screen(ChatScreen(self.agent_id))

    def action_deploy_telegram(self) -> None:
        from humuter.tui.screens.deploy import DeployScreen
        self.app.push_screen(DeployScreen(self.agent_id))

    def action_configure(self) -> None:
        from humuter.tui.screens.configure import ConfigureScreen
        self.app.push_screen(ConfigureScreen(self.agent_id, self._agent))

    @work(thread=True)
    def gen_api_key(self) -> None:
        from humuter import api
        try:
            result = api.generate_api_key(self.agent_id)
            key = result.get("api_key", "—")
            self.app.call_from_thread(
                self._show_result,
                f"[green]API Key generated:[/green] [yellow]{key}[/yellow]\n  [dim]Save this — it won't be shown again.[/dim]"
            )
        except Exception as e:
            self.app.call_from_thread(self._show_result, f"[red]{e}[/red]")

    @work(thread=True)
    def delete_agent(self) -> None:
        from humuter import api
        try:
            api.delete_agent(self.agent_id)
            self.app.call_from_thread(self._show_result, "[green]Agent deleted.[/green]")
            self.app.call_from_thread(self._go_back_after_delete)
        except Exception as e:
            self.app.call_from_thread(self._show_result, f"[red]{e}[/red]")

    def _go_back_after_delete(self) -> None:
        import asyncio
        self.set_timer(1.5, lambda: self.app.action_switch_screen("agents"))

    def action_go_back(self) -> None:
        self.app.pop_screen()
