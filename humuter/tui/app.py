"""Main Textual TUI application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from humuter.tui.screens.dashboard import DashboardScreen
from humuter.tui.screens.agents import AgentListScreen
from humuter.tui.screens.create_agent import CreateAgentScreen
from humuter.tui.screens.credits import CreditsScreen
from humuter.tui.screens.chat import ChatScreen
from humuter.tui.screens.deploy import DeployScreen


class HumuterApp(App):
    """Humuter — Deploy AI agents from your terminal."""

    TITLE = "Humuter"
    CSS_PATH = "theme.tcss"

    BINDINGS = [
        Binding("d", "switch_screen('dashboard')", "Dashboard", show=True),
        Binding("a", "switch_screen('agents')", "Agents", show=True),
        Binding("n", "switch_screen('create')", "New Agent", show=True),
        Binding("b", "switch_screen('credits')", "Billing", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "agents": AgentListScreen,
        "create": CreateAgentScreen,
        "credits": CreditsScreen,
        "chat": ChatScreen,
        "deploy": DeployScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("dashboard")

    def action_switch_screen(self, screen_name: str) -> None:
        """Switch to a named screen, replacing current."""
        # Pop all screens back to default, then push requested
        while len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(screen_name)
