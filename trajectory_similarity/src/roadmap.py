import pandas as pd
import networkx as nx
from tqdm import tqdm


class RoadMap:
    def __init__(self):
        self.graph = nx.Graph()
        self.segment_lengths = {}
        self.segment_to_nodes = {}
        self.node_positions = {}
        self._distance_cache = {}
        self._source_distance_cache = {}

    @classmethod
    def from_files(cls, nodes_file: str, edges_file: str):
        roadmap = cls()

        nodes = pd.read_csv(nodes_file)
        edges = pd.read_csv(edges_file)

        for _, row in nodes.iterrows():
            node_id = int(row["node_id"])
            roadmap.node_positions[node_id] = (float(row["lon"]), float(row["lat"]))
            roadmap.graph.add_node(node_id)

        for _, row in edges.iterrows():
            edge_id = int(row["edge_id"])
            u = int(row["start_node"])
            v = int(row["end_node"])
            length = float(row["length"])

            roadmap.graph.add_edge(u, v, weight=length, segment_id=edge_id)
            roadmap.segment_lengths[edge_id] = length
            roadmap.segment_to_nodes[edge_id] = (u, v)

        return roadmap

    @classmethod
    def from_osmnx_graph(cls, graph, edges_gdf):
        roadmap = cls()

        for node_id, data in graph.nodes(data=True):
            roadmap.node_positions[int(node_id)] = (float(data.get("x")), float(data.get("y")))
            roadmap.graph.add_node(int(node_id))

        for segment_id, (edge_key, row) in enumerate(edges_gdf.iterrows()):
            u, v, key = edge_key
            length = float(row.get("length", 0.0))

            roadmap.graph.add_edge(int(u), int(v), weight=length, segment_id=segment_id)
            roadmap.segment_lengths[segment_id] = length
            roadmap.segment_to_nodes[segment_id] = (int(u), int(v))

        return roadmap

    def shortest_path_distance(self, node_a: int, node_b: int) -> float:
        if node_a == node_b:
            return 0.0

        node_a = int(node_a)
        node_b = int(node_b)

        if node_a not in self._source_distance_cache:
            try:
                self._source_distance_cache[node_a] = nx.single_source_dijkstra_path_length(
                    self.graph,
                    node_a,
                    weight="weight",
                )
            except nx.NodeNotFound:
                self._source_distance_cache[node_a] = {}

        return float(self._source_distance_cache[node_a].get(node_b, float("inf")))

    def precompute_distances_for_trajectories(self, trajectories):
        node_ids = set()

        for traj in trajectories:
            for point in traj.points:
                if point.node_id is not None:
                    node_ids.add(int(point.node_id))

        node_ids = sorted(node_ids)

        print(f"Precomputing shortest-path distances for {len(node_ids)} unique nodes...")

        for source in tqdm(node_ids, desc="Precomputing node distances"):
            try:
                lengths = nx.single_source_dijkstra_path_length(
                    self.graph,
                    source,
                    weight="weight",
                )
            except nx.NodeNotFound:
                continue

            for target in node_ids:
                key = (source, target) if source <= target else (target, source)

                if key not in self._distance_cache:
                    self._distance_cache[key] = float(lengths.get(target, float("inf")))

        print(f"Distance cache size: {len(self._distance_cache)}")