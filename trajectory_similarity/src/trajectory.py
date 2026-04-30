

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Point:
    x: float
    y: float
    osm_id: Optional[int] = None
    timestamp: Optional[str] = None


@dataclass
class Segment:
    segment_id: int
    start_node: int
    end_node: int
    length: float


@dataclass
class Trajectory:
    traj_id: int
    points: List[Point] = field(default_factory=list)
    segment_ids: List[int] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.points) == 0 and len(self.segment_ids) == 0

    def __str__(self) -> str:
        if self.segment_ids:
            return f"Trajectory({self.traj_id}): " + " -> ".join(map(str, self.segment_ids))
        return f"Trajectory({self.traj_id}) with {len(self.points)} points"