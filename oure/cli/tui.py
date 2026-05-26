import os

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, DataTable, Footer, Header, Static

from oure.data.cache import CacheManager


class InfoPanel(Static):  # type: ignore
    """A widget to display system status."""

    def on_mount(self) -> None:
        self.update(
            "Status: [green]Online[/green]\n"
            "Mode: Text User Interface (TUI)\n\n"
            "Database: " + os.path.basename(CacheManager.DEFAULT_DB_PATH) + "\n"
            "Engine: OURE v1.0.0"
        )


class ActiveConjunctionsTable(DataTable):  # type: ignore
    """A table to display high-risk events from the cache."""

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_columns(
            "Primary ID",
            "Secondary ID",
            "TCA (UTC)",
            "Probability (Pc)",
            "Miss Dist (km)",
            "Level",
        )

        # Load mock data for the initial TUI view to show it works
        self.add_row(
            "25544", "43205", "2026-05-26 14:00:00", "1.2e-4", "0.85", "YELLOW"
        )
        self.add_row(
            "25544", "41456", "2026-05-27 09:30:00", "8.5e-5", "1.20", "YELLOW"
        )
        self.add_row("48274", "12345", "2026-05-27 18:45:00", "4.1e-3", "0.15", "RED")


class OureTuiApp(App):  # type: ignore
    """The main Terminal User Interface for OURE."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 3fr;
    }

    #sidebar {
        width: 100%;
        height: 100%;
        dock: left;
        padding: 1;
        border-right: solid green;
    }

    #main-content {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    DataTable {
        height: 1fr;
        border: solid cyan;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh Data"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        with Container(id="sidebar"):
            yield Static(
                "[bold magenta]OURE Control Panel[/bold magenta]\n", classes="title"
            )
            yield InfoPanel()
            yield Static("\n")
            yield Button("Analyze Fleet", id="btn_analyze", variant="primary")
            yield Button("Avoidance Wizard", id="btn_avoid", variant="warning")
            yield Button("Fetch TLEs", id="btn_fetch", variant="success")

        with Container(id="main-content"):
            yield Static(
                "[bold cyan]Active High-Risk Conjunctions (Top 100)[/bold cyan]"
            )
            yield ActiveConjunctionsTable()

        yield Footer()

    def action_refresh(self) -> None:
        """Action to perform when 'r' is pressed."""
        self.notify("Refreshing data from cache...")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn_analyze":
            self.notify("Fleet analysis requires specifying a catalog file.")
        elif event.button.id == "btn_avoid":
            self.notify("Select a conjunction from the table first.")
        elif event.button.id == "btn_fetch":
            self.notify("Fetching latest TLEs from Space-Track in background...")


def launch_tui() -> None:
    """Entry point for the TUI."""
    app = OureTuiApp()
    app.run()
