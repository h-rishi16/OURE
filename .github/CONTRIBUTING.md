# Contributing to OURE

Thank you for your interest in contributing to the Orbital Uncertainty & Risk Engine (OURE). We welcome contributions from aerospace engineers, data scientists, and software developers to help improve orbital risk assessment.

## Development Environment Setup

OURE uses a robust toolchain to ensure code quality and mathematical correctness.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/h-rishi16/OURE.git
    cd OURE
    ```

2.  **Set up the environment:**
    We use standard Python packaging to simplify environment setup. This will create a `.venv` and install all dependencies.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e '.[dev,web]'
    ```

3.  **Run the test suite:** OURE enforces a strict 88% minimum coverage requirement.
    ```bash
    pytest tests/ -v --cov=oure
    ```
4.  **Run static analysis:** We use `ruff` for linting and `mypy` for strict type checking.
    ```bash
    ruff check oure/ tests/
    mypy oure/
    ```

## Pull Request Checklist

Before opening a PR, ensure:
*   [ ] You have added tests for any new physics models or features.
*   [ ] `pytest` passes with 100% success and >88% coverage.
*   [ ] `ruff` and `mypy` report zero errors.
*   [ ] Architectural layer boundaries are respected (verified by `test_architecture.py`).

## Architectural Guidelines

OURE uses a strict 5-layer decoupled architecture. If you are adding new features, please respect these boundaries:
*   `core/`: Immutable data models. Cannot import from any other layer.
*   `data/`: Ingestion and caching.
*   `physics/`: Propagators and transformations.
*   `conjunction/`: Screening and TCA algorithms. (May import from `physics/`).
*   `risk/`: B-Plane projection and probability calculations. (May import from `physics/`).
*   `uncertainty/`: Covariance propagation and Monte Carlo. (May import from `physics/`).

Thank you for contributing to safer space operations!
