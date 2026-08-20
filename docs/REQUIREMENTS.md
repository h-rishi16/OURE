# OURE Requirements Mapping Matrix (RMM)

This document establishes bi-directional traceability (SWE-052) between software requirements and the automated test suite.

| Requirement ID | Description | Verification Method | Associated Tests |
| :--- | :--- | :--- | :--- |
| **REQ-PHYS-01** | The system shall support Analytical Orbit Propagation using the SGP4 algorithm for TEME to GCRF coordinates. | Automated Test | `test_sgp4_base`, `test_sgp4_propagate_sequence` |
| **REQ-PHYS-02** | The system shall support High-Precision Numerical Propagation (HPOP) utilizing RK45 integration. | Automated Test | `test_numerical_propagator`, `test_numerical_propagate_many` |
| **REQ-PHYS-03** | The system shall compute Probability of Collision (Pc) using the 2D Foster (1992) equation on the encounter B-Plane. | Automated Test | `test_foster_pc_known_value` |
| **REQ-DATA-01** | The system shall securely fetch and cache Two-Line Elements (TLEs) from Space-Track.org. | Automated Test | `test_spacetrack_fetcher_fetch_from_network`, `test_spacetrack_fetcher_login_success` |
| **REQ-DATA-02** | The system shall ingest F10.7 Solar Flux data from NOAA for atmospheric density models. | Automated Test | `test_noaa_fetcher_network_fetch`, `test_noaa_fetcher_cache_hit` |
| **REQ-DATA-03** | The system shall parse and export CCSDS standardized Conjunction Data Messages (CDM). | Automated Test | `test_cdm_parser`, `test_cdm_writer` |
| **REQ-RISK-01** | The system shall recommend Delta-V maneuvers utilizing SLSQP to achieve a target Pc of 1e-5. | Automated Test | `test_maneuver_optimizer` |
| **REQ-OPS-01** | The system shall support a periodic Watchlist monitoring daemon to evaluate specific assets against the public catalog. | Automated Test | `test_watchlist_monitor_run_screening_and_alerts` |
| **REQ-OPS-02** | The system shall implement an automated API endpoint for TraCSS-compliant operator-to-operator maneuver negotiation. | Automated Test | `test_negotiate_low_pc`, `test_negotiate_no_capability`, `test_negotiate_critical_fuel`, `test_negotiate_less_fuel`, `test_negotiate_more_fuel` |
| **REQ-PHYS-04** | The system shall support multi-state maneuver propagation for fleet-wide physics simulations. | Automated Test | `test_maneuver_optimizer` |
| **REQ-OPS-03** | The system shall securely route all microservices through a unified NGINX reverse proxy on a single port. | Manual Test | `Verification of Port 80 routing` |
| **REQ-UI-01** | The system shall provide an interactive 3D Web UI for spatial visualization of LEO and GSO satellite catalogs. | Manual Test | `Next.js Globe rendering` |
