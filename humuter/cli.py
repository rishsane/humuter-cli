"""Humuter CLI — Deploy AI agents from your terminal."""

import click
from rich.console import Console

from humuter import __version__

console = Console()

# Exact brand orange
ORANGE = "#ff8c00"

BANNER = f"""\
[bold {ORANGE}]  ██   ██ ██    ██ ███    ███ ██    ██ ████████ ███████ ██████[/]
[bold {ORANGE}]  ██   ██ ██    ██ ████  ████ ██    ██    ██    ██      ██   ██[/]
[bold {ORANGE}]  ███████ ██    ██ ██ ████ ██ ██    ██    ██    █████   ██████[/]
[bold {ORANGE}]  ██   ██ ██    ██ ██  ██  ██ ██    ██    ██    ██      ██   ██[/]
[bold {ORANGE}]  ██   ██  ██████  ██      ██  ██████     ██    ███████ ██   ██[/]"""


def show_welcome():
    """Show the welcome banner."""
    console.print(BANNER)
    console.print(f"  [dim]v{__version__}[/dim]\n")


def show_post_login():
    """Show what to do after successful login."""
    console.print(f"\n  [green bold]Logged in successfully![/green bold]\n")
    console.print(f"  [{ORANGE} bold]What's next?[/]")
    console.print(f"  Run [{ORANGE} bold]humuter[/] to launch the interactive dashboard.\n")
    console.print(f"  ┌{'─' * 50}┐")
    console.print(f"  │  [{ORANGE}]humuter[/]        Launch dashboard              │")
    console.print(f"  └{'─' * 50}┘\n")
    console.print(f"  [bold]Dashboard shortcuts:[/bold]")
    console.print(f"    [{ORANGE}]d[/]  Dashboard     [{ORANGE}]a[/]  Agents      [{ORANGE}]n[/]  New Agent")
    console.print(f"    [{ORANGE}]b[/]  Billing       [{ORANGE}]c[/]  Chat        [{ORANGE}]q[/]  Quit")
    console.print()
    console.print(f"  [bold]Quick commands (skip dashboard):[/bold]")
    console.print(f"    [{ORANGE}]humuter agents list[/]        List all agents")
    console.print(f"    [{ORANGE}]humuter agents status ID[/]   Agent details")
    console.print(f"    [{ORANGE}]humuter credits[/]            Check balance")
    console.print()


def show_not_logged_in():
    """Show the not-logged-in screen with clear instructions."""
    show_welcome()
    console.print(f"  [yellow]Not logged in yet.[/yellow]\n")
    console.print(f"  ┌{'─' * 50}┐")
    console.print(f"  │  [{ORANGE}]humuter login[/]  Sign in via browser           │")
    console.print(f"  └{'─' * 50}┘\n")


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="humuter")
@click.pass_context
def main(ctx):
    """Deploy AI agents from your terminal."""
    if ctx.invoked_subcommand is None:
        from humuter.config import load_credentials
        if not load_credentials():
            show_not_logged_in()
            return
        from humuter.tui.app import HumuterApp
        app = HumuterApp()
        app.run()


@main.command()
def login():
    """Log in to your Humuter account via browser."""
    from humuter.auth import login as do_login
    show_welcome()
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
        console.print(f"[red]Not logged in.[/red] Run [{ORANGE}]humuter login[/] first.")
        raise SystemExit(1)

    from humuter import api

    if action is None or action == "list":
        agents = api.list_agents()
        if not agents:
            console.print(f"No agents yet. Run [{ORANGE}]humuter[/] to create one.\n")
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
        console.print(f"Usage: [{ORANGE}]humuter agents[/] [list|status ID|delete ID]")


@main.command()
def credits():
    """Show credit balance."""
    from humuter.config import load_credentials
    if not load_credentials():
        console.print(f"[red]Not logged in.[/red] Run [{ORANGE}]humuter login[/] first.")
        raise SystemExit(1)
    from humuter import api
    stats = api.get_platform_stats()
    bal = stats.get("balance", 0) / 1_000_000
    console.print(f"\n  Balance: [green bold]${bal:.2f}[/green bold]\n")


if __name__ == "__main__":
    main()
