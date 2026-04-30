import pandas as pd
import networkx as nx


class RoadMap:
    def __init__(self, node_file: str, edge_file: str):
        self.node_file = node_file
        self.edge_file = edge_file
        self.graph = nx.Graph()
        self.load_graph()

    def load_graph(self):
        edges = pd.read_csv(self.edge_file)

        for _, row in edges.iterrows():
            self.graph.add_edge(
                int(row["start_node"]),
                int(row["end_node"]),
                weight=float(row["length"]),
                segment_id=int(row["edge_id"]),
            )

    def shortest_path_distance(self, node_a: int, node_b: int) -> float:
        try:
            return nx.shortest_path_length(
                self.graph,
                source=node_a,
                target=node_b,
                weight="weight",
            )
        except Exception:
            return float("inf")