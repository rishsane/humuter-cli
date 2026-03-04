"""Login flow — opens browser, polls for completion."""

import time
import webbrowser

import click
from rich.console import Console

from humuter import api
from humuter.config import save_credentials, clear_credentials, load_credentials

console = Console()


def login():
    """Device-flow login: create session → open browser → poll."""
    existing = load_credentials()
    if existing:
        if not click.confirm("You're already logged in. Re-authenticate?", default=False):
            return

    console.print("\n[bold]Authenticating with Humuter...[/bold]\n")

    try:
        session = api.create_cli_session()
    except api.ApiError as e:
        console.print(f"[red]Failed to start login: {e.message}[/red]")
        return

    session_id = session["session_id"]
    login_url = session["login_url"]

    console.print(f"Opening browser to:\n[cyan]{login_url}[/cyan]\n")
    webbrowser.open(login_url)
    console.print("Waiting for you to log in via the browser...\n")

    # Poll every 2 seconds for up to 10 minutes
    max_attempts = 300
    for i in range(max_attempts):
        time.sleep(2)
        try:
            result = api.poll_cli_session(session_id)
        except api.ApiError:
            continue

        status = result.get("status")

        if status == "completed":
            token = result["token"]
            user_id = result.get("user_id", "")
            save_credentials(token, user_id)
            console.print("[green bold]Logged in successfully![/green bold]\n")
            console.print("You can now use [cyan]humuter[/cyan] commands.\n")
            return

        if status == "expired":
            console.print("[red]Session expired. Please try again.[/red]")
            return

        # Still pending — show progress dots
        if i % 5 == 0 and i > 0:
            console.print("  Still waiting...", style="dim")

    console.print("[red]Timed out waiting for login. Please try again.[/red]")


def logout():
    """Clear stored credentials."""
    clear_credentials()
    console.print("[green]Logged out.[/green]")
