from __future__ import annotations

from math import inf
from typing import List

from geometry import Point, Trajectory, euclidean_dist


def calculate_dtw(list1: List[Point], list2: List[Point]) -> float:
    """
    Equivalent to AdaTrace Evaluation.calculateDTW.
    """
    m = len(list1)
    n = len(list2)

    dtw_matrix = [[0.0 for _ in range(n + 1)] for _ in range(m + 1)]

    for i in range(1, m + 1):
        dtw_matrix[i][0] = inf

    for j in range(1, n + 1):
        dtw_matrix[0][j] = inf

    dtw_matrix[0][0] = 0.0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            p1 = list1[i - 1]
            p2 = list2[j - 1]
            euclid_dist = euclidean_dist(p1, p2)

            min_prev = min(
                dtw_matrix[i - 1][j],
                dtw_matrix[i][j - 1],
                dtw_matrix[i - 1][j - 1],
            )

            dtw_matrix[i][j] = euclid_dist + min_prev

    return dtw_matrix[m][n]


def calc_intersection_count(
    traj1: Trajectory,
    traj2: Trajectory,
    tolerance: float = 0.001,
) -> int:
    """
    Equivalent to traj1.calcIntersectionCount(traj2).

    Java logic:
      for every point p in traj2:
          if any point in traj1 is within 0.001:
              count p once
    """
    count = 0

    for p in traj2:
        for candidate in traj1:
            if euclidean_dist(p, candidate) < tolerance:
                count += 1
                break

    return count
