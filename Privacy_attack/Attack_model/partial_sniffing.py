from __future__ import annotations

from math import inf
from typing import Any, Dict, List, Optional
from tqdm import tqdm

from Privacy_attack.geometry import Cell, Grid, Point, Trajectory
from Privacy_attack.grid_conversion import convert_all_to_grid_trajs, get_nth_densest_cell
from Privacy_attack.trajectory_metrics import calc_intersection_count, calculate_dtw


def get_sniffed_points(traj: Trajectory, sniff_zone: Cell) -> List[Point]:
    """
    Equivalent to Trajectory.getSniffedPoints.

    Returns the first contiguous segment of points inside sniff_zone.
    """
    pos = 0

    while pos < len(traj):
        if sniff_zone.in_cell(traj[pos]):
            sniffed: List[Point] = []
            sniff_pos = pos

            while sniff_pos < len(traj) and sniff_zone.in_cell(traj[sniff_pos]):
                sniffed.append(traj[sniff_pos])
                sniff_pos += 1

            return sniffed

        pos += 1

    return []


def partial_sniffing_score_only(
    orig_xy: List[Trajectory],
    syn_xy: List[Trajectory],
    grid: Grid,
    sniff_n: int = 12,
    sensitive_n: int = 10,
    sensitive_zone: Optional[Cell] = None,
    intersection_threshold: int = 5,
) -> Dict[str, Any]:
    """
    Score-only version of AdaTrace Partial Sniffing.

    This does NOT:
      - remove failing synthetic trajectories
      - generate replacement synthetic trajectories
      - mutate orig_xy
      - mutate syn_xy

    It identifies which synthetic trajectories would fail the sniffing defense.
    """

    orig_grid = convert_all_to_grid_trajs(
        trajs=orig_xy,
        grid=grid,
        interp_wanted=True,
        remove_duplicates=True,
        desc="Converting original trajectories",
    )

    syn_grid = convert_all_to_grid_trajs(
        trajs=syn_xy,
        grid=grid,
        interp_wanted=True,
        remove_duplicates=True,
        desc="Converting synthetic trajectories",
    )

    sniff_region = get_nth_densest_cell(
        orig_grid_trajs=orig_grid,
        grid=grid,
        n=sniff_n,
    )

    if sensitive_zone is None:
        sensitive_zone = get_nth_densest_cell(
            orig_grid_trajs=orig_grid,
            grid=grid,
            n=sensitive_n,
        )

    sniffed_original_indices: List[int] = []
    sniffed_original_trajs: List[Trajectory] = []

    for i, grid_traj in enumerate(orig_grid):
        if sniff_region in grid_traj:
            sniffed_original_indices.append(i)
            sniffed_original_trajs.append(orig_xy[i])

    failing_events: List[Dict[str, Any]] = []
    matched_events: List[Dict[str, Any]] = []
    no_match_count = 0

    for orig_index, sniffed_traj in tqdm(zip(sniffed_original_indices, sniffed_original_trajs), total=len(sniffed_original_trajs), desc="Partial sniffing",):
        sniffed_actual_pts = get_sniffed_points(sniffed_traj, sniff_region)

        min_dist_so_far = inf
        min_index = -1

        for syn_index, syn_traj in enumerate(syn_xy):
            syn_sniffed = get_sniffed_points(syn_traj, sniff_region)

            if len(syn_sniffed) < 1:
                continue

            dist = calculate_dtw(sniffed_actual_pts, syn_sniffed)

            if dist < min_dist_so_far:
                min_dist_so_far = dist
                min_index = syn_index

        if min_index < 0:
            no_match_count += 1
            continue

        most_similar_synthetic = syn_xy[min_index]
        most_similar_grid = syn_grid[min_index]

        intersect = calc_intersection_count(
            traj1=most_similar_synthetic,
            traj2=sniffed_traj,
            tolerance=0.001,
        )

        matched_events.append(
            {
                "original_index": orig_index,
                "synthetic_index": min_index,
                "dtw_distance": min_dist_so_far,
                "intersection_count": intersect,
            }
        )

        if intersect >= intersection_threshold:
            failing_events.append(
                {
                    "original_index": orig_index,
                    "synthetic_index": min_index,
                    "reason": "intersection",
                    "dtw_distance": min_dist_so_far,
                    "intersection_count": intersect,
                }
            )

        if sensitive_zone in most_similar_grid:
            failing_events.append(
                {
                    "original_index": orig_index,
                    "synthetic_index": min_index,
                    "reason": "sensitive_zone",
                    "dtw_distance": min_dist_so_far,
                    "intersection_count": intersect,
                }
            )

    failing_synthetic_indices_unique = sorted(
        {event["synthetic_index"] for event in failing_events}
    )

    failures_by_intersection = sum(
        1 for event in failing_events
        if event["reason"] == "intersection"
    )

    failures_by_sensitive_zone = sum(
        1 for event in failing_events
        if event["reason"] == "sensitive_zone"
    )

    return {
        "sniff_region": sniff_region.name,
        "sensitive_zone": sensitive_zone.name,
        "sniffed_original_count": len(sniffed_original_trajs),
        "matched_count": len(matched_events),
        "no_match_count": no_match_count,
        "failing_event_count": len(failing_events),
        "failing_synthetic_count_unique": len(failing_synthetic_indices_unique),
        "failures_by_intersection": failures_by_intersection,
        "failures_by_sensitive_zone": failures_by_sensitive_zone,
        "failing_synthetic_indices_unique": failing_synthetic_indices_unique,
        "failing_events": failing_events,
        "matched_events": matched_events,
    }
