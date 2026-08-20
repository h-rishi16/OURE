import time
from datetime import UTC, datetime

import numpy as np

from oure.core.models import ConjunctionEvent, CovarianceMatrix, StateVector
from oure.risk.calculator import RiskCalculator

state_p = StateVector(
    r=np.array([7000.0, 0, 0]),
    v=np.array([0, 7.5, 0]),
    epoch=datetime.now(UTC),
    sat_id="P",
)
state_s = StateVector(
    r=np.array([7000.1, 0, 0]),
    v=np.array([0, 7.5, 0.01]),
    epoch=datetime.now(UTC),
    sat_id="S",
)
cov_p = CovarianceMatrix(matrix=np.eye(6) * 0.01, epoch=datetime.now(UTC), sat_id="P")
cov_s = CovarianceMatrix(matrix=np.eye(6) * 0.01, epoch=datetime.now(UTC), sat_id="S")

event = ConjunctionEvent(
    primary_id="P",
    secondary_id="S",
    tca=datetime.now(UTC),
    miss_distance_km=0.1,
    relative_velocity_km_s=0.01,
    primary_state=state_p,
    secondary_state=state_s,
    primary_covariance=cov_p,
    secondary_covariance=cov_s,
)

# Test Foster Series
calc = RiskCalculator()
calc.pc_calculator.method = "series"  # PcMethod.FOSTER_SERIES
start = time.perf_counter()
res = calc.compute_pc(event)
end = time.perf_counter()

print(f"Time taken (Series): {(end-start)*1000:.2f} ms")
print(f"Pc: {res.pc}")
