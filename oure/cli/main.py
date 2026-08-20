"""
OURE Command-Line Interface - Main Entry Point
==============================================
"""

from importlib.metadata import version as _pkg_version
from pathlib import Path

import rich_click as click

# Configure rich-click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = False
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


@click.group(invoke_without_command=True)
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
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Enable verbose debug logging."
)
@click.option(
    "--log-file", type=click.Path(), default=None, help="Path to write log output."
)
@click.version_option(version=_pkg_version("oure"), prog_name="OURE")
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

    if ctx.invoked_subcommand is None:
        import click as standard_click

        if isinstance(standard_click.Context.protected_args, property):
            import typing

            def set_protected_args(self: typing.Any, value: typing.Any) -> None:
                self._protected_args = value

            standard_click.Context.protected_args = property(
                standard_click.Context.protected_args.fget, set_protected_args
            )

        import click_repl._completer
        import click_repl.utils

        original_resolve_context = click_repl.utils._resolve_context

        import typing

        def safe_resolve_context(args: typing.Any, ctx: click.Context) -> click.Context:
            try:
                return typing.cast(click.Context, original_resolve_context(args, ctx))
            except Exception:
                return ctx

        click_repl.utils._resolve_context = safe_resolve_context
        click_repl._completer._resolve_context = safe_resolve_context

        from click_repl import repl
        from rich import print as rprint

        # Print the ASCII art and description before starting the shell
        rprint(click.rich_click.HEADER_TEXT)
        rprint(
            "[dim]Type '/help' to see available commands, or '/exit' to quit.[/dim]\n"
        )

        # click_repl relies on the short_help attribute for descriptions in the autocomplete menu
        command = typing.cast(click.Group, ctx.command)
        for cmd in command.commands.values():
            if getattr(cmd, "short_help", None) is None:
                cmd.short_help = cmd.get_short_help_str()

        import shutil

        def get_prompt() -> str:
            cols, _ = shutil.get_terminal_size()
            return f"{'─' * cols}\n> "

        repl(click.get_current_context(), prompt_kwargs={"message": get_prompt})


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


@cli.command("/exit")
def cmd_slash_exit() -> None:
    """Exit the interactive shell."""
    from click_repl.exceptions import ExitReplException

    raise ExitReplException()


@cli.command("/help")
@click.pass_context
def cmd_slash_help(ctx: click.Context) -> None:
    """Show all available commands."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(
        title="Available Commands",
        title_style="bold magenta",
        show_header=False,
        box=None,
        padding=(0, 2),
    )

    if (
        ctx.parent
        and hasattr(ctx.parent, "command")
        and hasattr(ctx.parent.command, "commands")
    ):
        for name, cmd in sorted(ctx.parent.command.commands.items()):
            if getattr(cmd, "hidden", False):
                continue
            table.add_row(f"[cyan]{name}[/cyan]", cmd.get_short_help_str() or "")

    console.print()
    console.print(table)
    console.print()


if __name__ == "__main__":
    import sys

    from oure.cli.main import cli as real_cli

    sys.exit(real_cli(auto_envvar_prefix="OURE"))
