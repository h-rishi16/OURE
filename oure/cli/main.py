"""
OURE Command-Line Interface - Main Entry Point
==============================================
"""

from pathlib import Path

import rich_click as click

# Configure rich-click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = "Try running '--help' for more information."
click.rich_click.ERRORS_EPILOGUE = (
    "To find out more, visit https://github.com/h-rishi16/oure"
)
click.rich_click.HEADER_TEXT = """[cyan]
  ██████╗ ██╗   ██╗██████╗ ███████╗
 ██╔═══██╗██║   ██║██╔══██╗██╔════╝
 ██║   ██║██║   ██║██████╔╝█████╗
 ██║   ██║██║   ██║██╔══██╗██╔══╝
 ╚██████╔╝╚██████╔╝██║  ██║███████╗
  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝[/cyan]

[bold]Orbital Uncertainty & Risk Engine[/bold]
Satellite Collision Probability Solver for Space Situational Awareness.
"""

from oure.core.logging_config import LogFormat, configure_logging
from oure.data.cache import CacheManager
from oure.data.noaa import NOAASolarFluxFetcher
from oure.data.spacetrack import SpaceTrackFetcher

# setup_logging removed — configure_logging() from logging_config is used instead


class OUREContext:
    """Holds shared configuration and service instances."""

    def __init__(
        self,
        st_username: str | None,
        st_password: str | None,
        db_path: Path | None,
        verbose: bool,
    ):
        from oure.core.config import settings

        actual_user = st_username or settings.spacetrack_user
        actual_pass = st_password or settings.spacetrack_pass

        self.cache = CacheManager(db_path=db_path)
        self.tle_fetcher = SpaceTrackFetcher(
            username=actual_user, password=actual_pass, cache=self.cache
        )
        self.flux_fetcher = NOAASolarFluxFetcher(cache=self.cache)
        self.verbose = verbose


@click.group()
@click.option(
    "--st-username",
    envvar="SPACETRACK_USER",
    required=False,
    help="Space-Track.org username (or set $SPACETRACK_USER)",
)
@click.option(
    "--st-password",
    envvar="SPACETRACK_PASS",
    required=False,
    help="Space-Track.org password (or set $SPACETRACK_PASS)",
)
@click.option(
    "--db-path",
    type=click.Path(),
    default=None,
    help="Path to SQLite cache database (default: ~/.oure/cache.db)",
)
@click.option("--verbose", "-v", is_flag=True, default=False)
@click.option("--log-file", type=click.Path(), default=None)
@click.version_option(version="1.0.0", prog_name="OURE")
@click.pass_context
def cli(
    ctx: click.Context,
    st_username: str,
    st_password: str,
    db_path: str | None,
    verbose: bool,
    log_file: str | None,
) -> None:
    """Main CLI Entry Point."""
    import os

    fmt = (
        LogFormat.CONSOLE
        if not os.getenv("OURE_LOG_FORMAT") == "json"
        else LogFormat.JSON
    )
    configure_logging(
        level="DEBUG" if verbose else "INFO", format=fmt, log_file=log_file
    )

    ctx.ensure_object(dict)
    ctx.obj = OUREContext(
        st_username=st_username,
        st_password=st_password,
        db_path=Path(db_path) if db_path else None,
        verbose=verbose,
    )


# Import commands to register them with the CLI group
from . import (  # noqa: F401
    cmd_analyze,
    cmd_auth,
    cmd_avoid,
    cmd_cache,
    cmd_cdm,
    cmd_export,
    cmd_fetch,
    cmd_fleet,
    cmd_history,
    cmd_monitor,
    cmd_plot,
    cmd_report,
    cmd_sensor,
    cmd_shatter,
)
from .tui import launch_tui


@cli.command("tui")
def tui_cmd() -> None:
    """Launch the interactive Terminal User Interface (TUI) Dashboard."""
    launch_tui()


if __name__ == "__main__":
    cli(auto_envvar_prefix="OURE")
