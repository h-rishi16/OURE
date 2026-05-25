"""
OURE API - TraCSS Autonomous Negotiation
========================================
Implements the emerging 2025 Space Traffic Coordination standards for
operator-to-operator machine negotiation of collision avoidance maneuvers.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from oure.api.middleware import require_api_key

logger = logging.getLogger("oure.api.negotiate")
router = APIRouter(prefix="/negotiate", tags=["Negotiation"])


class TraCSSNegotiationRequest(BaseModel):
    our_sat_id: str = Field(
        ..., description="NORAD ID of the satellite owned by the OURE operator."
    )
    their_sat_id: str = Field(
        ..., description="NORAD ID of the external operator's satellite."
    )
    tca: datetime = Field(..., description="Time of Closest Approach.")
    pc: float = Field(
        ..., description="Probability of Collision calculated by external operator."
    )
    their_fuel_mass_kg: float = Field(
        ..., description="Remaining propellant mass of external satellite in kg."
    )
    their_maneuver_capability: bool = Field(
        ..., description="Can the external satellite execute a maneuver?"
    )


class TraCSSNegotiationResponse(BaseModel):
    decision: str = Field(..., description="WE_WILL_MANEUVER or YOU_MUST_MANEUVER")
    reason: str = Field(..., description="Technical rationale for the decision.")


@router.post(
    "/",
    response_model=TraCSSNegotiationResponse,
    dependencies=[Depends(require_api_key)],
)
def negotiate_maneuver(request: TraCSSNegotiationRequest) -> TraCSSNegotiationResponse:
    """
    Accepts an automated maneuver negotiation request from an external operator.
    Evaluates capabilities and fuel limits to autonomously decide who should move.
    """
    logger.info(
        f"Negotiation request: {request.our_sat_id} (Us) vs {request.their_sat_id} (Them) "
        f"at TCA {request.tca} with Pc={request.pc:.2e}"
    )

    if request.pc < 1e-6:
        raise HTTPException(
            status_code=400, detail="Pc is too low to trigger automated negotiation."
        )

    # Rule 1: Capability
    if not request.their_maneuver_capability:
        return TraCSSNegotiationResponse(
            decision="WE_WILL_MANEUVER",
            reason="External satellite lacks maneuver capability. OURE operator assumes burden.",
        )

    # In a fully integrated system, we would query the spacecraft bus for current fuel.
    # For OURE, we assume a nominal 50.0 kg fuel reserve for our controlled assets.
    OUR_FUEL_MASS_KG = 50.0

    # Rule 2: Critical Fuel Levels
    if request.their_fuel_mass_kg < 5.0 and OUR_FUEL_MASS_KG >= 5.0:
        return TraCSSNegotiationResponse(
            decision="WE_WILL_MANEUVER",
            reason="External satellite is in critical fuel state (< 5kg). OURE operator assumes burden.",
        )

    # Rule 3: Proportional Fuel Burden
    if OUR_FUEL_MASS_KG >= request.their_fuel_mass_kg:
        return TraCSSNegotiationResponse(
            decision="WE_WILL_MANEUVER",
            reason="OURE operator has higher fuel reserves. We will execute avoidance.",
        )

    # Fallback
    return TraCSSNegotiationResponse(
        decision="YOU_MUST_MANEUVER",
        reason="External satellite possesses equal or greater fuel reserves. Please execute avoidance.",
    )
