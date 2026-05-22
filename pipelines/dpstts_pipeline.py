from pathlib import Path

from pipelines.common import resolve_path, run_command, format_epsilon_list


def validate_dpstts_paths(dpstts_dir, prepare_script, tpm_script, input_path):
    required_paths = [
        dpstts_dir,
        prepare_script,
        tpm_script,
        input_path,
    ]

    missing = [p for p in required_paths if not p.exists()]

    if missing:
        missing_text = "\n".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing required DP-STTS files/folders:\n{missing_text}"
        )


def prepare_dpstts_dataset(
    root_dir,
    python_exe,
    prepare_script,
    input_path,
    dpstts_dir,
    output_root,
    epsilons,
    cell_h,
    cell_w,
    time_step,
    full_day_time,
):
    command = [
        str(python_exe),
        str(prepare_script),

        "--input",
        str(input_path),

        "--dpstts-dir",
        str(dpstts_dir),

        "--output-root",
        str(output_root),

        "--epsilons",
        format_epsilon_list(epsilons),

        "--cell-h",
        str(cell_h),

        "--cell-w",
        str(cell_w),

        "--time-step",
        str(time_step),
    ]

    if full_day_time:
        command.append("--full-day-time")

    print("\nPreparing DP-STTS dataset...")
    run_command(command, cwd=root_dir)
    print("\nDP-STTS dataset prepared.")


def run_dpstts(
    dpstts_dir,
    python_exe,
    tpm_script,
    dataset,
    epsilons,
    iterations,
    epsilon_prefix_ratio,
    output_root,
    random_seed,
):
    command = [
        str(python_exe),
        str(tpm_script),

        "--dataset",
        str(dataset),

        "--epsilons",
        format_epsilon_list(epsilons),

        "--iterations",
        str(iterations),

        "--epsilon-prefix-ratio",
        str(epsilon_prefix_ratio),

        "--output-root",
        str(output_root),
    ]

    if random_seed is not None:
        command.extend([
            "--random-seed",
            str(random_seed),
        ])

    print("\nRunning DP-STTS...")
    run_command(command, cwd=dpstts_dir)
    print("\nDP-STTS finished.")


def run_dpstts_pipeline(root_dir: Path, config: dict):
    shared = config["parameters"]
    cfg = config["dp_methods"]["dp-stts"]

    dpstts_dir = root_dir / cfg.get("project_dir", "DP_STTS")

    prepare_script = root_dir / "tools" / "prepare_dpstts_dataset.py"
    tpm_script = dpstts_dir / "TPM.py"

    python_exe = cfg.get("python", "python")

    input_path = resolve_path(root_dir, cfg["input_path"])
    output_root = resolve_path(root_dir, cfg["output_path"])

    epsilons = cfg.get("epsilon_values", shared["epsilon_values"])

    dataset = cfg.get("dataset", "Porto")
    cell_h = cfg.get("cell_h", 6)
    cell_w = cfg.get("cell_w", 6)
    time_step = cfg.get("time_step", 15)
    full_day_time = cfg.get("full_day_time", False)

    iterations = cfg.get("iterations", 1)
    epsilon_prefix_ratio = cfg.get("epsilon_prefix_ratio", 0.5)
    random_seed = cfg.get("random_seed", None)

    validate_dpstts_paths(
        dpstts_dir=dpstts_dir,
        prepare_script=prepare_script,
        tpm_script=tpm_script,
        input_path=input_path,
    )

    prepare_dpstts_dataset(
        root_dir=root_dir,
        python_exe=python_exe,
        prepare_script=prepare_script,
        input_path=input_path,
        dpstts_dir=dpstts_dir,
        output_root=output_root,
        epsilons=epsilons,
        cell_h=cell_h,
        cell_w=cell_w,
        time_step=time_step,
        full_day_time=full_day_time,
    )

    run_dpstts(
        dpstts_dir=dpstts_dir,
        python_exe=python_exe,
        tpm_script=tpm_script,
        dataset=dataset,
        epsilons=epsilons,
        iterations=iterations,
        epsilon_prefix_ratio=epsilon_prefix_ratio,
        output_root=output_root,
        random_seed=random_seed,
    )