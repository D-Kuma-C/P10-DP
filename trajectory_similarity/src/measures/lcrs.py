from trajectory_similarity.src.trajectory import Trajectory
from measures.lors import LORS


class LCRS:
    @staticmethod
    def compute(t1: Trajectory, t2: Trajectory) -> float:
        overlap = -LORS.compute(t1, t2)

        len1 = len(t1.segment_ids)
        len2 = len(t2.segment_ids)

        denominator = len1 + len2 - overlap
        if denominator == 0:
            return 0.0

        return -(overlap / denominator)