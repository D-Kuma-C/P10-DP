from __future__ import annotations

from math import sqrt
from typing import Any, Dict, List, Optional
from tqdm import tqdm
import random

from geometry import Grid, Trajectory, euclidean_dist, get_distance_travelled
from grid_conversion import convert_all_to_grid_trajs
from outlier_utils import (
    average_knn_length_scores,
    average_knn_point_scores,
    end_point,
    get_data_boundaries,
    get_outlier_indices,
    start_point,
)
from trajectory_metrics import calculate_dtw


def sample_originals_for_plausible_deniability(original_trajs, sample_size, random_state):
    if sample_size is None or sample_size <= 0:
        return original_trajs

    if len(original_trajs) <= sample_size:
        return original_trajs

    rng = random.Random(random_state)
    return rng.sample(original_trajs, sample_size)


def _progress(iterable, show_progress: bool, desc: str, total: Optional[int] = None, leave: bool = True):
    if not show_progress:
        return iterable
    return tqdm(iterable, total=total, desc=desc, leave=leave)


def _max_possible_xy_distance(orig_xy: List[Trajectory]) -> float:
    min_x, max_x, min_y, max_y = get_data_boundaries(orig_xy)
    return sqrt((max_x - min_x) ** 2 + (max_y - min_y) ** 2)


def _point_pd_check(tout, orig_xy, point_kind, closest_threshold, kappa, beta, max_possible_distance,
                    show_progress_inner=False, desc="Checking plausible deniability") -> Dict[str, Any]:
    if point_kind == "start":
        tout_point = tout[0]
        getter = lambda traj: traj[0]
    elif point_kind == "end":
        tout_point = tout[-1]
        getter = lambda traj: traj[-1]
    else:
        raise ValueError("point_kind must be 'start' or 'end'")

    min_dist = float("inf")
    closest_orig_index = -1
    for idx, tcand in enumerate(orig_xy):
        curr_dist = euclidean_dist(tout_point, getter(tcand))
        if curr_dist < min_dist:
            min_dist = curr_dist
            closest_orig_index = idx

    threshold = max_possible_distance * closest_threshold
    if min_dist > threshold:
        return {"failed": False, "pass_reason": "closest_original_farther_than_threshold",
                "min_dist": min_dist, "threshold": threshold, "closest_orig_index": closest_orig_index,
                "currk": None}

    second_threshold = max_possible_distance * beta
    currk = 0
    iterator = _progress(orig_xy, show_progress_inner, desc=desc, total=len(orig_xy), leave=False)
    for tclosecand in iterator:
        distv = euclidean_dist(tout_point, getter(tclosecand))
        if abs(distv - min_dist) <= second_threshold:
            currk += 1
        if currk >= kappa:
            return {"failed": False, "pass_reason": "plausible_deniability_satisfied",
                    "min_dist": min_dist, "threshold": threshold, "second_threshold": second_threshold,
                    "closest_orig_index": closest_orig_index, "currk": currk}

    return {"failed": True, "pass_reason": None, "min_dist": min_dist, "threshold": threshold,
            "second_threshold": second_threshold, "closest_orig_index": closest_orig_index, "currk": currk}


def _length_pd_check(tout, orig_xy, closest_threshold, kappa, beta, max_possible_distance,
                     exact_adatrace, show_progress_inner=False, desc="Checking length plausible deniability") -> Dict[str, Any]:
    tout_len = get_distance_travelled(tout)
    min_dist = float("inf")
    closest_orig_index = -1
    for idx, tcand in enumerate(orig_xy):
        diff = get_distance_travelled(tcand) - tout_len
        curr_dist = diff if exact_adatrace else abs(diff)
        if curr_dist < min_dist:
            min_dist = curr_dist
            closest_orig_index = idx

    threshold = max_possible_distance * closest_threshold
    if min_dist > threshold:
        return {"failed": False, "pass_reason": "closest_original_farther_than_threshold",
                "min_dist": min_dist, "threshold": threshold, "closest_orig_index": closest_orig_index,
                "currk": None}

    second_threshold = max_possible_distance * beta
    currk = 0
    iterator = _progress(orig_xy, show_progress_inner, desc=desc, total=len(orig_xy), leave=False)
    for tclosecand in iterator:
        distv = abs(get_distance_travelled(tclosecand) - tout_len)
        if abs(distv - min_dist) <= second_threshold:
            currk += 1
        if currk >= kappa:
            return {"failed": False, "pass_reason": "plausible_deniability_satisfied",
                    "min_dist": min_dist, "threshold": threshold, "second_threshold": second_threshold,
                    "closest_orig_index": closest_orig_index, "currk": currk}

    return {"failed": True, "pass_reason": None, "min_dist": min_dist, "threshold": threshold,
            "second_threshold": second_threshold, "closest_orig_index": closest_orig_index, "currk": currk}


def _dtw_pd_check(tout, orig_xy, closest_threshold, kappa, beta,
                  show_progress_inner=False, desc="Checking DTW plausible deniability") -> Dict[str, Any]:
    min_dist = float("inf")
    max_dist = float("-inf")
    closest_orig_index = -1
    dtw_distances = []
    iterator = _progress(enumerate(orig_xy), show_progress_inner, desc=desc + " - DTW distances",
                         total=len(orig_xy), leave=False)
    for idx, tcand in iterator:
        curr_dist = calculate_dtw(tout, tcand)
        dtw_distances.append(curr_dist)
        if curr_dist < min_dist:
            min_dist = curr_dist
            closest_orig_index = idx
        if curr_dist > max_dist:
            max_dist = curr_dist

    threshold = max_dist * closest_threshold
    if min_dist > threshold:
        return {"failed": False, "pass_reason": "closest_original_farther_than_threshold",
                "min_dist": min_dist, "max_dist": max_dist, "threshold": threshold,
                "closest_orig_index": closest_orig_index, "currk": None}

    second_threshold = max_dist * beta
    currk = 0
    for distv in dtw_distances:
        if abs(distv - min_dist) <= second_threshold:
            currk += 1
        if currk >= kappa:
            return {"failed": False, "pass_reason": "plausible_deniability_satisfied",
                    "min_dist": min_dist, "max_dist": max_dist, "threshold": threshold,
                    "second_threshold": second_threshold, "closest_orig_index": closest_orig_index,
                    "currk": currk}

    return {"failed": True, "pass_reason": None, "min_dist": min_dist, "max_dist": max_dist,
            "threshold": threshold, "second_threshold": second_threshold,
            "closest_orig_index": closest_orig_index, "currk": currk}


def _record_stage_summary(stage_name: str, outlier_indices: List[int], failed_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    failed_indices = [event["synthetic_index"] for event in failed_events]
    return {"stage": stage_name, "outlier_count_raw": len(outlier_indices),
            "outlier_count_unique": len(set(outlier_indices)), "failed_count_raw": len(failed_indices),
            "failed_count_unique": len(set(failed_indices)), "failed_indices_unique": sorted(set(failed_indices)),
            "failed_events": failed_events}


def _remove_failed_from_working_set(working_syn: List[Trajectory], failed_working_indices: List[int]) -> List[Trajectory]:
    failed_set = set(failed_working_indices)
    return [traj for idx, traj in enumerate(working_syn) if idx not in failed_set]


def _run_point_stage(stage_name, point_kind, orig_xy, working_syn, top_k_neighbors, n_outliers,
                     closest_threshold, kappa, beta, exact_adatrace, max_possible_distance, show_progress_inner):
    if point_kind == "start":
        scores = average_knn_point_scores(working_syn, start_point, start_point, start_point,
                                          top_k_neighbors, "Scoring trip-start outliers", True)
    else:
        query_getter = start_point if exact_adatrace else end_point
        scores = average_knn_point_scores(working_syn, end_point, query_getter, end_point,
                                          top_k_neighbors, "Scoring trip-end outliers", True)

    outlier_indices = get_outlier_indices(scores, n_outliers, exact_adatrace)
    failed_events = []
    iterator = _progress(outlier_indices, show_progress_inner, f"Checking {stage_name} plausible deniability", total=len(outlier_indices))
    for outlier_index in iterator:
        check = _point_pd_check(working_syn[outlier_index], orig_xy, point_kind, closest_threshold,
                                kappa, beta, max_possible_distance, show_progress_inner,
                                f"{stage_name} candidate {outlier_index}")
        if check["failed"]:
            failed_events.append({"stage": stage_name, "synthetic_index": outlier_index, **check})
    return _record_stage_summary(stage_name, outlier_indices, failed_events)


def _run_length_stage(orig_xy, working_syn, top_k_neighbors, n_outliers, closest_threshold, kappa, beta,
                      exact_adatrace, show_progress_inner):
    scores = average_knn_length_scores(working_syn, top_k_neighbors, "Scoring length outliers", True)
    outlier_indices = get_outlier_indices(scores, n_outliers, exact_adatrace)
    orig_lengths = [get_distance_travelled(t) for t in orig_xy]
    max_possible_distance = max(orig_lengths) - min(orig_lengths)
    failed_events = []
    iterator = _progress(outlier_indices, True, "Checking length plausible deniability", total=len(outlier_indices))
    for outlier_index in iterator:
        check = _length_pd_check(working_syn[outlier_index], orig_xy, closest_threshold, kappa, beta,
                                 max_possible_distance, exact_adatrace, show_progress_inner,
                                 f"Length candidate {outlier_index}")
        if check["failed"]:
            failed_events.append({"stage": "length", "synthetic_index": outlier_index, **check})
    return _record_stage_summary("length", outlier_indices, failed_events)


def _find_location_outliers(working_syn, n_outliers, exact_adatrace):
    min_x, max_x, min_y, max_y = get_data_boundaries(working_syn)
    syn_grid = Grid(25, min_x, max_x, min_y, max_y)
    syn_detailed = convert_all_to_grid_trajs(working_syn, syn_grid, True, True,
                                             "Converting synthetic trajectories to detailed 25x25 grid")
    cell_visits = {cell: 0 for cell in syn_grid.cells}
    iterator = _progress(syn_detailed, True, "Counting detailed-grid cell visits", total=len(syn_detailed))
    for grid_traj in iterator:
        for cell in grid_traj:
            cell_visits[cell] += 1

    # exact_adatrace=True preserves sortByValue descending. False uses intended rare-cell ascending sort.
    sorted_cell_items = sorted(cell_visits.items(), key=lambda item: item[1], reverse=exact_adatrace)
    rare_cells = []
    for cell, visits in sorted_cell_items:
        rare_cells.append(cell)
        if visits > n_outliers:
            break
    rare_cell_set = set(rare_cells)
    outlier_indices = []
    iterator = _progress(enumerate(syn_detailed), True, "Finding location-visit outlier candidates", total=len(syn_detailed))
    for i, grid_traj in iterator:
        for cell in grid_traj:
            if cell in rare_cell_set:
                outlier_indices.append(i)
                break
        if len(outlier_indices) >= n_outliers:
            break
    return {"outlier_indices": outlier_indices, "rare_cell_count": len(rare_cells),
            "rare_cells": [cell.name for cell in rare_cells],
            "detailed_grid_bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y}}


def _run_location_stage(orig_xy, working_syn, n_outliers, closest_threshold, kappa, beta,
                        exact_adatrace, show_progress_inner):
    candidate_info = _find_location_outliers(working_syn, n_outliers, exact_adatrace)
    outlier_indices = candidate_info["outlier_indices"]
    failed_events = []
    iterator = _progress(outlier_indices, True, "Checking location-visit DTW plausible deniability", total=len(outlier_indices))
    for outlier_index in iterator:
        check = _dtw_pd_check(working_syn[outlier_index], orig_xy, closest_threshold, kappa, beta,
                              show_progress_inner, f"Location candidate {outlier_index}")
        if check["failed"]:
            failed_events.append({"stage": "location_visit", "synthetic_index": outlier_index, **check})
    summary = _record_stage_summary("location_visit", outlier_indices, failed_events)
    summary["rare_cell_count"] = candidate_info["rare_cell_count"]
    summary["rare_cells"] = candidate_info["rare_cells"]
    summary["detailed_grid_bounds"] = candidate_info["detailed_grid_bounds"]
    return summary


def outlier_leakage_score_only(
    orig_xy: List[Trajectory],
    syn_xy: List[Trajectory],
    top_k_neighbors: int = 50,
    n_outliers: int = 200,
    closest_threshold: float = 0.1,
    plausible_deniability_kappa: int = 100,
    plausible_deniability_beta: float = 0.05,
    exact_adatrace: bool = True,
    mutate_like_java_between_stages: bool = True,
    show_progress_inner: bool = False,
    plausible_deniability_sample_size: Optional[int] = None,
    random_state: int = 0,
) -> Dict[str, Any]:
    """
    Score-only Python version of AdaTrace Outlier Leakage Defense.

    exact_adatrace=True preserves Java quirks/bugs:
      1. End outlier kNN stores end points but queries start points.
      2. Length closest distance uses signed difference.
      3. Location visit cells use provided sortByValue descending.

    exact_adatrace=False uses likely intended behavior for those three places.

    mutate_like_java_between_stages=True simulates removals between stages.
    No replacement trajectories are generated.
    """
    working_syn = list(syn_xy)
    original_count = len(syn_xy)
    max_possible_xy_distance = _max_possible_xy_distance(orig_xy)
    pd_orig_xy = sample_originals_for_plausible_deniability(
        orig_xy,
        sample_size=plausible_deniability_sample_size,
        random_state=random_state,
    )

    print(
        "Outlier plausible-deniability original sample:",
        f"{len(pd_orig_xy)} / {len(orig_xy)}"
    )
    stages = []
    removed_by_stage = []
    index_note = ("Indices are relative to the working synthetic dataset at each stage, "
                  "not stable original syn_xy indices, when mutate_like_java_between_stages=True.")

    start_summary = _run_point_stage(
        "start", "start", pd_orig_xy, working_syn, top_k_neighbors, n_outliers,
        closest_threshold, plausible_deniability_kappa, plausible_deniability_beta,
        exact_adatrace, max_possible_xy_distance, show_progress_inner
    )

    stages.append(start_summary)
    if mutate_like_java_between_stages:
        failed = start_summary["failed_indices_unique"]
        removed_by_stage.append({"stage": "start", "working_indices_removed": failed})
        working_syn = _remove_failed_from_working_set(working_syn, failed)

    end_summary = _run_point_stage(
        "end", "end", pd_orig_xy, working_syn, top_k_neighbors, n_outliers,
        closest_threshold, plausible_deniability_kappa, plausible_deniability_beta,
        exact_adatrace, max_possible_xy_distance, show_progress_inner
    )

    stages.append(end_summary)
    if mutate_like_java_between_stages:
        failed = end_summary["failed_indices_unique"]
        removed_by_stage.append({"stage": "end", "working_indices_removed": failed})
        working_syn = _remove_failed_from_working_set(working_syn, failed)

    length_summary = _run_length_stage(
        pd_orig_xy, working_syn, top_k_neighbors, n_outliers // 2,
        closest_threshold, plausible_deniability_kappa, plausible_deniability_beta,
        exact_adatrace, show_progress_inner
    )

    stages.append(length_summary)
    if mutate_like_java_between_stages:
        failed = length_summary["failed_indices_unique"]
        removed_by_stage.append({"stage": "length", "working_indices_removed": failed})
        working_syn = _remove_failed_from_working_set(working_syn, failed)

    location_summary = _run_location_stage(
        pd_orig_xy, working_syn, n_outliers, closest_threshold,
        plausible_deniability_kappa, plausible_deniability_beta,
        exact_adatrace, show_progress_inner
    )

    stages.append(location_summary)
    if mutate_like_java_between_stages:
        failed = location_summary["failed_indices_unique"]
        removed_by_stage.append({"stage": "location_visit", "working_indices_removed": failed})
        working_syn = _remove_failed_from_working_set(working_syn, failed)

    return {
        "parameters": {
            "top_k_neighbors": top_k_neighbors,
            "n_outliers": n_outliers,
            "closest_threshold": closest_threshold,
            "plausible_deniability_kappa": plausible_deniability_kappa,
            "plausible_deniability_beta": plausible_deniability_beta,
            "plausible_deniability_sample_size": plausible_deniability_sample_size,
            "plausible_deniability_actual_sample_size": len(pd_orig_xy),
            "random_state": random_state,
            "exact_adatrace": exact_adatrace,
            "mutate_like_java_between_stages": mutate_like_java_between_stages,
        },
        "original_synthetic_count": original_count,
        "final_working_synthetic_count_if_removed": len(working_syn),
        "estimated_removed_count_if_removed": original_count - len(working_syn),
        "total_failed_events": sum(stage["failed_count_raw"] for stage in stages),
        "sum_of_unique_failures_by_stage": sum(stage["failed_count_unique"] for stage in stages),
        "index_note": index_note,
        "removed_by_stage": removed_by_stage,
        "stages": stages,
    }
