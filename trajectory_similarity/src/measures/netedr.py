import numpy as np
from trajectory_similarity.src.utils.distance import point_distance


class NetEDR:
    def __init__(self, match_threshold: float = 1000.0):
        self.match_threshold = match_threshold

    def compute(self, t1, t2, roadmap=None):
        ps1 = t1.points
        ps2 = t2.points
        m, n = len(ps1), len(ps2)

        if m == 0:
            return float(n)
        if n == 0:
            return float(m)

        dp = np.zeros((m + 1, n + 1), dtype=float)

        for i in range(m + 1):
            dp[i, 0] = i
        for j in range(n + 1):
            dp[0, j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                d = point_distance(ps1[i - 1], ps2[j - 1], roadmap)
                sub_cost = 0.0 if d <= self.match_threshold else 1.0
                dp[i, j] = min(
                    dp[i - 1, j] + 1.0,
                    dp[i, j - 1] + 1.0,
                    dp[i - 1, j - 1] + sub_cost,
                )

        return float(dp[m, n])