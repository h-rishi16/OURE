# OURE Software Safety Hazard Analysis

This document identifies potential software hazards and safety-critical failure modes in the OURE platform, detailing how the software defends against them and alerts the operator. This satisfies NASA-STD-8739.8B requirements.

## 1. False-Negative Collision Probability ($P_c$)

### Description of Hazard
The system calculates and reports a "Safe" $P_c$ (e.g., $< 10^{-6}$) for an impending collision, causing operators to falsely conclude no maneuver is necessary.

### Root Causes & System Defenses

**A. Probability Dilution Region**
*   **Cause:** If covariance (uncertainty) grows excessively large, the probability density spreads out so thinly that the integral over the collision cross-section drops to near zero.
*   **Defense:** OURE implements **Covariance Realism** via the Schmidt-Kalman Filter (SKF) with Adaptive State Noise Compensation (ASNC). The system validates residuals using $\chi^2$ (Chi-Square) testing to ensure covariance matrices are statistically realistic and not artificially inflated.

**B. Non-Linearity Breakdown (Foster's Assumption Failure)**
*   **Cause:** The standard 2D Foster algorithm assumes linear relative motion during the encounter. For low relative velocities or highly curved trajectories (e.g., geostationary orbits), this linearization breaks down, resulting in an invalid $P_c$.
*   **Defense:** `FosterPcCalculator` actively monitors the `miss_distance` and `propagation_age_hours`. If the encounter falls outside the linear regime ($< 3 \times$ Hard Body Radius), the system abandons the analytical formula and automatically fails over to the brute-force `MonteCarloSampler` to calculate the true topological risk.

---

## 2. Temporal Drift in Solar Radiation Pressure (SRP)

### Description of Hazard
The system calculates future positions based on misaligned environmental forces, leading to massive along-track errors.

### Root Causes & System Defenses

*   **Cause:** Using the host machine's wall-clock time (`datetime.now()`) to calculate the Sun vector during a simulation that spans days into the future.
*   **Defense:** The `NumericalPropagator` strictly tracks the `sim_epoch` internally. It computes the Sun vector inline using an analytical model aligned to the exact simulation timestamp, ensuring the solar radiation pressure force mathematically rotates correctly throughout the propagation window.

---

## 3. Unsafe Maneuver Recommendations

### Description of Hazard
The `ManeuverOptimizer` recommends a Delta-V that avoids the immediate collision but inadvertently destabilizes the satellite's orbital regime or exhausts its fuel reserves.

### Root Causes & System Defenses

*   **Cause:** Blindly minimizing $P_c$ without considering orbital element constraints.
*   **Defense:** The `ManeuverOptimizer` is bound by multiple strict constraints:
    1.  **Station Keeping:** It actively measures the post-maneuver RAAN. If the Delta-V alters the Right Ascension of the Ascending Node by more than $\pm0.05^\circ$, the maneuver is flagged as violating station-keeping rules.
    2.  **Fuel Estimation:** It utilizes the Tsiolkovsky rocket equation to report the exact propellant mass (`fuel_cost_kg`) required for the burn, allowing operators to reject maneuvers that require unfeasible amounts of cold-gas or hydrazine.
    3.  **Prograde/Retrograde Bounds:** The Delta-V vector search space is strictly bounded (`max_dv_km_s`), preventing chaotic mathematical solutions from the SLSQP solver.

---

## Alerting Mechanisms

Any hazard that results in a degraded calculation state triggers the `WatchlistAlert` system via the `AlertDispatcher`.

If a calculation fails safely (e.g., due to missing data), the system raises a `click.ClickException`, terminating the CLI gracefully rather than returning silent zeroes. In the API layer, this bubbles up as an HTTP 500 error with a sanitized JSON payload, preventing internal stack traces from leaking to the client while ensuring the failure is definitively logged.
