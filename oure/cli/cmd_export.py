from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import click
import numpy as np

from oure.core.models import ConjunctionEvent, CovarianceMatrix, StateVector
from oure.data.cdm_writer import CDMWriter
from oure.data.oem import OEMWriter
from oure.physics.sgp4_propagator import SGP4Propagator
from oure.reporting.pdf_report import ConjunctionReportGenerator

from .main import cli
from .utils import UI


def _get_mock_event(event_id: str) -> ConjunctionEvent:
    # Mock retrieval logic since cache retrieval by event_id isn't fully implemented in the db schema yet
    return ConjunctionEvent(
        primary_id="25544",
        secondary_id=event_id,
        tca=datetime.now(UTC),
        miss_distance_km=1.0,
        relative_velocity_km_s=10.0,
        primary_state=StateVector(
            np.array([7000.0, 0, 0]), np.array([0, 7.5, 0]), datetime.now(UTC), "25544"
        ),
        secondary_state=StateVector(
            np.array([7000.5, 0, 0]),
            np.array([0, -7.5, 0]),
            datetime.now(UTC),
            event_id,
        ),
        primary_covariance=CovarianceMatrix(np.eye(6), datetime.now(UTC), "25544"),
        secondary_covariance=CovarianceMatrix(np.eye(6), datetime.now(UTC), event_id),
    )


@cli.command("generate-cdm")
@click.option("--event-id", required=True, help="Event ID to retrieve from cache.")
@click.option("--output", type=click.Path(), required=True, help="Output path for CDM.")
def generate_cdm(event_id: str, output: str) -> None:
    """Generate a CCSDS compliant CDM file from an event."""
    event = _get_mock_event(event_id)
    writer = CDMWriter()
    writer.write(
        event, event.primary_covariance, event.secondary_covariance, Path(output)
    )
    UI.success(f"Generated CDM for {event_id} at {output}")


@cli.command("report-event")
@click.option("--event-id", required=True, help="Event ID to retrieve from cache.")
@click.option("--output", type=click.Path(), required=True, help="Output path for PDF.")
@click.option(
    "--include-maneuver", is_flag=True, help="Include maneuver recommendation."
)
def report_event(event_id: str, output: str, include_maneuver: bool) -> None:
    """Generate a PDF mission report for a conjunction event."""
    event = _get_mock_event(event_id)
    generator = ConjunctionReportGenerator()
    generator.generate(event, None, Path(output))
    UI.success(f"Generated PDF report for {event_id} at {output}")


@cli.command("export-ephemeris")
@click.option("--primary", required=True, help="NORAD catalog ID of the satellite.")
@click.option(
    "--output", type=click.Path(), required=True, help="Output path for OEM file."
)
@click.pass_obj
def export_ephemeris(ctx: Any, primary: str, output: str) -> None:
    """Propagate a satellite for 24 hours and export its ephemeris in CCSDS OEM format."""
    tle = ctx.tle_fetcher.fetch_tle(primary)
    propagator = SGP4Propagator(tle)

    start_time = datetime.now(UTC)
    states = []

    # Dummy state vector just to satisfy BasePropagator interface
    dummy_state = StateVector(np.zeros(3), np.zeros(3), start_time, primary)

    click.echo(f"Propagating {primary} for 24 hours...")
    for minutes in range(0, 24 * 60, 5):  # 5-minute step size
        epoch = start_time + timedelta(minutes=minutes)
        state = propagator.propagate_to(dummy_state, epoch)
        states.append(state)

    writer = OEMWriter()
    oem_data = writer.write(states)

    with open(output, "w") as f:
        f.write(oem_data)

    UI.success(f"Successfully exported 24-hour ephemeris to {output}")
