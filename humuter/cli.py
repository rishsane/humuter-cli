"""Humuter CLI — Deploy AI agents from your terminal."""

import click
from rich.console import Console

from humuter import __version__

console = Console()

BANNER = """
[bold orange1]  ██   ██ ██    ██ ███    ███ ██    ██ ████████ ███████ ██████[/bold orange1]
[bold orange1]  ██   ██ ██    ██ ████  ████ ██    ██    ██    ██      ██   ██[/bold orange1]
[bold orange1]  ███████ ██    ██ ██ ████ ██ ██    ██    ██    █████   ██████[/bold orange1]
[bold orange1]  ██   ██ ██    ██ ██  ██  ██ ██    ██    ██    ██      ██   ██[/bold orange1]
[bold orange1]  ██   ██  ██████  ██      ██  ██████     ██    ███████ ██   ██[/bold orange1]
"""


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="humuter")
@click.pass_context
def main(ctx):
    """Deploy AI agents from your terminal."""
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        console.print(f"  [dim]v{__version__}[/dim]\n")
        console.print("  [bold]Commands:[/bold]")
        console.print("    [cyan]humuter login[/cyan]                Log in to your account")
        console.print("    [cyan]humuter agents list[/cyan]          List your agents")
        console.print("    [cyan]humuter agents create[/cyan]        Create a new agent")
        console.print("    [cyan]humuter agents deploy ID[/cyan]     Deploy to Telegram/Discord")
        console.print("    [cyan]humuter agents status ID[/cyan]     Show agent details")
        console.print("    [cyan]humuter agents configure ID[/cyan]  Edit training data")
        console.print("    [cyan]humuter credits balance[/cyan]      Check credit balance")
        console.print("    [cyan]humuter credits usage[/cyan]        Usage breakdown")
        console.print("    [cyan]humuter chat ID \"message\"[/cyan]    Chat with your agent")
        console.print("    [cyan]humuter config set-key[/cyan]       Set BYOK API key")
        console.print()
        console.print("  [dim]Run any command with --help for details.[/dim]\n")


# --- Auth ---

@main.command()
def login():
    """Log in to your Humuter account via browser."""
    from humuter.auth import login as do_login
    do_login()


@main.command()
def logout():
    """Clear stored credentials."""
    from humuter.auth import logout as do_logout
    do_logout()


# --- Agents ---

@main.group(invoke_without_command=True)
@click.pass_context
def agents(ctx):
    """Manage your agents."""
    if ctx.invoked_subcommand is None:
        console.print("Usage: [cyan]humuter agents <command>[/cyan]\n")
        console.print("  [cyan]list[/cyan]           List all agents")
        console.print("  [cyan]create[/cyan]         Create a new agent")
        console.print("  [cyan]deploy ID[/cyan]      Deploy agent to a channel")
        console.print("  [cyan]status ID[/cyan]      Show agent details")
        console.print("  [cyan]configure ID[/cyan]   Edit training data")
        console.print("  [cyan]delete ID[/cyan]      Delete an agent")
        console.print()


@agents.command(name="list")
def agents_list():
    """List all your agents."""
    from humuter.agents import list_agents
    list_agents()


@agents.command(name="create")
def agents_create():
    """Create a new agent interactively."""
    from humuter.agents import create_agent
    create_agent()


@agents.command(name="deploy")
@click.argument("agent_id")
def agents_deploy(agent_id):
    """Deploy an agent to Telegram or Discord."""
    from humuter.agents import deploy_agent
    deploy_agent(agent_id)


@agents.command(name="status")
@click.argument("agent_id")
def agents_status(agent_id):
    """Show agent details and stats."""
    from humuter.agents import status_agent
    status_agent(agent_id)


@agents.command(name="configure")
@click.argument("agent_id")
def agents_configure(agent_id):
    """Edit agent training data."""
    from humuter.agents import configure_agent
    configure_agent(agent_id)


@agents.command(name="delete")
@click.argument("agent_id")
def agents_delete(agent_id):
    """Delete an agent."""
    from humuter.agents import require_auth
    require_auth()
    if click.confirm(f"Delete agent {agent_id}? This cannot be undone.", default=False):
        try:
            from humuter import api
            api.delete_agent(agent_id)
            console.print("[green]Agent deleted.[/green]")
        except Exception as e:
            console.print(f"[red]{e}[/red]")


# --- Credits ---

@main.group(invoke_without_command=True)
@click.pass_context
def credits(ctx):
    """Manage credits and usage."""
    if ctx.invoked_subcommand is None:
        from humuter.credits import balance
        balance()


@credits.command(name="balance")
def credits_balance():
    """Show your credit balance."""
    from humuter.credits import balance
    balance()


@credits.command(name="usage")
def credits_usage():
    """Show detailed usage breakdown."""
    from humuter.credits import usage
    usage()


@credits.command(name="topup")
def credits_topup():
    """Open browser to top up credits."""
    import webbrowser
    from humuter.config import API_BASE
    webbrowser.open(f"{API_BASE}/platform/dashboard/billing")
    console.print("Opened billing page in your browser.\n")


# --- Chat ---

@main.command()
@click.argument("agent_id")
@click.argument("message")
def chat(agent_id, message):
    """Send a message to your agent via API."""
    from humuter.agents import require_auth
    require_auth()

    # Get the agent's API key
    try:
        from humuter import api as hapi
        keys = hapi.list_api_keys()
        agent_key = next((k for k in keys if k["agent_id"] == agent_id), None)

        if not agent_key:
            console.print("[yellow]No API key found for this agent. Generating one...[/yellow]")
            result = hapi.generate_api_key(agent_id)
            api_key = result["api_key"]
            console.print(f"  API Key: [yellow]{api_key}[/yellow]")
            console.print("  [dim]Save this — it won't be shown again.[/dim]\n")
        else:
            # We only have the prefix, need the user to provide the full key
            console.print(f"[dim]Using key: {agent_key['prefix']}[/dim]")
            api_key = click.prompt("Paste your full API key (hmt_...)")

        console.print(f"\n[dim]You:[/dim] {message}")
        console.print("[dim]...[/dim]")

        result = hapi.chat(api_key, message)
        reply = result.get("reply", result.get("text", ""))
        if isinstance(reply, dict):
            reply = reply.get("text", str(reply))
        console.print(f"\n[bold cyan]Agent:[/bold cyan] {reply}\n")

        tokens = result.get("tokens_used", 0)
        if tokens:
            console.print(f"[dim]({tokens:,} tokens used)[/dim]\n")
    except Exception as e:
        console.print(f"[red]{e}[/red]")


# --- Config ---

@main.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """CLI configuration."""
    if ctx.invoked_subcommand is None:
        from humuter.config import load_config, load_credentials
        creds = load_credentials()
        conf = load_config()
        console.print("\n[bold]Configuration[/bold]\n")
        console.print(f"  Logged in:  {'[green]yes[/green]' if creds else '[red]no[/red]'}")
        if creds:
            console.print(f"  User ID:    [dim]{creds.get('user_id', '—')}[/dim]")
        console.print(f"  API URL:    [dim]{conf.get('api_url', 'https://humuter.com')}[/dim]")
        console.print()


@config.command(name="set-key")
@click.argument("provider", type=click.Choice(["openai", "anthropic"]))
@click.argument("api_key")
def config_set_key(provider, api_key):
    """Set a BYOK API key (applied to all agents).

    Example: humuter config set-key openai sk-...
    """
    from humuter.agents import require_auth
    require_auth()

    try:
        from humuter import api as hapi
        agents = hapi.list_agents()
        if not agents:
            console.print("[yellow]No agents yet. Key will be applied when you create one.[/yellow]")
            return

        field = f"custom_{provider}_key"
        for agent in agents:
            hapi.update_agent(agent["id"], {field: api_key})

        console.print(f"[green]{provider.title()} key set for {len(agents)} agent(s).[/green]\n")
    except Exception as e:
        console.print(f"[red]{e}[/red]")


if __name__ == "__main__":
    main()
