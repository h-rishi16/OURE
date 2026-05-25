# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-21

### Added
- **Initial Production Release:** OURE (Orbital Uncertainty & Risk Engine) is now stable and ready for enterprise deployment.
- **Physics Engine:** Native SGP4 propagation combined with a High Precision Orbit Propagator (HPOP) featuring J2 oblateness, Solar Radiation Pressure (SRP), and atmospheric drag perturbations.
- **Risk Calculation:** Implementation of the Foster $P_c$ algorithm on the 2D B-plane.
- **Collision Avoidance:** Interactive `oure avoid` command featuring a step-by-step guide and SLSQP optimization for finding minimum-fuel 3D Delta-V vectors.
- **NASA Standard Breakup Model:** `oure shatter` command to simulate hypervelocity collisions and debris cloud dispersion.
- **Distributed Fleet Screening:** `oure analyze-fleet` command for parallel 1-vs-N catalog screening across the entire Space-Track NORAD database using modern `gp` endpoints.
- **Enterprise Web Stack:** Decoupled FastAPI + HTMX dashboard for interactive visualizations and system-to-system integrations.
- **Background Workers:** Celery + Redis architecture for handling heavy physics tasks without blocking the API.
- **TraCSS Autonomous Negotiation:** Implementation of the emerging 2025 Space Traffic Coordination standards for operator-to-operator machine negotiation of maneuvers.
- **CI/CD Pipeline:** Automated GitHub Actions workflows for building and publishing Python wheels and Docker images to `ghcr.io`.
