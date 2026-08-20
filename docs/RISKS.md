# OURE Project Risk Register

This document serves as the formal Risk Management Plan and Risk Register for the OURE project, satisfying the requirements of NPR 7150.2D (SWE §3.6).

## Risk Matrix Definition
- **Likelihood:** 1 (Rare) to 5 (Almost Certain)
- **Impact:** 1 (Negligible) to 5 (Catastrophic)
- **Risk Score = Likelihood × Impact**

---

## 1. External API Dependency Risks

### RISK-API-01: Space-Track.org Unavailability
*   **Description:** The primary source for TLE data becomes unreachable due to network outages, API limits, or credential revocation.
*   **Likelihood:** 3
*   **Impact:** 4
*   **Score:** 12
*   **Mitigation Strategy:** OURE implements an SQLite caching layer (`oure/data/cache.py`) to serve the most recent TLEs. The system includes an automated fallback to generate mathematically bounded mock TLEs if the cache is expired and the network is down.

### RISK-API-02: NOAA Space Weather API Changes
*   **Description:** NOAA drastically alters the payload structure of the 45-day solar flux forecast, breaking the JSON parser.
*   **Likelihood:** 2
*   **Impact:** 3
*   **Score:** 6
*   **Mitigation Strategy:** The `_parse_flux` method in `oure/data/noaa.py` is defensively programmed to handle both Dictionary and List payload variations. If all parsing fails, it safely falls back to the solar mean (`150.0 SFU`), preventing a system crash while logging a warning.

---

## 2. Infrastructure & Compute Risks

### RISK-INFRA-01: Memory Exhaustion (OOM) via Monte Carlo
*   **Description:** A user or automated script requests an extreme number of Monte Carlo samples (e.g., > 10,000,000) for a fleet-wide screening, exhausting server RAM.
*   **Likelihood:** 3
*   **Impact:** 4 (Service Denial)
*   **Score:** 12
*   **Mitigation Strategy:** FastAPI request models do not expose `mc_samples` to remote API callers, preventing external abuse. For the CLI, it relies on operator discretion, as local users control their own compute limits.

### RISK-INFRA-02: Celery Worker Deadlocks
*   **Description:** Background screening tasks enter an infinite loop, starving the queue and halting mission operations.
*   **Likelihood:** 1
*   **Impact:** 5
*   **Score:** 5
*   **Mitigation Strategy:** All `while True` loops have been eradicated from the codebase per JPL Power of 10. Fleet screening is chunked via `propagate_many_to()`, and long-running optimizations are strictly capped via `maxiter=25` in the SLSQP solver.

---

## 3. Mathematical & Integrity Risks

### RISK-MATH-01: Singular Covariance Matrices
*   **Description:** An incoming CDM or calculated uncertainty bubble possesses zero variance along one axis, causing standard matrix inversion (`np.linalg.inv`) to fail with a `LinAlgError`.
*   **Likelihood:** 2
*   **Impact:** 5 (Calculation Failure)
*   **Score:** 10
*   **Mitigation Strategy:** OURE exclusively utilizes Moore-Penrose pseudo-inverses (`np.linalg.pinv`) in all risk (Foster $P_c$) and uncertainty (Kalman Filter) algorithms, guaranteeing numerical stability even during perfect singularities.
