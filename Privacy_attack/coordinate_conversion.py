from __future__ import annotations

from math import cos, radians
from typing import Iterable, List, Optional, Tuple


Point = Tuple[float, float]


EARTH_RADIUS_METERS = 6_371_000.0


def latlon_to_xy_meters(
    lon: float,
    lat: float,
    origin_lon: float,
    origin_lat: float,
) -> Point:
    """
    Converts lon/lat degrees to local x/y meters.

    Uses an equirectangular local projection:

        x = R * lon_delta * cos(origin_lat)
        y = R * lat_delta

    Input:
        lon, lat in degrees

    Output:
        x, y in meters
    """
    x = EARTH_RADIUS_METERS * radians(lon - origin_lon) * cos(radians(origin_lat))
    y = EARTH_RADIUS_METERS * radians(lat - origin_lat)

    return x, y


def get_latlon_origin(
    trajectories: List[List[Point]],
    coordinate_order: str = "lonlat",
) -> Point:
    """
    Finds a stable origin for local projection.

    Returns:
        origin_lon, origin_lat

    coordinate_order:
        "lonlat" means each point is (lon, lat)
        "latlon" means each point is (lat, lon)
    """
    if coordinate_order not in {"lonlat", "latlon"}:
        raise ValueError("coordinate_order must be 'lonlat' or 'latlon'")

    lons = []
    lats = []

    for traj in trajectories:
        for a, b in traj:
            if coordinate_order == "lonlat":
                lon, lat = a, b
            else:
                lat, lon = a, b

            lons.append(lon)
            lats.append(lat)

    if not lons:
        raise ValueError("No coordinates found")

    origin_lon = sum(lons) / len(lons)
    origin_lat = sum(lats) / len(lats)

    return origin_lon, origin_lat


def convert_trajectories_latlon_to_xy_meters(
    trajectories: List[List[Point]],
    coordinate_order: str = "lonlat",
    origin_lon: Optional[float] = None,
    origin_lat: Optional[float] = None,
) -> Tuple[List[List[Point]], Tuple[float, float]]:
    """
    Converts all trajectories from lat/lon degrees to local x/y meters.

    Returns:
        converted_trajectories, (origin_lon, origin_lat)
    """
    if coordinate_order not in {"lonlat", "latlon"}:
        raise ValueError("coordinate_order must be 'lonlat' or 'latlon'")

    if origin_lon is None or origin_lat is None:
        origin_lon, origin_lat = get_latlon_origin(
            trajectories,
            coordinate_order=coordinate_order,
        )

    converted = []

    for traj in trajectories:
        converted_traj = []

        for a, b in traj:
            if coordinate_order == "lonlat":
                lon, lat = a, b
            else:
                lat, lon = a, b

            x, y = latlon_to_xy_meters(
                lon=lon,
                lat=lat,
                origin_lon=origin_lon,
                origin_lat=origin_lat,
            )

            converted_traj.append((x, y))

        converted.append(converted_traj)

    return converted, (origin_lon, origin_lat)