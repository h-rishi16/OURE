from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from oure.core.models import ConjunctionEvent, OptimizationResult


class ConjunctionReportGenerator:
    """Generates a PDF mission report for a conjunction event."""

    def generate(
        self,
        event: ConjunctionEvent,
        maneuver: OptimizationResult | None,
        output_path: Path,
    ) -> None:
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(
            0,
            10,
            "OURE Conjunction Mission Report",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        pdf.set_font("Helvetica", "", 12)
        pdf.cell(
            0,
            8,
            f"Generated: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%S')}Z",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(4)

        # 1. Executive Summary
        from oure.risk.calculator import RiskCalculator

        calc = RiskCalculator()
        res = calc.compute_pc(event)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "1. Executive Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 12)

        pc_text = f"Probability of Collision (Pc): {res.pc:.4e}"
        if res.warning_level == "RED":
            pc_text += "  [ACTION REQUIRED]"
        elif res.warning_level == "YELLOW":
            pc_text += "  [MONITOR]"
        else:
            pc_text += "  [NOMINAL]"
        pdf.cell(0, 8, pc_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.cell(
            0,
            8,
            f"Time of Closest Approach (TCA): {event.tca.strftime('%Y-%m-%dT%H:%M:%S')}Z",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(
            0,
            8,
            f"Miss Distance: {event.miss_distance_km:.2f} km",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(
            0,
            8,
            f"Relative Velocity: {event.relative_velocity_km_s:.2f} km/s",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(4)

        # 2. Object details
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "2. Object Details", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(
            0,
            8,
            f"Primary Object (NORAD ID): {event.primary_id}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(
            0,
            8,
            f"Primary Altitude: {np.linalg.norm(event.primary_state.r) - 6371.0:.2f} km",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(
            0,
            8,
            f"Secondary Object (NORAD ID): {event.secondary_id}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(
            0,
            8,
            f"Secondary Altitude: {np.linalg.norm(event.secondary_state.r) - 6371.0:.2f} km",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(4)

        # 3. Uncertainty analysis
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(
            0,
            10,
            "3. Uncertainty Analysis (B-Plane)",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(
            0,
            8,
            f"Sigma X: {res.b_plane_sigma_x * 1000.0:.2f} m",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.cell(
            0,
            8,
            f"Sigma Z: {res.b_plane_sigma_z * 1000.0:.2f} m",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(4)

        # 4. Maneuver recommendation
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(
            0, 10, "4. Maneuver Recommendation", new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        pdf.set_font("Helvetica", "", 12)
        if maneuver and maneuver.success:
            burn_epoch_str = (
                maneuver.burn_epoch.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
                if maneuver.burn_epoch
                else "N/A"
            )
            pdf.cell(
                0,
                8,
                f"Burn Epoch: {burn_epoch_str}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.cell(
                0,
                8,
                f"Delta-V (km/s): [{maneuver.optimal_dv_km_s[0]:.6f}, {maneuver.optimal_dv_km_s[1]:.6f}, {maneuver.optimal_dv_km_s[2]:.6f}]",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.cell(
                0,
                8,
                f"Estimated Fuel Cost: {maneuver.fuel_cost_kg:.2f} kg",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.cell(
                0,
                8,
                f"Post-Maneuver Pc: {maneuver.final_pc:.4e}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.cell(
                0,
                8,
                f"Station Keeping Preserved: {'Yes' if maneuver.station_keeping_ok else 'No'}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
        else:
            pdf.cell(
                0,
                8,
                "No maneuver computed or required.",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "5. Metadata", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(
            0,
            8,
            "Generated by OURE - Orbital Uncertainty & Risk Engine",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        pdf.output(str(output_path))
