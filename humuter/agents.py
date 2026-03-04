"""Agent management commands."""

import click
from rich.console import Console
from rich.table import Table

from humuter import api
from humuter.config import load_credentials

console = Console()

AGENT_TYPES = [
    ("community_manager", "Community Manager — Moderates and answers questions"),
    ("community_analyst", "Community Analyst — Silent listening and analytics"),
    ("customer_service", "Customer Service — Helps users resolve issues"),
    ("protocol_onboarding", "Protocol Onboarding — Sales and lead qualification"),
    ("other", "Custom Agent — Define your own role"),
]


def require_auth():
    if not load_credentials():
        console.print("[red]Not logged in. Run:[/red] [cyan]humuter login[/cyan]")
        raise SystemExit(1)


def list_agents():
    require_auth()
    try:
        agents = api.list_agents()
    except api.ApiError as e:
        console.print(f"[red]{e.message}[/red]")
        return

    if not agents:
        console.print("No agents yet. Create one with [cyan]humuter agents create[/cyan]\n")
        return

    table = Table(title="Your Agents", show_edge=False, pad_edge=False)
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Plan")
    table.add_column("Messages")
    table.add_column("API Key")

    for a in agents:
        status_style = "green" if a["status"] == "active" else "yellow"
        table.add_row(
            a["id"][:12] + "...",
            a["name"],
            a.get("agent_type", "—"),
            f"[{status_style}]{a['status']}[/{status_style}]",
            a.get("plan", "—"),
            str(a.get("messages_handled", 0)),
            a.get("api_key_prefix", "—"),
        )

    console.print(table)
    console.print()


def create_agent():
    require_auth()
    console.print("\n[bold]Create a new agent[/bold]\n")

    # Agent name
    name = click.prompt("Agent name", type=str)

    # Agent type
    console.print("\nAgent types:")
    for i, (type_id, desc) in enumerate(AGENT_TYPES, 1):
        console.print(f"  [cyan]{i}[/cyan]. {desc}")
    type_choice = click.prompt("\nSelect type", type=int, default=1)
    if type_choice < 1 or type_choice > len(AGENT_TYPES):
        type_choice = 1
    agent_type = AGENT_TYPES[type_choice - 1][0]

    # Billing mode
    console.print("\nBilling:")
    console.print("  [cyan]1[/cyan]. Credits (pay-as-you-go)")
    console.print("  [cyan]2[/cyan]. Subscription")
    billing_choice = click.prompt("Select billing", type=int, default=1)
    billing_mode = "credits" if billing_choice == 1 else "subscription"
    plan = "free" if billing_mode == "subscription" else "free"

    # Training data
    console.print("\n[bold]Training data[/bold] (press Enter to skip any field)\n")
    project_name = click.prompt("Project name", default="", show_default=False)
    project_description = click.prompt("Project description", default="", show_default=False)
    tone = click.prompt("Communication tone (e.g. professional, casual, friendly)", default="", show_default=False)
    key_topics = click.prompt("Key topics (comma-separated)", default="", show_default=False)
    website_url = click.prompt("Website URL", default="", show_default=False)

    training_data = {}
    if project_name:
        training_data["project_name"] = project_name
    if project_description:
        training_data["project_description"] = project_description
    if tone:
        training_data["tone"] = tone
    if key_topics:
        training_data["key_topics"] = key_topics
    if website_url:
        training_data["website_url"] = website_url

    # FAQ
    if click.confirm("\nAdd FAQ entries?", default=False):
        faq_items = []
        while True:
            q = click.prompt("  Q", default="", show_default=False)
            if not q:
                break
            a = click.prompt("  A", default="", show_default=False)
            if a:
                faq_items.append(f"Q: {q}\nA: {a}")
        if faq_items:
            training_data["faq_items"] = "\n\n".join(faq_items)

    # LLM provider
    console.print("\nLLM Provider:")
    console.print("  [cyan]1[/cyan]. Anthropic (Claude Sonnet)")
    console.print("  [cyan]2[/cyan]. OpenAI (GPT-4o)")
    llm_choice = click.prompt("Select provider", type=int, default=1)
    llm_provider = "openai" if llm_choice == 2 else "anthropic"

    console.print("\nCreating agent...", style="dim")

    try:
        result = api.create_agent({
            "name": name,
            "agent_type": agent_type,
            "plan": plan,
            "training_data": training_data,
        })
    except api.ApiError as e:
        console.print(f"[red]Failed: {e.message}[/red]")
        return

    agent = result.get("agent", {})
    api_key = result.get("apiKey")

    # Set billing mode and LLM provider
    try:
        api.update_agent(agent["id"], {"billing_mode": billing_mode, "llm_provider": llm_provider})
    except api.ApiError:
        pass

    console.print(f"\n[green bold]Agent created![/green bold]\n")
    console.print(f"  ID:   [cyan]{agent.get('id', '—')}[/cyan]")
    console.print(f"  Name: {agent.get('name', '—')}")
    console.print(f"  Type: {agent.get('agent_type', '—')}")

    if api_key:
        console.print(f"\n  API Key: [yellow]{api_key}[/yellow]")
        console.print("  [dim]Save this key — it won't be shown again.[/dim]")

    console.print(f"\nNext steps:")
    console.print(f"  [cyan]humuter agents deploy {agent.get('id', 'ID')}[/cyan] — connect to Telegram")
    console.print(f"  [cyan]humuter chat {agent.get('id', 'ID')} \"Hello\"[/cyan] — test your agent")
    console.print()


def deploy_agent(agent_id: str):
    require_auth()

    try:
        agent = api.get_agent(agent_id)
    except api.ApiError as e:
        console.print(f"[red]{e.message}[/red]")
        return

    console.print(f"\n[bold]Deploy: {agent.get('name', agent_id)}[/bold]\n")

    console.print("Channels:")
    console.print("  [cyan]1[/cyan]. Telegram Bot")
    console.print("  [cyan]2[/cyan]. Discord (coming soon)")
    channel = click.prompt("Select channel", type=int, default=1)

    if channel == 1:
        console.print("\nTo deploy to Telegram:")
        console.print("  1. Open @BotFather on Telegram")
        console.print("  2. Send /newbot and follow the prompts")
        console.print("  3. Copy the bot token\n")

        bot_token = click.prompt("Paste your Telegram bot token")

        console.print("\nConnecting...", style="dim")
        try:
            api.connect_telegram(agent_id, bot_token)
            console.print("[green bold]Telegram connected![/green bold]")
            console.print("Your agent is now live. Send it a message on Telegram.\n")
        except api.ApiError as e:
            console.print(f"[red]Failed: {e.message}[/red]")
    else:
        console.print("[yellow]Discord deployment coming soon.[/yellow]")


def status_agent(agent_id: str):
    require_auth()
    try:
        agent = api.get_agent(agent_id)
    except api.ApiError as e:
        console.print(f"[red]{e.message}[/red]")
        return

    console.print(f"\n[bold]{agent.get('name', 'Agent')}[/bold]\n")
    console.print(f"  ID:            [cyan]{agent.get('id')}[/cyan]")
    console.print(f"  Type:          {agent.get('agent_type', '—')}")
    console.print(f"  Status:        {'[green]active[/green]' if agent.get('status') == 'active' else agent.get('status', '—')}")
    console.print(f"  Plan:          {agent.get('plan', '—')}")
    console.print(f"  Billing:       {agent.get('billing_mode', 'subscription')}")
    console.print(f"  LLM:           {agent.get('llm_provider', 'anthropic')}")
    console.print(f"  Messages:      {agent.get('messages_handled', 0)}")
    console.print(f"  Tokens used:   {agent.get('tokens_used', 0):,}")
    console.print(f"  API Key:       {agent.get('api_key_prefix', 'none')}")
    console.print(f"  Telegram:      {'connected' if agent.get('telegram_bot_token') else 'not connected'}")
    console.print(f"  Discord:       {'connected' if agent.get('discord_server_id') else 'not connected'}")
    console.print()


def configure_agent(agent_id: str):
    require_auth()
    try:
        agent = api.get_agent(agent_id)
    except api.ApiError as e:
        console.print(f"[red]{e.message}[/red]")
        return

    td = agent.get("training_data", {})
    console.print(f"\n[bold]Configure: {agent.get('name', agent_id)}[/bold]")
    console.print("[dim]Press Enter to keep current value.[/dim]\n")

    updates = {}
    new_td = dict(td)

    project_name = click.prompt("Project name", default=td.get("project_name", ""), show_default=True)
    if project_name != td.get("project_name", ""):
        new_td["project_name"] = project_name

    project_desc = click.prompt("Project description", default=td.get("project_description", ""), show_default=True)
    if project_desc != td.get("project_description", ""):
        new_td["project_description"] = project_desc

    tone = click.prompt("Tone", default=td.get("tone", ""), show_default=True)
    if tone != td.get("tone", ""):
        new_td["tone"] = tone

    if new_td != td:
        updates["training_data"] = new_td

    if updates:
        console.print("\nSaving...", style="dim")
        try:
            api.update_agent(agent_id, updates)
            console.print("[green]Updated![/green]\n")
        except api.ApiError as e:
            console.print(f"[red]{e.message}[/red]")
    else:
        console.print("\n[dim]No changes.[/dim]\n")
