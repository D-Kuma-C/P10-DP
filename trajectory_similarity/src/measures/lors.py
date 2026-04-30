
from trajectory_similarity.src.trajectory import Trajectory


class LORS:
    @staticmethod
    def compute(t1: Trajectory, t2: Trajectory) -> float:
        s1 = t1.segment_ids
        s2 = t2.segment_ids

        m, n = len(s1), len(s2)
        if m == 0 or n == 0:
            return 0.0

        dp = [[0.0] * n for _ in range(m)]

        dp[0][0] = 1.0 if s1[0] == s2[0] else 0.0

        for i in range(1, m):
            dp[i][0] = max(dp[i - 1][0], 1.0 if s1[i] == s2[0] else 0.0)

        for j in range(1, n):
            dp[0][j] = max(dp[0][j - 1], 1.0 if s2[j] == s1[0] else 0.0)

        for i in range(1, m):
            for j in range(1, n):
                if s1[i] == s2[j]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return -dp[m - 1][n - 1]