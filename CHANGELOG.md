# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-22

### Added
- **Next.js 3D Globe Frontend:** Integrated React Three Fiber for interactive 3D visualization of satellite fleets and conjunctions.
- **Local TLE Data Fetching:** Added static fallback for local caching of Space-Track 3LE data to bypass cloud IP bans.
- **Dynamic Conjunction Analysis:** Implemented random sampling for mock top 5 conjunction events with a UI refresh feature.
- **Orbital Mechanics Engine:** Fully vectorized SGP4 propagation mapped to React Three Fiber instanced meshes.
- **Enterprise Web Stack:** Decoupled FastAPI backend and Next.js 3D React Three Fiber frontend for interactive visualizations and system-to-system integrations.
- **Background Workers:** Celery + Redis architecture for handling heavy physics tasks without blocking the API.

### Changed
- **Physics Rendering Performance:** Optimized the Globe.tsx UPDATE_CHUNKS parameter to significantly reduce CPU overhead on client browsers.
- **Mypy Type Checking:** Resolved strict dimensional assignment errors in 3D coordinate meshes.

### Added
- **Initial Production Release:** OURE (Orbital Uncertainty & Risk Engine) is now stable and ready for enterprise deployment.
- **Physics Engine:** Native SGP4 propagation combined with a High Precision Orbit Propagator (HPOP) featuring J2 oblateness, Solar Radiation Pressure (SRP), and atmospheric drag perturbations.
- **Risk Calculation:** Implementation of the Foster $P_c$ algorithm on the 2D B-plane, and the Alfano (2005) Maximum Probability method for worst-case non-linear geometries.
- **CCSDS Export:** Added `oure export-ephemeris` command for generating OEM (Orbit Ephemeris Message) KVN trajectories.
- **Cross-Validation:** Added an optional backend wrapper for the Java-based `orekit` package for enterprise-level validation.
- **Collision Avoidance:** Interactive `oure avoid` command featuring a step-by-step guide and SLSQP optimization for finding minimum-fuel 3D Delta-V vectors.
- **NASA Standard Breakup Model:** `oure shatter` command to simulate hypervelocity collisions and debris cloud dispersion.
- **Distributed Fleet Screening:** `oure analyze-fleet` command for parallel 1-vs-N catalog screening across the entire Space-Track NORAD database using modern `gp` endpoints.
- **Enterprise Web Stack:** Decoupled FastAPI backend and Next.js 3D React Three Fiber frontend for interactive visualizations and system-to-system integrations.
- **Background Workers:** Celery + Redis architecture for handling heavy physics tasks without blocking the API.
- **TraCSS Autonomous Negotiation:** Implementation of the emerging 2025 Space Traffic Coordination standards for operator-to-operator machine negotiation of maneuvers.
- **CI/CD Pipeline:** Automated GitHub Actions workflows for building and publishing Python wheels and Docker images to `ghcr.io`.

### Changed
- **Dependencies:** Consolidated all optional dev/web dependencies into the main installation block for universal CLI distribution.
- **Infrastructure:** Consolidated all background services (API, Grafana, Prometheus) behind an NGINX reverse proxy on Port 80.
- **Distribution:** Configured PyPI Trusted Publishing via GitHub Actions for automated `pip install oure` deployment.
