import os
import pandas as pd
from tqdm import tqdm

from trajectory import Point
from roadmap import RoadMap


def downsample_sequence(sequence, max_len):
    if max_len is None or max_len <= 0:
        return sequence

    if len(sequence) <= max_len:
        return sequence

    if max_len == 1:
        return [sequence[0]]

    indices = [
        round(i * (len(sequence) - 1) / (max_len - 1))
        for i in range(max_len)
    ]

    return [sequence[i] for i in indices]


def build_network_with_osmnx(trajectories, place: str, output_dir: str):
    import osmnx as ox

    os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading OSMnx road network for: {place}")
    graph = ox.graph_from_place(place, network_type="drive")

    # Keep graph unprojected because input points are lon/lat.
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(graph)

    edge_key_to_segment_id = {
        edge_key: segment_id
        for segment_id, edge_key in enumerate(edges_gdf.index)
    }

    roadmap = RoadMap.from_osmnx_graph(graph, edges_gdf)

    nodes_out = []
    for node_id, data in graph.nodes(data=True):
        nodes_out.append({
            "node_id": int(node_id),
            "lon": float(data["x"]),
            "lat": float(data["y"]),
        })

    edges_out = []
    for edge_key, segment_id in edge_key_to_segment_id.items():
        u, v, key = edge_key
        row = edges_gdf.loc[edge_key]
        edges_out.append({
            "edge_id": segment_id,
            "start_node": int(u),
            "end_node": int(v),
            "length": float(row.get("length", 0.0)),
            "osmnx_u": int(u),
            "osmnx_v": int(v),
            "osmnx_key": int(key),
        })

    pd.DataFrame(nodes_out).to_csv(f"{output_dir}/nodes.csv", index=False)
    pd.DataFrame(edges_out).to_csv(f"{output_dir}/edges.csv", index=False)

    segment_rows = []

    for traj in tqdm(trajectories, desc="Assigning OSMnx segments"):
        if not traj.points:
            traj.segment_ids = []
            continue

        lons = [p.lon for p in traj.points]
        lats = [p.lat for p in traj.points]

        matched_edges = ox.distance.nearest_edges(graph, X=lons, Y=lats)
        matched_nodes = ox.distance.nearest_nodes(graph, X=lons, Y=lats)

        new_points = []
        for p, node_id in zip(traj.points, matched_nodes):
            new_points.append(
                Point(
                    lon=p.lon,
                    lat=p.lat,
                    timestamp=p.timestamp,
                    node_id=int(node_id),
                )
            )
        traj.points = new_points

        segment_ids = []
        previous_seg = None
        order = 0

        for edge_key in matched_edges:
            seg_id = edge_key_to_segment_id[edge_key]

            # Remove repeated consecutive segment IDs.
            if seg_id != previous_seg:
                segment_ids.append(seg_id)
                segment_rows.append({
                    "dataset": traj.dataset,
                    "traj_id": traj.traj_id,
                    "order": order,
                    "segment_id": seg_id,
                })
                order += 1

            previous_seg = seg_id

        traj.segment_ids = segment_ids

    pd.DataFrame(segment_rows).to_csv(f"{output_dir}/trajectory_segments.csv", index=False)

    print(f"Saved network files to: {output_dir}")
    return roadmap, trajectories

def load_prebuilt_network(trajectories, nodes_file: str, edges_file: str, segments_file: str):
    roadmap = RoadMap.from_files(nodes_file, edges_file)
    segments = pd.read_csv(segments_file)

    indexed_segments = {}
    indexed_node_sequences = {}

    for (dataset, traj_id), group in segments.groupby(["dataset", "traj_id"]):
        group = group.sort_values("order")

        segment_ids = group["segment_id"].astype(int).tolist()
        indexed_segments[(dataset, traj_id)] = segment_ids

        node_sequence = []

        if "start_node" in group.columns and "end_node" in group.columns:
            rows = list(group.itertuples(index=False))

            for idx, row in enumerate(rows):
                start_node = int(row.start_node)
                end_node = int(row.end_node)

                if idx == 0:
                    node_sequence.append(start_node)

                node_sequence.append(end_node)

        indexed_node_sequences[(dataset, traj_id)] = node_sequence

    for traj in tqdm(trajectories, desc="Loading prebuilt segment IDs and node IDs"):
        key = (traj.dataset, traj.traj_id)

        traj.segment_ids = indexed_segments.get(key, [])

        node_sequence = indexed_node_sequences.get(key, [])

        node_sequence = downsample_sequence(node_sequence, max_len=50)
        traj.segment_ids = downsample_sequence(traj.segment_ids, max_len=50)

        if node_sequence:
            new_points = []

            original_points = traj.points
            original_timestamps = [p.timestamp for p in original_points]

            for idx, node_id in enumerate(node_sequence):
                lon, lat = roadmap.node_positions.get(node_id, (None, None))

                if lon is None or lat is None:
                    continue

                timestamp = None
                if original_timestamps:
                    timestamp = original_timestamps[min(idx, len(original_timestamps) - 1)]

                new_points.append(
                    Point(
                        lon=float(lon),
                        lat=float(lat),
                        timestamp=timestamp,
                        node_id=int(node_id),
                    )
                )

            if new_points:
                traj.points = new_points

    return roadmap, trajectories