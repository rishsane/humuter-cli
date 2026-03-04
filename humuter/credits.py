"""Credits and usage commands."""

from rich.console import Console
from rich.table import Table

from humuter import api
from humuter.agents import require_auth

console = Console()


def balance():
    require_auth()
    try:
        stats = api.get_platform_stats()
    except api.ApiError as e:
        console.print(f"[red]{e.message}[/red]")
        return

    bal = stats.get("balance", 0)
    credits = bal / 1_000_000

    console.print(f"\n[bold]Credit Balance[/bold]\n")
    console.print(f"  Balance:  [green bold]${credits:.2f}[/green bold]")
    console.print(f"  This month: ${stats.get('month', {}).get('spent', 0) / 1_000_000:.2f} spent")
    console.print(f"  Requests:   {stats.get('month', {}).get('requests', 0)} this month")
    console.print(f"  Tokens:     {stats.get('month', {}).get('input_tokens', 0) + stats.get('month', {}).get('output_tokens', 0):,} this month")
    console.print()


def usage():
    require_auth()
    try:
        stats = api.get_platform_stats()
    except api.ApiError as e:
        console.print(f"[red]{e.message}[/red]")
        return

    month = stats.get("month", {})
    agents = stats.get("agent_breakdown", [])

    console.print(f"\n[bold]Usage Breakdown (This Month)[/bold]\n")
    console.print(f"  Total cost:     ${month.get('spent', 0) / 1_000_000:.4f}")
    console.print(f"  Requests:       {month.get('requests', 0)}")
    console.print(f"  Input tokens:   {month.get('input_tokens', 0):,}")
    console.print(f"  Output tokens:  {month.get('output_tokens', 0):,}")

    if agents:
        console.print(f"\n[bold]By Agent[/bold]\n")
        table = Table(show_edge=False, pad_edge=False)
        table.add_column("Agent", style="bold")
        table.add_column("Requests", justify="right")
        table.add_column("Cost", justify="right")

        for a in sorted(agents, key=lambda x: x["cost_micro_credits"], reverse=True):
            table.add_row(
                a["agent_name"],
                str(a["requests"]),
                f"${a['cost_micro_credits'] / 1_000_000:.4f}",
            )
        console.print(table)

    console.print()
