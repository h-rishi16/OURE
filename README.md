<div align="center">

# OURE
### Orbital Uncertainty & Risk Engine

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
[![Deploy Status](https://img.shields.io/github/actions/workflow/status/h-rishi16/oure/deploy.yml?style=for-the-badge&logo=github&label=Deploy)](https://github.com/h-rishi16/oure/actions)
[![Test Status](https://img.shields.io/github/actions/workflow/status/h-rishi16/oure/ci.yml?style=for-the-badge&logo=pytest&label=Tests)](https://github.com/h-rishi16/oure/actions)
![Stars](https://img.shields.io/github/stars/h-rishi16/oure?style=for-the-badge&color=yellow)
![License](https://img.shields.io/github/license/h-rishi16/oure?style=for-the-badge)

*A high-performance, enterprise-grade Space Situational Awareness (SSA) platform designed for orbital risk prediction, collision avoidance optimization, fragmentation modeling, and massive fleet screening.*

<img src="https://upload.wikimedia.org/wikipedia/commons/b/b4/GPS_Satellite_Constellation_Animation.gif" alt="Orbital Fleet Constellation" width="500" style="border-radius: 10px; margin: 20px 0;"/>

[Explore the Live Demo](https://oure-pi.vercel.app) · [Report Bug](https://github.com/h-rishi16/oure/issues/new?template=bug_report.md)

</div>

---

## Mission Brief

Built for mission-critical speed and mathematical rigor, OURE processes **Space-Track Two-Line Elements (TLEs)**, **NASA CDDIS data**, and **CCSDS Conjunction Data Messages (CDMs)**. It propagates uncertainty using vectorized Monte Carlo simulations and evaluates Probability of Collision ($P_c$) using Foster's algorithm on the encounter B-plane.

## Core Capabilities

- **Multi-Fidelity Physics Engine:** Native SGP4 propagation combined with a High Precision Orbit Propagator (HPOP) featuring J2 oblateness, Solar Radiation Pressure (SRP), and atmospheric drag perturbations.
- **NASA-Grade Integration:** Supports parsing NASA CDDIS CPF (Satellite Laser Ranging) files for centimeter-level accuracy and implements a simplified exponential atmospheric density fit inspired by the Jacchia model for solar flux drag modifications.
- **Collision Avoidance (SLSQP):** Mathematical maneuver optimization to find minimum-fuel 3D Delta-V vectors that mitigate collision risk below safety thresholds.
- **NASA Standard Breakup Model (Simplified):** Simplified simulation of hypervelocity impacts and debris cloud dispersion inspired by the NASA Standard Breakup Model.
- **Sensor Fusion:** Linear Joseph-form covariance updates with Schmidt consider-parameters (Schmidt-Kalman Filter) to simulate commercial radar tasking and covariance collapse.
- **KD-Tree Fleet Screening:** Distributed epoch-bucketed $O(N \log N)$ screening of entire satellite constellations against the full NORAD catalog.

## Mission Control (UI & Observability)

- **Enterprise Observability:** Fully instrumented FastAPI REST API and Celery/Redis background workers, seamlessly integrated with **Prometheus and Grafana** for real-time physics engine throughput and risk quantification latency monitoring.
- **Interactive Visualizations:** 3D ECI encounter geometry and massive orbital fleet visualization using Next.js, React Three Fiber, and Three.js.
  - **Hybrid CPU/GPU Engine:** Offloads rendering for 30,000+ active satellites to a custom WebGL Vertex Shader for buttery-smooth 144Hz performance, while retaining precise CPU-based spatial raycasting for click interactions.
  - **High-Fidelity Planetary Data:** Renders Earth using high-resolution (50m) topographical GeoJSON borders for exact geographical precision.

---

## Launch Codes (Installation)

OURE can be run locally via CLI, launched via a lightweight web interface, or deployed as a full enterprise microservice stack.

### 1. Local Mission Control (CLI & Web)

You can install OURE globally using `pip` (or `uv`):

```bash
# Install the OURE backend package and its dependencies
pip install oure

# Start the FastAPI backend
uvicorn oure.api.main:app --reload

# In a new terminal, start the Next.js 3D Frontend
cd frontend
npm install
npm run dev
```

### 2. Enterprise Fleet Stack (Docker Compose)

For production environments, OURE deploys as a fully isolated 6-service stack including the API, Background Workers, Redis Broker, Operations Dashboard, Prometheus metrics, and a Grafana observability suite.

```bash
# Clone the repository for the Enterprise Stack
git clone https://github.com/h-rishi16/oure.git
cd oure

# Start the full Enterprise Stack
docker compose up --build -d
```

- **Operations Dashboard (Next.js 3D Globe):** [http://localhost](http://localhost)
- **API Documentation:** [http://localhost/api/docs](http://localhost/api/docs)
- **Grafana (Observability):** [http://localhost/grafana](http://localhost/grafana) *(Login: admin / admin)*
- **Prometheus Metrics:** [http://localhost/prometheus](http://localhost/prometheus)

### 3. Continuous Deployment (CI/CD)

OURE is configured with a fully automated, RAM-optimized deployment pipeline via **GitHub Actions**.
Any commit pushed to the `main` branch automatically triggers a deployment to the production server:
1. GitHub runners compile the heavily optimized Next.js `standalone` build.
2. Build artifacts are securely transferred to the remote server via SSH tar archives (preventing memory exhaustion on micro-VMs).
3. The server safely rebuilds the Docker container with `--no-cache` and restarts the Nginx reverse proxy.

---

## Ground Station Terminal (CLI)

### 1. Analyze a Conjunction
Assess the collision probability between two orbiting objects.
```bash
oure analyze --primary 25544 --secondary 43205 --look-ahead 72
```

### 2. Avoidance Maneuver Wizard
Starts an interactive guide to optimize a fuel-efficient burn:
```bash
oure avoid --primary 25544 --secondary 43205
```

### 3. Fleet Screening
Screen thousands of secondaries against a fleet of primaries in parallel:
```bash
oure analyze-fleet --primaries-file p.json --secondaries-file s.json --workers 8
```

### 4. Space Debris Fragmentation
Simulate a "What-if" collision between two objects:
```bash
oure shatter --primary 25544 --secondary 43205 --fragments 5000
```

---

## Spacecraft Architecture & Security

OURE enforces a strict, decoupled 5-layer architecture, hardened against Resource Exhaustion (DoS) and Numerical Singularities:
1. **Core:** Immutable data models (`StateVector`, `CovarianceMatrix`) and Prometheus Metrics Managers.
2. **Data:** Caching fetchers (`SpaceTrack`, `NOAA F10.7`), `NASA CDDIS CPF` parsing, and strict CCSDS `CDM Parser`.
3. **Physics:** Certified SGP4, RK45 Numerical integrators, NASA MSFC Atmospheric modeling, and SRP.
4. **Uncertainty:** Memory-hardened Vectorized Monte Carlo ensembles (capped at 100k samples), STM generation, and EKF Sensor updates.
5. **Conjunction/Risk:** TCA Golden-section search, Robust Foster $P_c$ math utilizing Moore-Penrose pseudo-inverses (`np.linalg.pinv`) to prevent singular matrix crashes, and SLSQP maneuver optimization.

---

## Flight Readiness (Testing & Quality)

OURE maintains strict engineering standards, verified by GitHub Actions CI/CD:
- **Test Coverage:** 83%+ measured via `pytest-cov` across 50+ test files and 140+ individual tests.
- **Static Analysis:** Strict `mypy` typing and `ruff` linting.
- **Numerical Stability:** Joseph-form covariance updates, eigenvalue-ordered risk projection with singularity protection.

```bash
uv run pytest tests/ -v --cov=oure
```

---

## AI Automaton Fleet (Issue Triage)

This repository is equipped with **Jules AI Fleet Automation**. If you open an issue, an AI agent may automatically pick it up, plan a fix, write the code, and submit a Pull Request—like a swarm of autonomous repair drones maintaining a space station.

*To enable this, the repository owner must set `JULES` in the GitHub Actions Secrets.*

---

<div align="center">
  <p><b>License</b></p>
  <p>OURE is released under the MIT License.</p>
  <p><i>"Ad astra per aspera"</i></p>
</div>
