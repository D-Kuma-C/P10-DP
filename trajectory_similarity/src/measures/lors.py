class LORS:
    def compute(self, t1, t2, roadmap=None):
        s1 = t1.segment_ids
        s2 = t2.segment_ids

        m, n = len(s1), len(s2)
        if m == 0 or n == 0:
            return 0.0

        dp = [[0.0] * n for _ in range(m)]

        first_len = roadmap.segment_lengths.get(s1[0], 1.0) if roadmap else 1.0
        dp[0][0] = first_len if s1[0] == s2[0] else 0.0

        for i in range(1, m):
            seg_len = roadmap.segment_lengths.get(s1[i], 1.0) if roadmap else 1.0
            if s1[i] == s2[0]:
                dp[i][0] = max(dp[i - 1][0], seg_len)
            else:
                dp[i][0] = dp[i - 1][0]

        for j in range(1, n):
            seg_len = roadmap.segment_lengths.get(s2[j], 1.0) if roadmap else 1.0
            if s2[j] == s1[0]:
                dp[0][j] = max(dp[0][j - 1], seg_len)
            else:
                dp[0][j] = dp[0][j - 1]

        for i in range(1, m):
            for j in range(1, n):
                if s1[i] == s2[j]:
                    seg_len = roadmap.segment_lengths.get(s1[i], 1.0) if roadmap else 1.0
                    dp[i][j] = dp[i - 1][j - 1] + seg_len
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return -float(dp[m - 1][n - 1])