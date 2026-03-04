"""Login flow — opens browser, polls for completion."""

import time
import webbrowser

import click
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

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

    # Poll with animated spinner
    with Live(Spinner("dots", text="[dim]Waiting for browser login...[/dim]"), refresh_per_second=10, console=console) as live:
        max_attempts = 300
        for i in range(max_attempts):
            time.sleep(2)
            try:
                result = api.poll_cli_session(session_id)
            except api.ApiError:
                continue

            status = result.get("status")

            if status == "completed":
                live.stop()
                token = result["token"]
                user_id = result.get("user_id", "")
                save_credentials(token, user_id)
                console.print("\n[green bold]Logged in successfully![/green bold]\n")
                console.print("Run [bold #ff8c00]humuter[/bold #ff8c00] to launch the dashboard.\n")
                return

            if status == "expired":
                live.stop()
                console.print("\n[red]Session expired. Please try again.[/red]")
                return

    console.print("\n[red]Timed out waiting for login. Please try again.[/red]")


def logout():
    """Clear stored credentials."""
    clear_credentials()
    console.print("[green]Logged out.[/green]")
