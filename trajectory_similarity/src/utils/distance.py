import math
from trajectory import Point


EARTH_RADIUS_M = 6371000.0


def haversine_m(lon1, lat1, lon2, lat2) -> float:
    lon1_rad = math.radians(lon1)
    lat1_rad = math.radians(lat1)
    lon2_rad = math.radians(lon2)
    lat2_rad = math.radians(lat2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def point_distance(p1: Point, p2: Point, roadmap=None) -> float:
    """
    Returns road-network shortest-path distance if both points have node IDs
    and a roadmap is available. Otherwise falls back to haversine distance.
    """
    if roadmap is not None and p1.node_id is not None and p2.node_id is not None:
        return roadmap.shortest_path_distance(p1.node_id, p2.node_id)

    return haversine_m(p1.lon, p1.lat, p2.lon, p2.lat)