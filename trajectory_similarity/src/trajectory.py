from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Point:
    lon: float
    lat: float
    timestamp: Optional[str] = None
    node_id: Optional[int] = None


@dataclass
class Trajectory:
    traj_id: int
    dataset: str
    points: List[Point] = field(default_factory=list)
    segment_ids: List[int] = field(default_factory=list)

    def point_count(self) -> int:
        return len(self.points)

    def segment_count(self) -> int:
        return len(self.segment_ids)

    def length(self, roadmap=None) -> float:
        """
        Returns trip length in meters.

        If a roadmap and segment IDs are available, road-network segment length
        is used. Otherwise, haversine distance over points is used.
        """
        if roadmap is not None and self.segment_ids:
            return sum(roadmap.segment_lengths.get(seg_id, 0.0) for seg_id in self.segment_ids)

        from utils.distance import haversine_m

        if len(self.points) < 2:
            return 0.0

        return sum(
            haversine_m(p1.lon, p1.lat, p2.lon, p2.lat)
            for p1, p2 in zip(self.points[:-1], self.points[1:])
        )

    def is_empty(self) -> bool:
        return len(self.points) == 0 and len(self.segment_ids) == 0