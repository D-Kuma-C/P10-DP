from pathlib import Path
import csv
import shutil

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


def combine_segment_files(original_segments_file, synthetic_segments_file, combined_file):
    combined_file.parent.mkdir(parents=True, exist_ok=True)

    with combined_file.open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow([
            "dataset",
            "traj_id",
            "order",
            "segment_id",
            "start_node",
            "end_node",
        ])

        for source_file in [original_segments_file, synthetic_segments_file]:
            with source_file.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    writer.writerow([
                        row["dataset"],
                        row["traj_id"],
                        row["order"],
                        row["segment_id"],
                        row["start_node"],
                        row["end_node"],
                    ])


def run_mapmatching_command(
    root_dir,
    config,
    input_file,
    output_file,
    segments_file,
    nodes_file,
    edges_file,
    edge_registry_file,
    dataset_label,
    overwrite_input,
):
    map_cfg = config["map_matching"]

    script = resolve_path(root_dir, map_cfg.get("script", "tools/mapmatching.py"))
    python_exe = map_cfg.get("python", "python")

    command = [
        str(python_exe),
        str(script),

        "--input-file",
        str(input_file),

        "--output-file",
        str(output_file),

        "--segments-file",
        str(segments_file),

        "--nodes-file",
        str(nodes_file),

        "--edges-file",
        str(edges_file),

        "--edge-registry-file",
        str(edge_registry_file),

        "--dataset-label",
        dataset_label,

        "--osrm-url",
        str(map_cfg.get("osrm_url", "http://localhost:5000/route/v1/driving")),

        "--max-match-points",
        str(map_cfg.get("max_match_points", 100)),

        "--start-id",
        str(map_cfg.get("start_id", 0)),
    ]

    end_id = map_cfg.get("end_id", None)

    if end_id is not None:
        command.extend(["--end-id", str(end_id)])

    if overwrite_input:
        command.append("--overwrite-input")

    run_command(command, cwd=root_dir)


def run_mapmatching_for_method(root_dir: Path, config: dict, dp_method_key: str):
    map_cfg = config.get("map_matching_synthetic", {})

    if not map_cfg.get("enabled", False):
        return

    method_cfg = config["dp_methods"][dp_method_key]

    if dp_method_key == "adatrace":
        synthetic_root = resolve_path(root_dir, method_cfg["gps_output_path"])
    else:
        synthetic_root = resolve_path(root_dir, method_cfg["output_path"])
    original_input = resolve_path(root_dir, method_cfg["input_path"])

    segments_root = resolve_path(
        root_dir,
        map_cfg.get("segments_root", "input/segments"),
    )

    model_folder = MODEL_NAMES.get(dp_method_key, dp_method_key)
    model_segments_root = segments_root / model_folder
    model_segments_root.mkdir(parents=True, exist_ok=True)

    nodes_file = model_segments_root / "nodes.csv"
    edges_file = model_segments_root / "edges.csv"
    edge_registry_file = model_segments_root / "edge_registry.json"

    original_segments_file = model_segments_root / "original_segments.csv"
    original_mapmatched_file = model_segments_root / "original_mapmatched.dat"

    run_original_once = map_cfg.get("run_original_once", True)

    if (
        not run_original_once
        or not original_segments_file.exists()
        or not nodes_file.exists()
        or not edges_file.exists()
        or not edge_registry_file.exists()
    ):
        print("\nMap-matching original dataset for segment extraction...")
        run_mapmatching_command(
            root_dir=root_dir,
            config=config,
            input_file=original_input,
            output_file=original_mapmatched_file,
            segments_file=original_segments_file,
            nodes_file=nodes_file,
            edges_file=edges_file,
            edge_registry_file=edge_registry_file,
            dataset_label="original",
            overwrite_input=map_cfg.get("overwrite_original", False),
        )
    else:
        print(f"\nOriginal segment file already exists, skipping: {original_segments_file}")

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        eps_label = f"eps_{epsilon}"
        eps_segments_dir = model_segments_root / eps_label
        eps_segments_dir.mkdir(parents=True, exist_ok=True)

        synthetic_segments_file = eps_segments_dir / f"{synthetic_file.stem}_segments.csv"
        combined_segments_file = eps_segments_dir / f"{synthetic_file.stem}_trajectory_segments.csv"

        print("\nMap-matching synthetic dataset...")
        run_mapmatching_command(
            root_dir=root_dir,
            config=config,
            input_file=synthetic_file,
            output_file=synthetic_file,
            segments_file=synthetic_segments_file,
            nodes_file=nodes_file,
            edges_file=edges_file,
            edge_registry_file=edge_registry_file,
            dataset_label="synthetic",
            overwrite_input=map_cfg.get("overwrite_synthetic", True),
        )

        print("\nCombining original + synthetic segment files...")
        combine_segment_files(
            original_segments_file=original_segments_file,
            synthetic_segments_file=synthetic_segments_file,
            combined_file=combined_segments_file,
        )

        print(f"Combined trajectory segments: {combined_segments_file}")