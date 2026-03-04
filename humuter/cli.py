"""Humuter CLI — Deploy AI agents from your terminal."""

import sys

import click
from rich.console import Console

from humuter import __version__

console = Console()

BANNER = """
[bold #ff8c00]  ██   ██ ██    ██ ███    ███ ██    ██ ████████ ███████ ██████[/bold #ff8c00]
[bold #ff8c00]  ██   ██ ██    ██ ████  ████ ██    ██    ██    ██      ██   ██[/bold #ff8c00]
[bold #ff8c00]  ███████ ██    ██ ██ ████ ██ ██    ██    ██    █████   ██████[/bold #ff8c00]
[bold #ff8c00]  ██   ██ ██    ██ ██  ██  ██ ██    ██    ██    ██      ██   ██[/bold #ff8c00]
[bold #ff8c00]  ██   ██  ██████  ██      ██  ██████     ██    ███████ ██   ██[/bold #ff8c00]
"""


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="humuter")
@click.pass_context
def main(ctx):
    """Deploy AI agents from your terminal."""
    if ctx.invoked_subcommand is None:
        # No subcommand — launch the TUI
        from humuter.config import load_credentials
        if not load_credentials():
            console.print(BANNER)
            console.print(f"  [dim]v{__version__}[/dim]\n")
            console.print("  [yellow]Not logged in.[/yellow] Run [cyan]humuter login[/cyan] first.\n")
            return
        from humuter.tui.app import HumuterApp
        app = HumuterApp()
        app.run()


@main.command()
def login():
    """Log in to your Humuter account via browser."""
    from humuter.auth import login as do_login
    console.print(BANNER)
    console.print(f"  [dim]v{__version__}[/dim]\n")
    do_login()


@main.command()
def logout():
    """Clear stored credentials."""
    from humuter.auth import logout as do_logout
    do_logout()


# Quick commands that bypass TUI for scripting / CI usage
@main.command(name="agents")
@click.argument("action", required=False)
@click.argument("agent_id", required=False)
def agents_cmd(action, agent_id):
    """Quick agent commands (list, status ID, delete ID)."""
    from humuter.config import load_credentials
    if not load_credentials():
        console.print("[red]Not logged in. Run:[/red] [cyan]humuter login[/cyan]")
        raise SystemExit(1)

    from humuter import api

    if action is None or action == "list":
        agents = api.list_agents()
        if not agents:
            console.print("No agents yet. Run [cyan]humuter[/cyan] to create one.\n")
            return
        for a in agents:
            status = "[green]active[/green]" if a["status"] == "active" else f"[yellow]{a['status']}[/yellow]"
            console.print(f"  {a['id'][:12]}  {a['name']:<25} {status}  {a.get('messages_handled', 0)} msgs")
        console.print()
    elif action == "status" and agent_id:
        agent = api.get_agent(agent_id)
        console.print(f"\n  [bold]{agent.get('name')}[/bold]")
        console.print(f"  ID:       {agent.get('id')}")
        console.print(f"  Status:   {agent.get('status')}")
        console.print(f"  Messages: {agent.get('messages_handled', 0)}")
        console.print(f"  Tokens:   {agent.get('tokens_used', 0):,}\n")
    elif action == "delete" and agent_id:
        if click.confirm(f"Delete agent {agent_id}?", default=False):
            api.delete_agent(agent_id)
            console.print("[green]Deleted.[/green]")
    else:
        console.print("Usage: humuter agents [list|status ID|delete ID]")


@main.command()
def credits():
    """Show credit balance."""
    from humuter.config import load_credentials
    if not load_credentials():
        console.print("[red]Not logged in. Run:[/red] [cyan]humuter login[/cyan]")
        raise SystemExit(1)
    from humuter import api
    stats = api.get_platform_stats()
    bal = stats.get("balance", 0) / 1_000_000
    console.print(f"\n  Balance: [green bold]${bal:.2f}[/green bold]\n")


if __name__ == "__main__":
    main()
