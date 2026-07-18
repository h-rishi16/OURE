from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from oure.cli.utils import _default_covariance, _tle_to_initial_state
from oure.conjunction.assessor import ConjunctionAssessor
from oure.data.api_client import fetch_active_tles
from oure.data.noaa import NOAASolarFluxFetcher
from oure.physics.factory import PropagatorFactory
from oure.risk.calculator import RiskCalculator
from oure.risk.plotter import RiskPlotter

router = APIRouter(prefix="/ui", tags=["UI"])

# Setup Jinja2 templates pointing to the local templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

flux_fetcher = NOAASolarFluxFetcher()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main HTMX dashboard page."""
    return templates.TemplateResponse(request, "index.html", {"request": request})


@router.get("/globe", response_class=HTMLResponse)
async def globe(request: Request) -> HTMLResponse:
    """Render the 3D Interactive Map."""
    return templates.TemplateResponse(request, "globe.html", {"request": request})


@router.get("/api/tles", response_class=PlainTextResponse)
async def get_tles() -> PlainTextResponse:
    """Fetch active TLEs asynchronously and serve them to the frontend."""
    cache_file = await fetch_active_tles()
    if cache_file and Path(cache_file).exists():
        with open(cache_file, "r") as f:
            return PlainTextResponse(f.read())
    raise HTTPException(status_code=500, detail="Could not fetch TLEs")


@router.post("/analyze", response_class=HTMLResponse)
async def analyze_risk(
    request: Request,
    primary_id: str = Form(...),
    secondary_id: str = Form(...),
    hbr: float = Form(0.02),
) -> HTMLResponse:
    """
    Process form data via HTMX, run the physics engine, and return
    the rendered HTML fragment containing the results and Plotly chart.
    """
    try:
        # 1. Fetch Data from CelesTrak (No Authentication Required)
        import httpx

        from oure.data.spacetrack import SpaceTrackFetcher  # For the parser logic

        url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={primary_id},{secondary_id}&FORMAT=json"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

        # Instantiate fetcher just to use its handy JSON parser method
        dummy_fetcher = SpaceTrackFetcher("", "")

        record_map = {}
        for item in data:
            try:
                # CelesTrak JSON is identical to SpaceTrack JSON
                rec = dummy_fetcher._parse_tle_record(item)
                record_map[rec.sat_id] = rec
            except Exception:
                continue

        if primary_id not in record_map or secondary_id not in record_map:
            raise HTTPException(
                status_code=404,
                detail="Satellite data missing or not found on CelesTrak.",
            )

        flux = flux_fetcher.get_current_f107()

        # 2. Setup States
        p_state = _tle_to_initial_state(record_map[primary_id])
        s_state = _tle_to_initial_state(record_map[secondary_id])
        p_cov = _default_covariance(primary_id)
        s_cov = _default_covariance(secondary_id)

        # 3. Propagator & Assessor
        base_prop = PropagatorFactory.build(
            tle=record_map[primary_id], solar_flux=flux, use_analytical=False
        )
        assessor = ConjunctionAssessor()

        # 4. Find Conjunctions
        events = assessor.find_conjunctions(
            primary=p_state,
            primary_cov=p_cov,
            primary_propagator=base_prop,
            secondaries=[(s_state, s_cov, base_prop)],
            look_ahead_hours=72.0,
        )

        if not events:
            # Render a safe response
            return templates.TemplateResponse(
                request,
                "result.html",
                {
                    "warning_level": "GREEN",
                    "pc": 0.0,
                    "tca": "N/A",
                    "miss_distance_km": 0.0,
                    "rel_velocity_km_s": 0.0,
                    "plot_html": None,
                },
            )

        # Process closest event
        event = events[0]
        calc = RiskCalculator(hard_body_radius_m=hbr * 1000.0)
        risk_result = calc.compute_pc(event)

        # 5. Generate Plotly Graph (HTML string without full page wrap)
        event_dict = {
            "primary_id": primary_id,
            "secondary_id": secondary_id,
            "miss_distance_km": event.miss_distance_km,
            "sigma_bplane_km": [
                risk_result.b_plane_sigma_x,
                risk_result.b_plane_sigma_z,
            ],
            "hard_body_radius_m": hbr * 1000.0,
            "pc": risk_result.pc,
        }
        fig = RiskPlotter.create_bplane_figure(event_dict)
        # Use full_html=False to just get the div and script tags
        plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

        # 6. Render the Result Template Fragment
        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "warning_level": risk_result.warning_level,
                "pc": risk_result.pc,
                "tca": event.tca.strftime("%Y-%m-%d %H:%M:%S"),
                "miss_distance_km": event.miss_distance_km,
                "rel_velocity_km_s": event.relative_velocity_km_s,
                "plot_html": plot_html,
            },
        )

    except Exception as e:
        import logging

        logging.getLogger("oure.api.ui").exception("UI Analysis failed")
        return HTMLResponse(
            f"""
            <div class="bg-red-900/50 border border-red-500 text-red-200 p-6 rounded-lg text-left">
                <h3 class="font-bold text-xl mb-2">Analysis Failed</h3>
                <p class="font-mono text-sm">{str(e)}</p>
            </div>
        """
        )
