import os
import tempfile

from celery.result import AsyncResult
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field, field_validator

from oure.api.celery_app import celery_app
from oure.api.middleware import require_api_key
from oure.api.negotiate import router as negotiate_router
from oure.api.tasks import run_fleet_screening
from oure.api.ui import router as ui_router
from oure.data.cdm_parser import CDMParser
from oure.risk.calculator import RiskCalculator

app = FastAPI(
    title="OURE API",
    version="1.0.0",
    description="Orbital Uncertainty & Risk Engine API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument the app for Prometheus monitoring
Instrumentator().instrument(app).expose(app)

app.include_router(negotiate_router)
app.include_router(ui_router)


class RiskResponse(BaseModel):
    primary_id: str
    secondary_id: str
    tca: str
    pc: float
    warning_level: str
    miss_distance_km: float
    rel_velocity_km_s: float


class TaskSubmitRequest(BaseModel):
    primary_id: str
    secondary_ids: list[str] = Field(..., max_length=1000)

    @field_validator("secondary_ids")
    @classmethod
    def limit_ids(cls, v: list[str]) -> list[str]:
        if len(v) > 1000:
            raise ValueError("Maximum 1,000 secondary IDs per screening task.")
        return v


@app.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    """Redirect root to the UI dashboard."""
    return RedirectResponse(url="/ui/")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Verify the API is running."""
    return {"status": "operational", "version": "1.0.0"}


@app.post("/tasks/screen", dependencies=[Depends(require_api_key)])
def submit_screening_task(req: TaskSubmitRequest) -> dict[str, str]:
    """Submit a fleet screening job to the background Celery worker queue."""
    task = run_fleet_screening.delay(req.primary_id, req.secondary_ids)
    return {"task_id": str(task.id), "status": "submitted"}


@app.get("/tasks/{task_id}", dependencies=[Depends(require_api_key)])
def get_task_status(task_id: str) -> dict[str, object]:
    """Retrieve the status and results of a background Celery task."""
    task_result = AsyncResult(task_id, app=celery_app)
    response: dict[str, object] = {
        "task_id": task_id,
        "state": task_result.state,
    }

    if task_result.state == "PROGRESS":
        response["meta"] = task_result.info
    elif task_result.state == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.state == "FAILURE":
        response["error"] = str(task_result.info)

    return response


@app.post(
    "/analyze/cdm", response_model=RiskResponse, dependencies=[Depends(require_api_key)]
)
async def analyze_cdm(
    file: UploadFile = File(...), hard_body_radius: float = 20.0
) -> RiskResponse:
    """
    Upload a JSON CDM file and receive a risk assessment.
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON CDMs are supported.")

    temp_path = None
    try:
        # Create temp file inside the try block to ensure cleanup
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name
            contents = await file.read()
            temp_file.write(contents)

        # Parse and calculate
        event = CDMParser.parse_json(temp_path)
        calc = RiskCalculator(hard_body_radius_m=hard_body_radius)
        result = calc.compute_pc(event)

        return RiskResponse(
            primary_id=result.conjunction.primary_id,
            secondary_id=result.conjunction.secondary_id,
            tca=result.conjunction.tca.isoformat(),
            pc=result.pc,
            warning_level=result.warning_level,
            miss_distance_km=result.conjunction.miss_distance_km,
            rel_velocity_km_s=result.conjunction.relative_velocity_km_s,
        )
    except Exception:
        import logging

        logging.getLogger("oure.api").exception("CDM processing failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse CDM file. Ensure it follows the CCSDS JSON schema.",
        )
    finally:
        # Guaranteed cleanup regardless of where an exception occurred
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


class PairRequest(BaseModel):
    primary_id: str
    secondary_id: str


@app.post(
    "/analyze/pair",
    response_model=RiskResponse,
    dependencies=[Depends(require_api_key)],
)
def analyze_pair_sync(req: PairRequest) -> RiskResponse:
    from oure.cli.utils import _default_covariance, _tle_to_initial_state
    from oure.conjunction.assessor import ConjunctionAssessor
    from oure.core.config import settings
    from oure.data.noaa import NOAASolarFluxFetcher
    from oure.data.spacetrack import SpaceTrackFetcher
    from oure.physics.factory import PropagatorFactory
    from oure.risk.calculator import RiskCalculator

    tle_fetcher = SpaceTrackFetcher(
        username=settings.spacetrack_user,
        password=settings.spacetrack_pass,
    )
    flux_fetcher = NOAASolarFluxFetcher()

    records = {
        r.sat_id: r
        for r in tle_fetcher.fetch(sat_ids=[req.primary_id, req.secondary_id])
    }
    flux = flux_fetcher.get_current_f107()

    if req.primary_id not in records or req.secondary_id not in records:
        raise HTTPException(
            status_code=404, detail="Could not fetch TLEs for one or both satellites."
        )

    primary_tle = records[req.primary_id]
    primary_state = _tle_to_initial_state(primary_tle)
    primary_prop = PropagatorFactory.build(primary_tle, solar_flux=flux)
    primary_cov = _default_covariance(req.primary_id)

    secondary_tle = records[req.secondary_id]
    secondary_state = _tle_to_initial_state(secondary_tle)
    secondary_prop = PropagatorFactory.build(secondary_tle, solar_flux=flux)
    secondary_cov = _default_covariance(req.secondary_id)

    secondaries_data = [(secondary_state, secondary_cov, secondary_prop)]

    assessor = ConjunctionAssessor(screening_distance_km=50.0)
    events = assessor.find_conjunctions(
        primary_state,
        primary_cov,
        primary_prop,
        secondaries_data,
        look_ahead_hours=72.0,
    )

    if not events:
        raise HTTPException(
            status_code=404, detail="No conjunction event found within 72 hours."
        )

    calculator = RiskCalculator(hard_body_radius_m=20.0)
    res = calculator.compute_pc(events[0])

    return RiskResponse(
        primary_id=res.conjunction.primary_id,
        secondary_id=res.conjunction.secondary_id,
        tca=res.conjunction.tca.isoformat(),
        pc=res.pc,
        warning_level=res.warning_level,
        miss_distance_km=res.conjunction.miss_distance_km,
        rel_velocity_km_s=res.conjunction.relative_velocity_km_s,
    )
