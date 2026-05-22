import numpy as np
from trajectory_similarity.src.utils.distance import point_distance


class NetERP:
    def __init__(self, gap_cost: float = 1.0):
        self.gap_cost = gap_cost

    def compute(self, t1, t2, roadmap=None):
        ps1 = t1.points
        ps2 = t2.points
        m, n = len(ps1), len(ps2)

        if m == 0 and n == 0:
            return 0.0
        if m == 0:
            return n * self.gap_cost
        if n == 0:
            return m * self.gap_cost

        dp = np.zeros((m + 1, n + 1), dtype=float)

        for i in range(1, m + 1):
            dp[i, 0] = dp[i - 1, 0] + self.gap_cost

        for j in range(1, n + 1):
            dp[0, j] = dp[0, j - 1] + self.gap_cost

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                match_cost = dp[i - 1, j - 1] + point_distance(ps1[i - 1], ps2[j - 1], roadmap)
                delete_cost = dp[i - 1, j] + self.gap_cost
                insert_cost = dp[i, j - 1] + self.gap_cost
                dp[i, j] = min(match_cost, delete_cost, insert_cost)

        return float(dp[m, n])