from pathlib import Path

from pipelines.common import resolve_path, run_command


def get_selected_dataset_output_path(root_dir: Path, config: dict) -> Path:
    cfg = config["dataset_selection"]

    dataset_name = cfg["dataset_name"]
    n = cfg["number_of_trajectories"]
    seed = cfg.get("random_seed", 42)

    output_root = resolve_path(
        root_dir,
        cfg.get("output_root", "input/cleandata"),
    )

    return output_root / dataset_name / f"{dataset_name}_{n}_seed_{seed}.dat"


def run_dataset_selection(root_dir: Path, config: dict):
    cfg = config.get("dataset_selection", {})

    if not cfg.get("enabled", False):
        return None

    script = root_dir / "tools" / "select_trajectories.py"
    python_exe = cfg.get("python", "python")

    input_file = resolve_path(root_dir, cfg["input_file"])
    output_file = get_selected_dataset_output_path(root_dir, config)

    command = [
        str(python_exe),
        str(script),

        "--input-file",
        str(input_file),

        "--output-file",
        str(output_file),

        "--number-of-trajectories",
        str(cfg["number_of_trajectories"]),

        "--random-seed",
        str(cfg.get("random_seed", 42)),
    ]

    if cfg.get("reindex", True):
        command.append("--reindex")

    print("\nSelecting trajectory subset...")
    run_command(command, cwd=root_dir)

    if not output_file.exists() or output_file.stat().st_size == 0:
        raise FileNotFoundError(f"Selected dataset was not created: {output_file}")

    return output_file