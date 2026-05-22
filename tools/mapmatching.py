# import datetime
# import math
# import csv
# import json
# import requests
#
# # MAP MATCHING Params
#
# OSRM_URL = "http://localhost:5000/route/v1/driving"
# MAX_MATCH_POINTS = 100  # OSRM limit
#
# START_ID = 0
# END_ID = 500
#
# INPUT_FILE = r"C:\Users\test\Desktop\Uni\P10-DP\input\dpstar_synthetic\eps_0.1\dpstar_eps_0.1.dat"
# OUTPUT_FILE = r"C:\Users\test\Desktop\Uni\P10-DP\output\test.dat"
# SEGMENTS_FILE = r"/input/segments\test_segments.csv"
#
# edge_lookup = {}
# edge_registry = {}
# next_edge_id = 0
#
#
# def write_trajectory(trajectory, traj_id):
#     trajectory_string = ";".join(trajectory) + ";"
#
#     with open(OUTPUT_FILE, "a") as out:
#         out.write(f"#{traj_id}\n")
#         out.write(f">0:{trajectory_string}\n")
#
#
# def haversine(p1, p2):
#     import math
#     R = 6371000
#     lon1, lat1 = map(math.radians, p1)
#     lon2, lat2 = map(math.radians, p2)
#
#     dlon = lon2 - lon1
#     dlat = lat2 - lat1
#
#     a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
#     return 2 * R * math.asin(math.sqrt(a))
#
#
# def is_valid_trip(traj):
#     if len(traj) < 2:
#         return False
#
#     total = sum(
#         haversine(traj[i], traj[i + 1])
#         for i in range(len(traj) - 1)
#     )
#
#     return total < 10000
#
#
# # Map match raw data
# def route_osrm(points):
#     if len(points) < 2:
#         return None
#
#     coords = ";".join([f"{lon},{lat}" for lon, lat in points])
#
#     try:
#         response = requests.get(
#             f"{OSRM_URL}/{coords}",
#             params={
#                 "overview": "full",
#                 "geometries": "geojson",
#                 "steps": "false",
#                 "annotations": "nodes"
#             },
#             timeout=5
#         )
#         data = response.json()
#
#     except Exception as e:
#         print("OSRM error:", e)
#         return None
#
#     if "routes" not in data or not data["routes"]:
#         return None
#
#     # geometry = data["routes"][0]["geometry"]["coordinates"]
#     return data["routes"][0]
#
#
# def parse_input(input_file):
#     trajectories = []
#     current = []
#
#     with open(input_file) as f:
#         for line in f:
#             line = line.strip()
#
#             if line.startswith("#"):
#                 if current:
#                     trajectories.append(current)
#                     current = []
#
#             elif line.startswith(">0:"):
#                 coords = line[3:].split(";")
#                 for c in coords:
#                     if not c:
#                         continue
#                     lon, lat = map(float, c.split(","))
#                     current.append((lon, lat))
#
#     if current:
#         trajectories.append(current)
#
#     return trajectories
#
#
# def extract_segments(route):
#     global next_edge_id
#
#     trajectory_segment_ids = []
#
#     if "legs" not in route:
#         return trajectory_segment_ids
#
#     for leg in route["legs"]:
#
#         if "annotation" not in leg:
#             continue
#
#         annotation = leg["annotation"]
#
#         if "nodes" not in annotation:
#             continue
#
#         nodes = annotation["nodes"]
#
#         for i in range(len(nodes) - 1):
#
#             start_node = nodes[i]
#             end_node = nodes[i + 1]
#
#             edge_key = (start_node, end_node)
#
#             # reuse existing segment
#             if edge_key in edge_lookup:
#                 edge_id = edge_lookup[edge_key]
#
#             else:
#                 edge_id = next_edge_id
#                 next_edge_id += 1
#
#                 edge_lookup[edge_key] = edge_id
#
#                 edge_registry[edge_id] = {
#                     "start_node": start_node,
#                     "end_node": end_node
#                 }
#
#             trajectory_segment_ids.append(edge_id)
#
#     return trajectory_segment_ids
#
#
# def process_trajectories(input_file, output_file, segment_file):
#     trajectories = parse_input(input_file)
#
#     traj_id = 0
#
#     with open(output_file, "w") as out, \
#             open(segment_file, "w") as seg_out:
#
#         seg_out.write("traj_id,order,segment_id\n")
#
#         for traj in trajectories:
#
#             if traj_id < START_ID:
#                 continue
#
#             if END_ID and traj_id > END_ID:
#                 break
#
#             # if haversine(traj[0], traj[-1]) > 3000:
#             #     continue
#
#             print("Mapmatching trajectory:", traj_id)
#
#             route = route_osrm(traj)
#
#             if not route:
#                 continue
#
#             matched = route["geometry"]["coordinates"]
#
#             segment_ids = extract_segments(route)
#
#             # trajectory output
#             parts = [f"{lon},{lat}" for lon, lat in matched]
#
#             out.write(f"#{traj_id}\n")
#             out.write(">0:" + ";".join(parts) + ";\n")
#
#             # segment output
#             for order, seg_id in enumerate(segment_ids):
#                 seg_out.write(f"{traj_id},{order},{seg_id}\n")
#
#             traj_id += 1
#
#
# process_trajectories(
#     INPUT_FILE,
#     OUTPUT_FILE,
#     SEGMENTS_FILE
# )

from pathlib import Path
import argparse
import csv
import json
import math
import shutil
import tempfile

import requests


def parse_args():
    parser = argparse.ArgumentParser(
        description="Map-match .dat trajectories using OSRM and create prebuilt network files."
    )

    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--segments-file", required=True)

    parser.add_argument("--nodes-file", required=True)
    parser.add_argument("--edges-file", required=True)
    parser.add_argument("--edge-registry-file", required=True)

    parser.add_argument(
        "--dataset-label",
        required=True,
        choices=["original", "synthetic"],
        help="Label written in trajectory_segments.csv.",
    )

    parser.add_argument(
        "--osrm-url",
        default="http://localhost:5000/route/v1/driving",
    )

    parser.add_argument("--max-match-points", type=int, default=100)
    parser.add_argument("--start-id", type=int, default=0)
    parser.add_argument("--end-id", type=int, default=None)

    parser.add_argument(
        "--overwrite-input",
        action="store_true",
        help="Overwrite input .dat with map-matched output.",
    )

    return parser.parse_args()


def haversine_m(p1, p2):
    radius_m = 6371000.0

    lon1, lat1 = map(math.radians, p1)
    lon2, lat2 = map(math.radians, p2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    return 2 * radius_m * math.asin(math.sqrt(a))


def coord_key(lon, lat, precision=7):
    return f"{round(float(lon), precision)},{round(float(lat), precision)}"


def edge_key_from_coords(p1, p2):
    """
    Stable directed edge key based on OSRM route geometry coordinates.
    """
    return f"{coord_key(p1[0], p1[1])}|{coord_key(p2[0], p2[1])}"


def parse_point(raw_point):
    """
    Supports:
        lon,lat
        lon,lat,timestamp

    Timestamp is ignored for map-matching output because OSRM route geometry
    creates new matched points.
    """
    parts = [p.strip() for p in raw_point.split(",")]

    if len(parts) < 2:
        return None

    lon = float(parts[0])
    lat = float(parts[1])

    return lon, lat


def parse_input(input_file):
    trajectories = []
    current_id = None
    current_points = []

    with open(input_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                if current_id is not None:
                    trajectories.append((current_id, current_points))

                id_text = line.replace("#", "").replace(":", "").strip()
                current_id = int(id_text)
                current_points = []

            elif line.startswith(">"):
                point_text = line.split(":", 1)[1] if ":" in line else line

                for raw_point in point_text.split(";"):
                    raw_point = raw_point.strip()

                    if not raw_point:
                        continue

                    point = parse_point(raw_point)

                    if point is not None:
                        current_points.append(point)

    if current_id is not None:
        trajectories.append((current_id, current_points))

    return trajectories


def route_osrm(points, osrm_url, timeout=20):
    if len(points) < 2:
        return None

    coords = ";".join(f"{lon},{lat}" for lon, lat in points)

    try:
        response = requests.get(
            f"{osrm_url}/{coords}",
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "false",
                "annotations": "false",
            },
            timeout=timeout,
        )
        data = response.json()

    except Exception as e:
        print("OSRM error:", e)
        return None

    if "routes" not in data or not data["routes"]:
        return None

    return data["routes"][0]


def chunk_points(points, max_points):
    if len(points) <= max_points:
        yield points
        return

    start = 0

    while start < len(points):
        end = min(start + max_points, len(points))
        chunk = points[start:end]

        if len(chunk) >= 2:
            yield chunk

        if end == len(points):
            break

        start = end - 1


def load_registry(registry_file):
    registry_file = Path(registry_file)

    if not registry_file.exists():
        return {
            "next_node_id": 0,
            "next_edge_id": 0,
            "node_lookup": {},
            "edge_lookup": {},
            "nodes": {},
            "edges": {},
        }

    with registry_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry, registry_file):
    registry_file = Path(registry_file)
    registry_file.parent.mkdir(parents=True, exist_ok=True)

    with registry_file.open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def get_or_create_node(registry, lon, lat):
    key = coord_key(lon, lat)

    if key in registry["node_lookup"]:
        return int(registry["node_lookup"][key])

    node_id = int(registry["next_node_id"])
    registry["next_node_id"] = node_id + 1

    registry["node_lookup"][key] = node_id
    registry["nodes"][str(node_id)] = {
        "node_id": node_id,
        "lon": float(lon),
        "lat": float(lat),
    }

    return node_id


def get_or_create_edge(registry, p1, p2):
    edge_key = edge_key_from_coords(p1, p2)

    if edge_key in registry["edge_lookup"]:
        return int(registry["edge_lookup"][edge_key])

    start_node = get_or_create_node(registry, p1[0], p1[1])
    end_node = get_or_create_node(registry, p2[0], p2[1])

    edge_id = int(registry["next_edge_id"])
    registry["next_edge_id"] = edge_id + 1

    length = haversine_m(p1, p2)

    registry["edge_lookup"][edge_key] = edge_id
    registry["edges"][str(edge_id)] = {
        "edge_id": edge_id,
        "start_node": start_node,
        "end_node": end_node,
        "length": float(length),
    }

    return edge_id

def get_edge_nodes(registry, segment_id):
    edge = registry["edges"][str(segment_id)]

    return int(edge["start_node"]), int(edge["end_node"])


def geometry_to_segments(registry, coordinates):
    segment_ids = []

    if len(coordinates) < 2:
        return segment_ids

    previous_segment_id = None

    for p1, p2 in zip(coordinates[:-1], coordinates[1:]):
        if p1 == p2:
            continue

        segment_id = get_or_create_edge(registry, p1, p2)

        # Remove consecutive duplicate segment IDs.
        if segment_id != previous_segment_id:
            segment_ids.append(segment_id)

        previous_segment_id = segment_id

    return segment_ids


def write_nodes_edges(registry, nodes_file, edges_file):
    nodes_file = Path(nodes_file)
    edges_file = Path(edges_file)

    nodes_file.parent.mkdir(parents=True, exist_ok=True)
    edges_file.parent.mkdir(parents=True, exist_ok=True)

    nodes = sorted(
        registry["nodes"].values(),
        key=lambda row: int(row["node_id"]),
    )

    edges = sorted(
        registry["edges"].values(),
        key=lambda row: int(row["edge_id"]),
    )

    with nodes_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["node_id", "lon", "lat"])
        writer.writeheader()
        writer.writerows(nodes)

    with edges_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["edge_id", "start_node", "end_node", "length"],
        )
        writer.writeheader()
        writer.writerows(edges)


def process_trajectories(
    input_file,
    output_file,
    segments_file,
    nodes_file,
    edges_file,
    edge_registry_file,
    dataset_label,
    osrm_url,
    max_match_points,
    start_id,
    end_id,
):
    input_file = Path(input_file)
    output_file = Path(output_file)
    segments_file = Path(segments_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    segments_file.parent.mkdir(parents=True, exist_ok=True)

    registry = load_registry(edge_registry_file)
    trajectories = parse_input(input_file)

    written_trajectories = 0
    skipped_trajectories = 0

    with output_file.open("w", encoding="utf-8", newline="") as out, \
            segments_file.open("w", encoding="utf-8", newline="") as seg_out:

        segment_writer = csv.writer(seg_out)
        segment_writer.writerow([
            "dataset",
            "traj_id",
            "order",
            "segment_id",
            "start_node",
            "end_node",
        ])

        for traj_id, traj_points in trajectories:
            if traj_id < start_id:
                continue

            if end_id is not None and traj_id > end_id:
                continue

            if len(traj_points) < 2:
                skipped_trajectories += 1
                continue

            print(f"Map-matching {dataset_label} trajectory: {traj_id}")

            matched_points = []
            segment_ids = []

            for point_chunk in chunk_points(traj_points, max_match_points):
                route = route_osrm(point_chunk, osrm_url=osrm_url)

                if not route:
                    continue

                coordinates = route["geometry"]["coordinates"]

                if matched_points and coordinates:
                    coordinates = coordinates[1:]

                matched_points.extend(coordinates)
                segment_ids.extend(geometry_to_segments(registry, coordinates))

            if len(matched_points) < 2:
                skipped_trajectories += 1
                continue

            point_text = ";".join(f"{lon},{lat}" for lon, lat in matched_points)

            out.write(f"#{traj_id}\n")
            out.write(f">0:{point_text};\n")

            for order, segment_id in enumerate(segment_ids):
                start_node, end_node = get_edge_nodes(registry, segment_id)

                segment_writer.writerow([
                    dataset_label,
                    traj_id,
                    order,
                    segment_id,
                    start_node,
                    end_node,
                ])

            written_trajectories += 1

    save_registry(registry, edge_registry_file)
    write_nodes_edges(registry, nodes_file, edges_file)

    print("Map-matching complete.")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Segments: {segments_file}")
    print(f"Nodes: {nodes_file}")
    print(f"Edges: {edges_file}")
    print(f"Registry: {edge_registry_file}")
    print(f"Written trajectories: {written_trajectories}")
    print(f"Skipped trajectories: {skipped_trajectories}")


def main():
    args = parse_args()

    input_file = Path(args.input_file)
    output_file = Path(args.output_file)

    if args.overwrite_input:
        temp_dir = Path(tempfile.mkdtemp(prefix="mapmatch_"))
        temp_output = temp_dir / input_file.name

        process_trajectories(
            input_file=input_file,
            output_file=temp_output,
            segments_file=args.segments_file,
            nodes_file=args.nodes_file,
            edges_file=args.edges_file,
            edge_registry_file=args.edge_registry_file,
            dataset_label=args.dataset_label,
            osrm_url=args.osrm_url,
            max_match_points=args.max_match_points,
            start_id=args.start_id,
            end_id=args.end_id,
        )

        shutil.copyfile(temp_output, input_file)

        if output_file.resolve() != input_file.resolve():
            output_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(input_file, output_file)

        shutil.rmtree(temp_dir)

        print(f"Overwrote input file with map-matched output: {input_file}")

    else:
        process_trajectories(
            input_file=input_file,
            output_file=output_file,
            segments_file=args.segments_file,
            nodes_file=args.nodes_file,
            edges_file=args.edges_file,
            edge_registry_file=args.edge_registry_file,
            dataset_label=args.dataset_label,
            osrm_url=args.osrm_url,
            max_match_points=args.max_match_points,
            start_id=args.start_id,
            end_id=args.end_id,
        )


if __name__ == "__main__":
    main()
