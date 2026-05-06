import math
from utils.distance import point_distance


class TP:
    def compute(self, t1, t2, roadmap=None):
        ps1 = t1.points
        ps2 = t2.points

        if len(ps1) == 0 or len(ps2) == 0:
            return 0.0

        total_exp_1 = 0.0
        for p in ps1:
            min_dist = min(point_distance(p, q, roadmap) for q in ps2)
            total_exp_1 += math.exp(-min_dist / 1000.0)

        total_exp_2 = 0.0
        for p in ps2:
            min_dist = min(point_distance(p, q, roadmap) for q in ps1)
            total_exp_2 += math.exp(-min_dist / 1000.0)

        spatial_score = total_exp_1 / len(ps1) + total_exp_2 / len(ps2)

        total_time_exp_1 = 0.0
        for i in range(len(ps1)):
            min_time_dist = min(abs(i - j) for j in range(len(ps2)))
            total_time_exp_1 += math.exp(-min_time_dist)

        total_time_exp_2 = 0.0
        for i in range(len(ps2)):
            min_time_dist = min(abs(i - j) for j in range(len(ps1)))
            total_time_exp_2 += math.exp(-min_time_dist)

        temporal_score = total_time_exp_1 / len(ps1) + total_time_exp_2 / len(ps2)

        return -(0.99 * spatial_score + 0.01 * temporal_score)