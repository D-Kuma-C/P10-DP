from __future__ import annotations
from typing import Callable, List, Tuple
from geometry import Point, Trajectory, euclidean_dist, get_distance_travelled
from tqdm import tqdm

def get_data_boundaries(data: List[Trajectory]) -> List[float]:
    data_min_x = float("inf")
    data_min_y = float("inf")
    data_max_x = float("-inf")
    data_max_y = float("-inf")
    for traj in data:
        if not traj:
            continue
        xs = [p[0] for p in traj]
        ys = [p[1] for p in traj]
        data_min_x = min(data_min_x, min(xs))
        data_max_x = max(data_max_x, max(xs))
        data_min_y = min(data_min_y, min(ys))
        data_max_y = max(data_max_y, max(ys))
    return [data_min_x, data_max_x, data_min_y, data_max_y]

def get_outlier_indices(scores: List[float], number: int, exact_adatrace: bool = True) -> List[int]:
    """Return indices of top outliers. exact_adatrace=True preserves scoresList.indexOf tie behavior."""
    if number <= 0:
        return []
    n = min(number, len(scores))
    if exact_adatrace:
        copy = sorted(scores)
        outlier_indices = []
        for i in range(n):
            search_for_val = copy[len(copy) - 1 - i]
            outlier_indices.append(scores.index(search_for_val))
        return outlier_indices
    return sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)[:n]

def get_outlier_trajs(trajs: List[Trajectory], scores: List[float], number: int, exact_adatrace: bool = True) -> List[Trajectory]:
    return [trajs[i] for i in get_outlier_indices(scores, number, exact_adatrace)]

def brute_force_knn_indices(points: List[Tuple[float, ...]], target: Tuple[float, ...], k: int, include_self: bool = True, self_index: int | None = None) -> List[int]:
    distances = []
    for idx, point in enumerate(points):
        if not include_self and self_index is not None and idx == self_index:
            continue
        dist = sum((a - b) ** 2 for a, b in zip(point, target)) ** 0.5
        distances.append((dist, idx))
    distances.sort(key=lambda item: item[0])
    return [idx for _, idx in distances[: min(k, len(distances))]]

def start_point(traj: Trajectory) -> Point:
    return traj[0]

def end_point(traj: Trajectory) -> Point:
    return traj[-1]

def average_knn_point_scores(
    trajs: List[Trajectory],
    point_getter_for_tree: Callable[[Trajectory], Point],
    point_getter_for_query: Callable[[Trajectory], Point],
    point_getter_for_distance: Callable[[Trajectory], Point],
    top_k_neighbors: int,
    desc: str = "Scoring kNN point outliers",
    include_self: bool = True,
) -> List[float]:
    tree_points = [tuple(point_getter_for_tree(traj)) for traj in trajs]
    iterator = tqdm(range(len(trajs)), total=len(trajs), desc=desc)
    scores = [0.0 for _ in trajs]
    for i in iterator:
        target = tuple(point_getter_for_query(trajs[i]))
        nbr_indices = brute_force_knn_indices(tree_points, target, top_k_neighbors, include_self=include_self, self_index=i)
        this_point = point_getter_for_distance(trajs[i])
        total = 0.0
        for j in nbr_indices:
            total += euclidean_dist(this_point, point_getter_for_distance(trajs[j]))
        scores[i] = total / len(nbr_indices) if nbr_indices else 0.0
    return scores

def average_knn_length_scores(trajs: List[Trajectory], top_k_neighbors: int, desc: str = "Scoring kNN length outliers", include_self: bool = True) -> List[float]:
    lengths = [get_distance_travelled(traj) for traj in trajs]
    tree_points = [(length,) for length in lengths]

    iterator = tqdm(range(len(trajs)), total=len(trajs), desc=desc)
    scores = [0.0 for _ in trajs]
    for i in iterator:
        nbr_indices = brute_force_knn_indices(tree_points, (lengths[i],), top_k_neighbors, include_self=include_self, self_index=i)
        total = sum(abs(lengths[i] - lengths[j]) for j in nbr_indices)
        scores[i] = total / len(nbr_indices) if nbr_indices else 0.0
    return scores
