"""
OURE Conjunction Assessment - Assessor
======================================
Orchestrator for the conjunction assessment process.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import numpy as np

from oure.core.models import ConjunctionEvent, CovarianceMatrix, StateVector
from oure.physics.base import BasePropagator

from .spatial_index import KDTreeSpatialIndex
from .tca_finder import TCARefinementEngine

logger = logging.getLogger("oure.conjunction.assessor")


class ConjunctionAssessor:
    """
    Two-stage conjunction detection orchestrator.
    """

    def __init__(
        self,
        screening_distance_km: float = 5.0,
        tca_time_step_s: float = 30.0,
        tca_refinement_tol_s: float = 0.1,
    ):
        self.screening_distance = screening_distance_km
        self.tca_time_step_s = tca_time_step_s
        self.tca_finder = TCARefinementEngine(tolerance_seconds=tca_refinement_tol_s)

    def _proximity_filter(
        self,
        primary: StateVector,
        primary_propagator: BasePropagator,
        secondaries: list[tuple[StateVector, CovarianceMatrix, BasePropagator]],
        time_offsets: list[float],
        t0: datetime,
    ) -> dict[int, tuple[datetime, datetime]]:
        """Stage 1: Coarse spatial filtering using KD-Trees or Vectorized norms."""
        candidate_pairs: dict[int, tuple[datetime, datetime]] = {}
        n_sec = len(secondaries)
        n_times = len(time_offsets)

        epochs = [t0 + timedelta(seconds=dt) for dt in time_offsets]

        # Pre-propagate primary for all epochs
        p_states = primary_propagator.propagate_sequence(primary, epochs)
        p_positions = np.array([s.r for s in p_states])

        sec_positions_all = np.zeros((n_times, n_sec, 3))

        for idx, (s_state, _, s_prop) in enumerate(secondaries):
            try:
                s_states = s_prop.propagate_sequence(s_state, epochs)
                sec_positions_all[:, idx, :] = np.array([s.r for s in s_states])
            except Exception as e:
                logger.warning(
                    f"Batch propagation failed for secondary index {idx}: {e}. Moving object far away."
                )
                sec_positions_all[:, idx, :] = (1e9, 1e9, 1e9)

        last_tree_epoch: datetime | None = None
        current_index: KDTreeSpatialIndex | None = None

        for t_idx, epoch in enumerate(epochs):
            p_pos = p_positions[t_idx]
            sec_positions = sec_positions_all[t_idx]

            if n_sec > 500:
                if (
                    current_index is None
                    or last_tree_epoch is None
                    or (epoch - last_tree_epoch).total_seconds() >= 300
                ):
                    current_index = KDTreeSpatialIndex(sec_positions)
                    last_tree_epoch = epoch

                close_indices = current_index.query_radius(
                    p_pos, radius_km=self.screening_distance
                )
            else:
                dists = np.linalg.norm(sec_positions - p_pos, axis=1)
                close_indices = np.where(dists <= self.screening_distance)[0].tolist()

            for idx in close_indices:
                if idx not in candidate_pairs:
                    candidate_pairs[int(idx)] = (epoch, epoch)
                else:
                    t_min, t_max = candidate_pairs[int(idx)]
                    candidate_pairs[int(idx)] = (min(t_min, epoch), max(t_max, epoch))

        return candidate_pairs

    def _golden_section_refinement(
        self,
        primary: StateVector,
        primary_cov: CovarianceMatrix,
        primary_propagator: BasePropagator,
        secondaries: list[tuple[StateVector, CovarianceMatrix, BasePropagator]],
        candidate_pairs: dict[int, tuple[datetime, datetime]],
    ) -> list[ConjunctionEvent]:
        """Stage 2: High precision refinement using golden-section search."""
        conjunction_events: list[ConjunctionEvent] = []
        margin = timedelta(seconds=self.tca_time_step_s)

        for sec_idx, (t_start, t_end) in candidate_pairs.items():
            s_state, s_cov, s_prop = secondaries[sec_idx]

            tca_result = self.tca_finder.find_tca(
                primary,
                primary_propagator,
                s_state,
                s_prop,
                t_start - margin,
                t_end + margin,
            )

            if tca_result:
                tca_epoch, miss_distance = tca_result
                if miss_distance <= self.screening_distance:
                    p_tca = primary_propagator.propagate_to(primary, tca_epoch)
                    s_tca = s_prop.propagate_to(s_state, tca_epoch)
                    v_rel = float(np.linalg.norm(p_tca.v - s_tca.v))

                    event = ConjunctionEvent(
                        primary_id=primary.sat_id,
                        secondary_id=s_state.sat_id,
                        tca=tca_epoch,
                        miss_distance_km=miss_distance,
                        relative_velocity_km_s=v_rel,
                        primary_state=p_tca,
                        secondary_state=s_tca,
                        primary_covariance=primary_cov,
                        secondary_covariance=s_cov,
                    )
                    conjunction_events.append(event)

        return conjunction_events

    def find_conjunctions(
        self,
        primary: StateVector,
        primary_cov: CovarianceMatrix,
        primary_propagator: BasePropagator,
        secondaries: list[tuple[StateVector, CovarianceMatrix, BasePropagator]],
        look_ahead_hours: float = 72.0,
    ) -> list[ConjunctionEvent]:
        """
        Screen primary against all secondaries over a look-ahead window.
        """
        n_steps = int(look_ahead_hours * 3600 / self.tca_time_step_s)
        t0 = primary.epoch
        time_offsets = [i * self.tca_time_step_s for i in range(n_steps)]

        logger.info(
            f"Screening {len(secondaries)} objects over {look_ahead_hours}h ({n_steps} steps)"
        )

        candidate_pairs = self._proximity_filter(
            primary, primary_propagator, secondaries, time_offsets, t0
        )
        logger.info(f"Stage 1 found {len(candidate_pairs)} candidate pairs")

        conjunction_events = self._golden_section_refinement(
            primary, primary_cov, primary_propagator, secondaries, candidate_pairs
        )

        conjunction_events.sort(key=lambda e: e.miss_distance_km)
        logger.info(f"Stage 2 produced {len(conjunction_events)} conjunction events")
        return conjunction_events

    def find_conjunctions_parallel(
        self,
        primary: StateVector,
        primary_cov: CovarianceMatrix,
        primary_propagator: BasePropagator,
        secondaries: list[tuple[StateVector, CovarianceMatrix, BasePropagator]],
        duration_s: float,
        workers: int | None = None,
    ) -> list[ConjunctionEvent]:
        """
        Parallelized version of find_conjunctions.
        """
        import concurrent.futures
        import multiprocessing

        if workers is None:
            workers = multiprocessing.cpu_count()

        chunk_size = max(1, len(secondaries) // workers)
        chunks = [
            secondaries[i : i + chunk_size]
            for i in range(0, len(secondaries), chunk_size)
        ]

        conjunction_events: list[ConjunctionEvent] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    self.find_conjunctions,
                    primary,
                    primary_cov,
                    primary_propagator,
                    chunk,
                    duration_s / 3600.0,
                )
                for chunk in chunks
            ]
            for future in concurrent.futures.as_completed(futures):
                conjunction_events.extend(future.result())

        conjunction_events.sort(key=lambda e: e.miss_distance_km)
        return conjunction_events
