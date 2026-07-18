## OURE v1.0.0 — Software Version Description

**Release date**: 2026-05-27
**Software class**: NASA Class D (Research Support)
**Governing standard**: NPR 7150.2D

### Summary of changes
This is the official initial production release of OURE (Orbital Uncertainty & Risk Engine), built for mission-critical SSA. The release consolidates all optional dependencies into a universal PyPI CLI distribution (`pip install oure`) and routes all Enterprise Stack microservices through a unified NGINX reverse proxy on Port 80. PyPI Trusted Publishing is now configured for automated, secure deployments.

### New requirements addressed
| Requirement | Description |
|------------|-------------|
| REQ-OPS-03 | The system shall securely route all microservices through a unified NGINX reverse proxy on a single port. |

### Known limitations
- Hypothesis-based integration tests currently execute slowly due to `scipy.integrate.dblquad` overhead.

### Data sources
- Space-Track.org TLE catalog
- NOAA Space Weather Prediction Center (F10.7)
- NASA CDDIS CPF (Satellite Laser Ranging)

### Verification
- Test coverage: 86.18%
- mypy strict: PASS
- ruff: PASS
- CI: GitHub Actions (Python 3.11, 3.12, 3.13)
