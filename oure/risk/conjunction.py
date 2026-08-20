import concurrent.futures
import multiprocessing

import numpy as np


def _process_chunk(
    chunk_pairs: list, satellites: list[dict], threshold: float
) -> list[tuple]:
    local_conjunctions = []
    for i, j in chunk_pairs:
        path_i = satellites[i]["path"]
        path_j = satellites[j]["path"]
        dist = np.linalg.norm(path_i - path_j, axis=1)
        min_dist = np.min(dist)
        if min_dist < threshold:
            local_conjunctions.append(
                (satellites[i]["id"], satellites[j]["id"], float(min_dist))
            )
    return local_conjunctions


def check_conjunctions(
    satellites: list[dict], threshold: float = 10.0, workers: int | None = None
) -> list[tuple]:
    num_sats = len(satellites)
    if num_sats == 0:
        return []
    min_coords = np.array([s["min_coords"] for s in satellites])
    max_coords = np.array([s["max_coords"] for s in satellites])
    overlap = (min_coords[:, None, :] <= max_coords[None, :, :]) & (
        max_coords[:, None, :] >= min_coords[None, :, :]
    )
    overlap_all_dims = np.all(overlap, axis=2)
    i_idx, j_idx = np.where(overlap_all_dims)
    valid_pairs = [(int(i), int(j)) for i, j in zip(i_idx, j_idx, strict=True) if i < j]
    if not valid_pairs:
        return []
    if workers is None:
        workers = multiprocessing.cpu_count()
    chunk_size = max(1, len(valid_pairs) // workers)
    chunks = [
        valid_pairs[i : i + chunk_size] for i in range(0, len(valid_pairs), chunk_size)
    ]
    conjunctions = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_process_chunk, chunk, satellites, threshold)
            for chunk in chunks
        ]
        for future in concurrent.futures.as_completed(futures):
            conjunctions.extend(future.result())
    conjunctions.sort(key=lambda x: (x[0], x[1]))
    return conjunctions
