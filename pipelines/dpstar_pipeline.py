from pathlib import Path

from pipelines.common import resolve_path, run_command, format_epsilon_list


def prepare_dpstar_dataset(
    root_dir: Path,
    python_exe,
    prepare_script,
    input_path,
    scaling_rate,
    synthetic_count,
):
    if not prepare_script.exists():
        raise FileNotFoundError(f"Missing script: {prepare_script}")

    if not input_path.exists():
        raise FileNotFoundError(f"Missing DP-Star cleaned input: {input_path}")

    command = [
        str(python_exe),
        str(prepare_script),

        "--input",
        str(input_path),

        "--scaling-rate",
        str(scaling_rate),
    ]

    if synthetic_count is not None:
        command.extend([
            "--max-trajectories",
            str(synthetic_count),
        ])

    print("\nPreparing DP-Star dataset...")
    run_command(command, cwd=root_dir)
    print("\nDP-Star dataset prepared.")


def run_dp_star(
    dpstar_dir,
    python_exe,
    dpstar_main,
    epsilons,
    n_top_grid,
    beta_factor,
    epsilon_alloc,
    scaling_rate,
    synthetic_count,
):
    if not dpstar_main.exists():
        raise FileNotFoundError(f"Missing DP-Star main file: {dpstar_main}")

    command = [
        str(python_exe),
        str(dpstar_main),

        "--epsilons",
        format_epsilon_list(epsilons),

        "--n-top-grid",
        str(n_top_grid),

        "--beta-factor",
        str(beta_factor),

        "--epsilon-alloc",
        ",".join(str(v) for v in epsilon_alloc),

        "--mapping-rate",
        str(scaling_rate),
    ]

    if synthetic_count is not None:
        command.extend([
            "--synthetic-count",
            str(synthetic_count),
        ])

    print("\nRunning DP-Star...")
    run_command(command, cwd=dpstar_dir)
    print("\nDP-Star finished.")


def collect_dpstar_outputs(root_dir, python_exe, collect_script, dpstar_dir, output_root):
    if not collect_script.exists():
        raise FileNotFoundError(f"Missing script: {collect_script}")

    sd_root = (
        dpstar_dir
        / "data"
        / "Geolife Trajectories 1.3"
        / "SD"
    )

    command = [
        str(python_exe),
        str(collect_script),

        "--sd-root",
        str(sd_root),

        "--output-root",
        str(output_root),
    ]

    print("\nCollecting DP-Star outputs into .dat files...")
    run_command(command, cwd=root_dir)
    print("\nDP-Star .dat outputs created.")


def run_dpstar_pipeline(root_dir: Path, config: dict):
    shared = config["parameters"]
    cfg = config["dp_methods"]["dp-star"]

    dpstar_dir = root_dir / cfg.get("project_dir", "DP_Star")
    dpstar_main = dpstar_dir / "dp_star_main.py"

    prepare_script = root_dir / "tools" / "prepare_dpstar_dataset.py"
    collect_script = root_dir / "tools" / "collect_dpstar_sd_to_dat.py"

    python_exe = cfg.get("python", "python")

    input_path = resolve_path(root_dir, cfg["input_path"])
    output_root = resolve_path(root_dir, cfg["output_path"])

    epsilons = cfg.get("epsilon_values", shared["epsilon_values"])

    scaling_rate = cfg.get("scaling_rate", 500)
    n_top_grid = cfg.get("n_top_grid", shared.get("grid_size", 15))
    beta_factor = cfg.get("beta_factor", 80)

    epsilon_alloc = cfg.get(
        "epsilon_allocation",
        [1 / 9, 3 / 9, 4 / 9, 1 / 9],
    )

    synthetic_count = cfg.get("synthetic_count", None)

    print("\n############ DP-Star BEGIN ############")

    prepare_dpstar_dataset(
        root_dir=root_dir,
        python_exe=python_exe,
        prepare_script=prepare_script,
        input_path=input_path,
        scaling_rate=scaling_rate,
        synthetic_count=synthetic_count,
    )

    run_dp_star(
        dpstar_dir=dpstar_dir,
        python_exe=python_exe,
        dpstar_main=dpstar_main,
        epsilons=epsilons,
        n_top_grid=n_top_grid,
        beta_factor=beta_factor,
        epsilon_alloc=epsilon_alloc,
        scaling_rate=scaling_rate,
        synthetic_count=synthetic_count,
    )

    collect_dpstar_outputs(
        root_dir=root_dir,
        python_exe=python_exe,
        collect_script=collect_script,
        dpstar_dir=dpstar_dir,
        output_root=output_root,
    )

    print("\n############ DP-Star END ############")