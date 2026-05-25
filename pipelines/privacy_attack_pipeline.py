from pathlib import Path
import re

from pipelines.common import resolve_path, run_command


ATTACK_FOLDER_NAMES = {
    "reid": "reidentification",
    "bayesian": "bayesian",
    "partial": "partial",
    "outlier": "outlier",
}


def extract_iteration_label(file_path: Path) -> str:
    """
    Extracts iteration labels from filenames like:

        something_iteration0.dat
        something_iteration_0.dat
        something_iter_1.dat
        something_iter1.dat

    Returns:
        iteration0, iteration1, etc.
    """
    name = file_path.stem.lower()

    patterns = [
        r"iteration[_-]?(\d+)",
        r"iter[_-]?(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return f"iteration{match.group(1)}"

    return "iteration_unknown"


def find_synthetic_files_for_model(synthetic_root: Path):
    """
    Finds synthetic .dat files under:

        synthetic_root/eps_0.5/*.dat
        synthetic_root/eps_1.0/*.dat

    Returns:
        list[(epsilon, synthetic_file)]
    """
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


def validate_privacy_attack_paths(privacy_attack_script: Path):
    if not privacy_attack_script.exists():
        raise FileNotFoundError(
            f"Missing privacy attack script:\n{privacy_attack_script}"
        )


def run_privacy_attack_for_file(
    root_dir: Path,
    config: dict,
    model_name: str,
    original_path: Path,
    synthetic_path: Path,
    epsilon: str,
    input_coordinates: str,
    coordinate_order: str = "lonlat",
):
    privacy_cfg = config["privacy_attack"]

    privacy_attack_dir = root_dir / privacy_cfg.get("project_dir", "Privacy_attack")
    privacy_attack_script = privacy_attack_dir / privacy_cfg.get("main_script", "PrivacyAttack_main.py")
    privacy_attack_python = privacy_cfg.get("python", "python")

    output_root = resolve_path(
        root_dir,
        privacy_cfg.get("output_root", "output/Privacy"),
    )

    validate_privacy_attack_paths(privacy_attack_script)

    if not original_path.exists():
        raise FileNotFoundError(f"Original file does not exist: {original_path}")

    if not synthetic_path.exists():
        raise FileNotFoundError(f"Synthetic file does not exist: {synthetic_path}")

    attacks = privacy_cfg.get("attacks", ["reid", "bayesian", "partial", "outlier"])
    iteration_label = extract_iteration_label(synthetic_path)

    for attack_arg in attacks:
        if attack_arg == "all":
            output_path = (
                output_root
                / model_name
                / f"eps_{epsilon}"
                / iteration_label
            )
        else:
            output_path = (
                output_root
                / model_name
                / f"eps_{epsilon}"
                / iteration_label
            )

        output_path.mkdir(parents=True, exist_ok=True)

        command = [
            str(privacy_attack_python),
            str(privacy_attack_script),

            "--orig-path",
            str(original_path),

            "--synth-path",
            str(synthetic_path),

            "--output-path",
            str(output_path),

            "--dataset-name",
            privacy_cfg.get("dataset_name", config["parameters"].get("dataset_name", "porto")),

            "--model-name",
            model_name,

            "--epsilon",
            str(epsilon),

            "--input-coordinates",
            input_coordinates,

            "--coordinate-order",
            coordinate_order,

            "--attacks",
            attack_arg,

            "--grid-size",
            str(privacy_cfg.get("grid_size", config["parameters"].get("grid_size", 20))),

            "--time-period-hours",
            str(privacy_cfg.get("time_period_hours", 24)),

            "--interval-minutes",
            str(privacy_cfg.get("interval_minutes", 15)),

            "--known-locations",
            str(privacy_cfg.get("known_locations", 3)),

            "--test-users",
            str(privacy_cfg.get("test_users", 3)),

            "--random-state",
            str(privacy_cfg.get("random_state", 0)),

            "--n-clusters",
            str(privacy_cfg.get("n_clusters", 4)),

            "--vartheta",
            str(privacy_cfg.get("vartheta", 0.1)),

            "--sensitive-n",
            str(privacy_cfg.get("sensitive_n", 10)),

            "--sniff-n",
            str(privacy_cfg.get("sniff_n", 12)),

            "--intersection-threshold",
            str(privacy_cfg.get("intersection_threshold", 5)),

            "--top-k-neighbors",
            str(privacy_cfg.get("top_k_neighbors", 50)),

            "--n-outliers",
            str(privacy_cfg.get("n_outliers", 200)),

            "--closest-threshold",
            str(privacy_cfg.get("closest_threshold", 0.1)),

            "--plausible-deniability-kappa",
            str(privacy_cfg.get("plausible_deniability_kappa", 100)),

            "--plausible-deniability-beta",
            str(privacy_cfg.get("plausible_deniability_beta", 0.05)),

            "--plausible-deniability-sample-size",
            str(privacy_cfg.get("plausible_deniability_sample_size", 100)),
        ]

        print("\nRunning privacy attack...")
        print(f"Attack: {attack_arg}")
        print(f"Model: {model_name}")
        print(f"Epsilon: {epsilon}")
        print(f"Iteration: {iteration_label}")
        print(f"Original: {original_path}")
        print(f"Synthetic: {synthetic_path}")
        print(f"Output: {output_path}")

        run_command(command, cwd=root_dir)

    print("\nPrivacy attacks finished.")


def run_privacy_attacks_for_adatrace(root_dir: Path, config: dict):
    cfg = config["dp_methods"]["adatrace"]

    synthetic_root = resolve_path(root_dir, cfg["output_path"])
    original_path = resolve_path(root_dir, cfg["xy_input_path"])

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            root_dir=root_dir,
            config=config,
            model_name="adatrace",
            original_path=original_path,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="xy",
            coordinate_order="lonlat",
        )


def run_privacy_attacks_for_dpstar(root_dir: Path, config: dict):
    cfg = config["dp_methods"]["dp-star"]

    synthetic_root = resolve_path(root_dir, cfg["output_path"])
    original_path = resolve_path(root_dir, cfg["input_path"])

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            root_dir=root_dir,
            config=config,
            model_name="dp_star",
            original_path=original_path,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="latlon",
            coordinate_order="lonlat",
        )


def run_privacy_attacks_for_privtrace(root_dir: Path, config: dict):
    cfg = config["dp_methods"]["privtrace"]

    synthetic_root = resolve_path(root_dir, cfg["output_path"])
    original_path = resolve_path(root_dir, cfg["input_path"])

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            root_dir=root_dir,
            config=config,
            model_name="privtrace",
            original_path=original_path,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="latlon",
            coordinate_order="lonlat",
        )


def run_privacy_attacks_for_dpstts(root_dir: Path, config: dict):
    cfg = config["dp_methods"]["dp-stts"]

    synthetic_root = resolve_path(root_dir, cfg["output_path"])
    original_path = resolve_path(root_dir, cfg["input_path"])

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            root_dir=root_dir,
            config=config,
            model_name="dp_stts",
            original_path=original_path,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="latlon",
            coordinate_order="lonlat",
        )