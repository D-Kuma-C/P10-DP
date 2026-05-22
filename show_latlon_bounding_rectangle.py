import folium


# ============================================================
# CONFIG
# ============================================================

# Input .dat file with lon,lat or lon,lat,time points
INPUT_FILE = r"C:\Users\test\Desktop\Uni\P10-DP\trajectory_similarity\data\original\porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630.dat"

# Output HTML map
OUTPUT_HTML = r"C:\Users\test\Desktop\Uni\P10-DP\boundingRectangle\latlon_second_bounding_rectangle_with_trajectories.html"

BOUNDING_RECTANGLE_RANK = 2

# ============================================================
# PARSE DAT FILE
# ============================================================

def read_trajectories_from_dat(file_path):
    trajectories = []
    current_traj_id = None

    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                current_traj_id = line.replace("#", "").replace(":", "").strip()
                continue

            if line.startswith(">"):
                if current_traj_id is None:
                    continue

                point_text = line.split(":", 1)[1]
                raw_points = point_text.split(";")

                points = []

                for p in raw_points:
                    p = p.strip()
                    if not p:
                        continue

                    parts = p.split(",")

                    if len(parts) < 2:
                        continue

                    lon = float(parts[0])
                    lat = float(parts[1])

                    points.append((lat, lon))

                if points:
                    trajectories.append({
                        "traj_id": current_traj_id,
                        "points": points,
                    })

    return trajectories


# ============================================================
# BOUNDING RECTANGLE LOGIC
# ============================================================

def compute_bounds(trajectories):
    all_points = []

    for traj in trajectories:
        for lat, lon in traj["points"]:
            all_points.append({
                "traj_id": traj["traj_id"],
                "lat": lat,
                "lon": lon,
            })

    if not all_points:
        raise ValueError("No longitude/latitude points found.")

    min_lon = min(p["lon"] for p in all_points)
    max_lon = max(p["lon"] for p in all_points)
    min_lat = min(p["lat"] for p in all_points)
    max_lat = max(p["lat"] for p in all_points)

    bounds = {
        "min_lon": min_lon,
        "max_lon": max_lon,
        "min_lat": min_lat,
        "max_lat": max_lat,
    }

    boundary_point_records = []

    for p in all_points:
        if (
            p["lon"] == min_lon
            or p["lon"] == max_lon
            or p["lat"] == min_lat
            or p["lat"] == max_lat
        ):
            boundary_point_records.append(p)

    boundary_traj_ids = sorted(
        set(p["traj_id"] for p in boundary_point_records),
        key=lambda x: int(x) if str(x).isdigit() else str(x),
    )

    boundary_trajectories = [
        traj for traj in trajectories
        if traj["traj_id"] in boundary_traj_ids
    ]

    return bounds, boundary_trajectories, boundary_point_records


def get_ranked_bounding_rectangle(trajectories, rank):
    remaining = list(trajectories)
    history = []

    for current_rank in range(1, rank + 1):
        if not remaining:
            raise ValueError(
                f"Cannot compute bounding rectangle rank {current_rank}; no trajectories remain."
            )

        bounds, boundary_trajectories, boundary_point_records = compute_bounds(remaining)

        history.append({
            "rank": current_rank,
            "bounds": bounds,
            "boundary_trajectories": boundary_trajectories,
            "boundary_point_records": boundary_point_records,
            "remaining_count_before_removal": len(remaining),
        })

        boundary_ids = set(t["traj_id"] for t in boundary_trajectories)

        remaining = [
            traj for traj in remaining
            if traj["traj_id"] not in boundary_ids
        ]

    return history[-1], history


# ============================================================
# MAP
# ============================================================

def add_rectangle_to_map(m, bounds, color, label):
    min_lon = bounds["min_lon"]
    max_lon = bounds["max_lon"]
    min_lat = bounds["min_lat"]
    max_lat = bounds["max_lat"]

    folium.Rectangle(
        bounds=[
            [min_lat, min_lon],
            [max_lat, max_lon],
        ],
        color=color,
        weight=4,
        fill=True,
        fill_opacity=0.12,
        popup=(
            f"{label}<br>"
            f"min_lon={min_lon:.6f}<br>"
            f"max_lon={max_lon:.6f}<br>"
            f"min_lat={min_lat:.6f}<br>"
            f"max_lat={max_lat:.6f}"
        ),
        tooltip=label,
    ).add_to(m)


def main():
    trajectories = read_trajectories_from_dat(INPUT_FILE)

    if not trajectories:
        raise ValueError("No trajectories found in input file.")

    selected, history = get_ranked_bounding_rectangle(
        trajectories,
        rank=BOUNDING_RECTANGLE_RANK,
    )

    bounds = selected["bounds"]
    boundary_trajectories = selected["boundary_trajectories"]
    boundary_point_records = selected["boundary_point_records"]

    min_lon = bounds["min_lon"]
    max_lon = bounds["max_lon"]
    min_lat = bounds["min_lat"]
    max_lat = bounds["max_lat"]

    print(f"Selected bounding rectangle rank: {BOUNDING_RECTANGLE_RANK}")
    print("\nBounding rectangle:")
    print(f"min_lon = {min_lon}")
    print(f"max_lon = {max_lon}")
    print(f"min_lat = {min_lat}")
    print(f"max_lat = {max_lat}")

    print("\nTrajectories that create this bounding rectangle:")
    for traj in boundary_trajectories:
        print(f"Trajectory #{traj['traj_id']} with {len(traj['points'])} points")

    print("\nBoundary point sources:")
    for p in boundary_point_records:
        side_names = []

        if p["lon"] == min_lon:
            side_names.append("min_lon")
        if p["lon"] == max_lon:
            side_names.append("max_lon")
        if p["lat"] == min_lat:
            side_names.append("min_lat")
        if p["lat"] == max_lat:
            side_names.append("max_lat")

        print(
            f"Trajectory #{p['traj_id']} -> "
            f"lat={p['lat']}, lon={p['lon']} "
            f"({', '.join(side_names)})"
        )

    center_lat = (min_lat + max_lat) / 2.0
    center_lon = (min_lon + max_lon) / 2.0

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    # Optional: draw previous rectangles lightly for context.
    for item in history[:-1]:
        add_rectangle_to_map(
            m,
            item["bounds"],
            color="gray",
            label=f"Previous bounding rectangle rank {item['rank']}",
        )

    # Draw selected second/ranked rectangle.
    add_rectangle_to_map(
        m,
        bounds,
        color="red",
        label=f"Bounding rectangle rank {BOUNDING_RECTANGLE_RANK}",
    )

    # Draw only the trajectories that create the selected rectangle.
    for traj in boundary_trajectories:
        traj_id = traj["traj_id"]
        points = traj["points"]

        folium.PolyLine(
            locations=points,
            weight=4,
            opacity=0.85,
            tooltip=f"Trajectory #{traj_id}",
            popup=f"Trajectory #{traj_id}<br>{len(points)} points",
        ).add_to(m)

        first_lat, first_lon = points[0]
        folium.Marker(
            location=[first_lat, first_lon],
            popup=f"Trajectory #{traj_id}",
            tooltip=f"Trajectory #{traj_id}",
        ).add_to(m)

    # Mark exact boundary points.
    for p in boundary_point_records:
        side_names = []

        if p["lon"] == min_lon:
            side_names.append("min_lon")
        if p["lon"] == max_lon:
            side_names.append("max_lon")
        if p["lat"] == min_lat:
            side_names.append("min_lat")
        if p["lat"] == max_lat:
            side_names.append("max_lat")

        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=6,
            fill=True,
            fill_opacity=1.0,
            popup=(
                f"Trajectory #{p['traj_id']}<br>"
                f"lat={p['lat']}<br>"
                f"lon={p['lon']}<br>"
                f"{', '.join(side_names)}"
            ),
            tooltip=f"#{p['traj_id']} boundary point",
        ).add_to(m)

    m.fit_bounds([
        [min_lat, min_lon],
        [max_lat, max_lon],
    ])

    m.save(OUTPUT_HTML)
    print(f"\nSaved map to: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()