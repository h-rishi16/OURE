# OURE Testing Guide

This document outlines how to run the automated unit testing suite and performance benchmarks for the OURE (Orbital Uncertainty & Risk Engine) project.

## Prerequisites
Ensure your virtual environment is activated and dependencies are installed. You should be in the root `oure/` project directory.
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (including dev/test tools)
pip install -e '.[dev]'
```

## Running the Automated Test Suite
OURE uses `pytest` for unit testing across all decoupled layers.

### Run All Tests
To execute the entire test suite (Core Models, Physics Propagators, Uncertainty propagation, and Conjunction Assessment):
```bash
pytest tests/
```

### Run Specific Test Modules
If you are developing a specific component, you can target its test file:
```bash
# Test core frozen dataclass models
pytest tests/unit/test_models.py

# Test the Physics Engine (SGP4, Numerical, Atmospheric Drag)
pytest tests/unit/test_sgp4.py tests/unit/test_advanced_physics.py

# Test STM Calculations and Covariance Propagation
pytest tests/unit/test_stm.py

# Test KD-Tree spatial screening and Foster/Chan Probability of Collision
pytest tests/unit/test_spatial_index.py tests/unit/test_fuzz_foster.py
```

### Test Flags
- **Verbose output:** `pytest -v tests/`
- **Output Python Print statements:** `pytest -s tests/`
- **Stop on first failure:** `pytest -x tests/`
