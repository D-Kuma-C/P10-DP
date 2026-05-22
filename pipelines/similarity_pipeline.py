from pathlib import Path

from pipelines.common import resolve_path, run_command


MODEL_NAMES = {
    "adatrace": "adatrace",
    "dp-star": "dpstar",
    "privtrace": "privtrace",
    "dp-stts": "dpstts",
}


def find_synthetic_files_for_model(synthetic_root: Path):
    if not synthetic_root.exists():
        raise FileNotFoundError(f"Synthetic root does not exist: {synthetic_root}")

    results = []

    for eps_dir in sorted(synthetic_root.glob("eps_*")):
        if not eps_dir.is_dir():
            continue

        epsilon = eps_dir.name.replace("eps_", "")

        for dat_file in sorted(eps_dir.glob("*.dat")):
            results.append((epsilon, dat_file))

    if not results:
        raise FileNotFoundError(f"No synthetic .dat files found under: {synthetic_root}")

    return results


def run_similarity_for_method(root_dir: Path, config: dict, dp_method_key: str):
    sim_cfg = config.get("trajectory_similarity", {})

    if not sim_cfg.get("enabled", False):
        return

    method_cfg = config["dp_methods"][dp_method_key]
    map_cfg = config["map_matching"]
    shared = config["parameters"]

    model_name = MODEL_NAMES.get(dp_method_key, dp_method_key)

    similarity_dir = resolve_path(
        root_dir,
        sim_cfg.get("project_dir", "trajectory_similarity"),
    )

    similarity_main = similarity_dir / sim_cfg.get("main_script", "src/main.py")
    python_exe = sim_cfg.get("python", "python")

    if not similarity_main.exists():
        raise FileNotFoundError(f"Missing trajectory similarity main script: {similarity_main}")

    original_path = resolve_path(root_dir, method_cfg["input_path"])
    if dp_method_key == "adatrace":
        synthetic_root = resolve_path(root_dir, method_cfg["gps_output_path"])
    else:
        synthetic_root = resolve_path(root_dir, method_cfg["output_path"])

    segments_root = resolve_path(
        root_dir,
        map_cfg.get("segments_root", "input/segments"),
    )

    model_segments_root = segments_root / model_name

    nodes_file = model_segments_root / "nodes.csv"
    edges_file = model_segments_root / "edges.csv"

    if not nodes_file.exists():
        raise FileNotFoundError(f"Missing nodes.csv: {nodes_file}")

    if not edges_file.exists():
        raise FileNotFoundError(f"Missing edges.csv: {edges_file}")

    output_root = resolve_path(
        root_dir,
        sim_cfg.get("output_root", "output/Similarity"),
    )

    dataset_name = shared.get("dataset_name", "porto")
    trajectory_count_label = sim_cfg.get("trajectory_count_label", "500")

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        eps_label = f"eps_{epsilon}"
        eps_segments_dir = model_segments_root / eps_label

        segments_file = eps_segments_dir / f"{synthetic_file.stem}_trajectory_segments.csv"

        if not segments_file.exists():
            raise FileNotFoundError(
                "Missing combined trajectory segment file. "
                "Map-matching must run before trajectory similarity:\n"
                f"{segments_file}"
            )

        command = [
            str(python_exe),
            str(similarity_main),

            "--original",
            str(original_path),

            "--synthetic",
            str(synthetic_file),

            "--epsilon",
            str(epsilon),

            "--dp-model",
            model_name,

            "--trajectory-count-label",
            str(trajectory_count_label),

            "--dataset-name",
            str(dataset_name),

            "--network-mode",
            "prebuilt",

            "--nodes",
            str(nodes_file),

            "--edges",
            str(edges_file),

            "--segments",
            str(segments_file),

            "--output-dir",
            str(output_root),

            "--max-pairs",
            str(sim_cfg.get("max_pairs", 10000)),

            "--random-seed",
            str(sim_cfg.get("random_seed", 42)),

            "--netedr-threshold",
            str(sim_cfg.get("netedr_threshold", 1000.0)),

            "--neterp-gap-cost",
            str(sim_cfg.get("neterp_gap_cost", 1.0)),
        ]

        print("\nRunning trajectory similarity...")
        print(f"DP method: {dp_method_key}")
        print(f"Epsilon: {epsilon}")
        print(f"Original: {original_path}")
        print(f"Synthetic: {synthetic_file}")
        print(f"Nodes: {nodes_file}")
        print(f"Edges: {edges_file}")
        print(f"Segments: {segments_file}")
        print(f"Output: {output_root}")

        run_command(command, cwd=similarity_dir)