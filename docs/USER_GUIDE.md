# OURE User Guide: Features & Examples

Welcome to the Orbital Uncertainty & Risk Engine (OURE). This guide provides a detailed explanation of every major feature in the platform, along with concrete, runnable examples.

## 1. Data Ingestion & Caching
**What it does:** OURE needs up-to-date orbital elements (TLEs) and space weather data to accurately propagate orbits. It fetches satellite data from Space-Track.org and F10.7 solar flux data from NOAA, caching them locally in a high-speed SQLite database to minimize network latency.

**Example:** Fetch the latest Two-Line Elements for all satellites in Low Earth Orbit (LEO) and update the local cache.
```bash
oure fetch --all-leo
```
*(Note: Requires `SPACETRACK_USER` and `SPACETRACK_PASS` to be set in your `.env` file.)*

---

## 2. Single Conjunction Analysis
**What it does:** Calculates the Probability of Collision ($P_c$) between two specific space objects. It uses SGP4 and our High Precision Orbit Propagator (HPOP) to propagate the orbits to the Time of Closest Approach (TCA), projects their positional uncertainties onto the 2D encounter B-plane, and integrates the probability density function using Foster's algorithm.

**Example:** Analyze the collision risk between the International Space Station (25544) and a piece of space debris (e.g., 43205) over the next 72 hours.
```bash
oure analyze --primary 25544 --secondary 43205 --look-ahead 72
```

---

## 3. Fleet Screening (Distributed)
**What it does:** Scales the single conjunction analysis to an entire constellation of satellites. It uses an $O(N \log N)$ KD-Tree spatial index and Python's `ProcessPoolExecutor` to rapidly screen thousands of secondary objects against your primary assets in parallel across multiple CPU cores.

**Example:** Screen your fleet against a catalog of debris. First, create JSON files containing NORAD IDs:
```bash
echo '["25544"]' > primaries.json
echo '["41456", "43205"]' > secondaries.json

oure analyze-fleet --primaries-file primaries.json --secondaries-file secondaries.json --workers 8
```

---

## 4. Collision Avoidance (Maneuver Optimization)
**What it does:** If a high-risk conjunction is detected, this interactive wizard helps you plan an avoidance maneuver. It uses the SciPy SLSQP (Sequential Least Squares Programming) optimizer to calculate the minimum-fuel 3D Delta-V (thrust vector) required to push the collision risk below your safety threshold.

**Example:** Plan an avoidance maneuver for the ISS, instructing the optimizer to find a burn to execute 12 hours before TCA.
```bash
oure avoid --primary 25544 --secondary 43205
```

---

## 5. Debris Fragmentation Modeling
**What it does:** Simulates what happens if a collision actually occurs. It implements the NASA Standard Breakup Model to generate a cloud of debris fragments based on the impact energy (relative velocity and mass), allowing you to visualize the immediate aftermath of a hypervelocity impact.

**Example:** Simulate the ISS (mass 420,000 kg) colliding with a 200 kg satellite, generating 5,000 tracked fragments.
```bash
oure shatter --primary 25544 --secondary 43205 --mass1 420000 --mass2 200 --fragments 5000
```

---

## 6. PDF Report Generation
**What it does:** Generates formal, mission-ready PDF briefings for high-risk conjunction events. These reports include TCA, miss distance, risk probabilities, and orbital parameters, suitable for submission to mission controllers or regulatory bodies.

**Example:** Scan the cache for recent high-risk events and generate PDF reports for them.
```bash
oure report
```

---

## 7. Enterprise Web Dashboard & API
**What it does:** OURE isn't just a CLI. It includes a decoupled FastAPI REST backend and a dynamic HTMX frontend. This allows you to integrate OURE into larger enterprise systems, submit massive screening tasks to background Celery workers, and view interactive Plotly 3D visualizations in your browser.

**Example:** Launch the full enterprise stack locally (API, Celery workers, Redis, Prometheus, and Grafana) using Docker.
```bash
docker compose up --build -d
```
Then navigate to:
- **Operations Dashboard:** [http://localhost:8000/ui/](http://localhost:8000/ui/)
- **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Grafana Metrics:** [http://localhost:3000](http://localhost:3000)
