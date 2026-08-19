"""
OURE CLI - Design System & UI Utilities
=======================================
Centralized theme and components for a consistent OURE experience.
"""

import json
import logging
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from oure.core.models import CovarianceMatrix, RiskResult, StateVector

logger = logging.getLogger("oure.cli.utils")

# Define the official OURE Brand Theme
OURE_THEME = Theme(
    {
        "info": "cyan",
        "warning": "bold yellow",
        "danger": "bold red",
        "success": "bold green",
        "highlight": "bold magenta",
        "dim": "grey50",
    }
)

console = Console(theme=OURE_THEME)


class UI:
    """Namespace for standardized UI components."""

    @staticmethod
    def header(title: str, subtitle: str | None = None) -> None:
        """Prints a branded OURE header."""
        logo = """[cyan]   ██████╗ ██╗   ██╗██████╗ ███████╗
  ██╔═══██╗██║   ██║██╔══██╗██╔════╝
  ██║   ██║██║   ██║██████╔╝█████╗
  ██║   ██║██║   ██║██╔══██╗██╔══╝
  ╚██████╔╝╚██████╔╝██║  ██║███████╗
   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝[/cyan]
"""
        content = (
            f"{logo}\n[bold white]OURE[/bold white] [dim]|[/dim] [info]{title}[/info]"
        )
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"
        console.print(Panel(content, border_style="blue", expand=False))

    @staticmethod
    def error(message: str, advice: str | None = None) -> None:
        """Prints a standardized error box."""
        content = f"[danger]Error:[/danger] {message}"
        if advice:
            content += f"\n\n[info]Advice:[/info] {advice}"
        console.print(
            Panel(
                content,
                border_style="red",
                title="[bold red]System Exception[/bold red]",
            )
        )

    @staticmethod
    def success(message: str) -> None:
        """Prints a simple success message."""
        console.print(f"[success]DONE[/success] {message}")


def _tle_to_initial_state(tle: Any) -> StateVector:
    """Backward-compatible wrapper. Use oure.core.utils.tle_to_initial_state instead."""
    from oure.core.utils import tle_to_initial_state

    return tle_to_initial_state(tle)


def _default_covariance(sat_id: str, sigma_km: float = 0.5) -> CovarianceMatrix:
    """Backward-compatible wrapper. Use oure.core.utils.default_covariance instead."""
    from oure.core.utils import default_covariance

    return default_covariance(sat_id, sigma_km)


def _print_results_table(results: list[RiskResult]) -> None:
    table = Table(title="Conjunction Assessment Results", box=None, border_style="dim")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Object 1", style="info")
    table.add_column("Object 2", style="danger")
    table.add_column("TCA (UTC)", justify="center", style="success")
    table.add_column("Miss (km)", justify="right", style="highlight")
    table.add_column("Pc", justify="right")
    table.add_column("Risk", justify="center")

    for idx, r in enumerate(results, 1):
        color = "white"
        symbol = "[ ]"
        if r.warning_level == "RED":
            color = "red"
            symbol = "[!]"
        elif r.warning_level == "YELLOW":
            color = "yellow"
            symbol = "[-]"
        elif r.warning_level == "GREEN":
            color = "green"
            symbol = "[o]"

        table.add_row(
            str(idx),
            str(r.conjunction.primary_id),
            str(r.conjunction.secondary_id),
            r.conjunction.tca.strftime("%Y-%m-%d %H:%M"),
            f"{r.conjunction.miss_distance_km:.3f}",
            f"[{color}]{r.pc:.2e}[/{color}]",
            f"[{color}]{symbol} {r.warning_level}[/{color}]",
        )
    console.print(table)


def _print_summary_banner(max_pc: float, num_events: int = 1) -> None:
    if max_pc >= 1e-3:
        color = "red"
        symbol = "RED ALERT"
    elif max_pc >= 1e-5:
        color = "yellow"
        symbol = "YELLOW ALERT"
    else:
        color = "green"
        symbol = "ALL CLEAR"

    console.print(
        Panel(
            f"{symbol} | Max Pc: [bold]{max_pc:.2e}[/bold]\nAnalyzed {num_events} potential encounter(s)",
            title="[bold]Risk Summary[/bold]",
            border_style=color,
            expand=False,
        )
    )


def _save_results_to_json(results: list[RiskResult], path: Path) -> None:
    output = []
    for r in results:
        output.append(
            {
                "primary_id": r.conjunction.primary_id,
                "secondary_id": r.conjunction.secondary_id,
                "tca": r.conjunction.tca.isoformat(),
                "pc": r.pc,
                "warning_level": r.warning_level,
                "miss_distance_km": r.conjunction.miss_distance_km,
                "rel_velocity_km_s": r.conjunction.relative_velocity_km_s,
                "sigma_bplane_km": [r.b_plane_sigma_x, r.b_plane_sigma_z],
                "hard_body_radius_m": r.hard_body_radius_m,
            }
        )
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
