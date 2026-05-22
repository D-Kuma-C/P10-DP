from pathlib import Path
import time
import datetime

from pipelines.common import resolve_path, run_command, epsilon_label


def validate_privtrace_paths(privtrace_dir, privtrace_main, input_path, python_exe):
    required_paths = [
        privtrace_dir,
        privtrace_main,
        privtrace_dir / "config" / "folder_and_file_names.py",
        privtrace_dir / "config" / "parameter_setter.py",
        privtrace_dir / "config" / "parameter_carrier.py",
        privtrace_dir / "tools" / "data_reader.py",
        input_path,
    ]

    missing = [p for p in required_paths if not p.exists()]

    if missing:
        missing_text = "\n".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing required PrivTrace files/folders:\n{missing_text}"
        )

    python_path = Path(python_exe)

    if not python_path.exists():
        raise FileNotFoundError(
            f"PrivTrace Python executable not found:\n{python_path}"
        )


def run_privtrace_once(
    privtrace_dir,
    privtrace_main,
    python_exe,
    input_path,
    output_file,
    epsilon,
    epsilon_partition,
    trajectory_count,
):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(python_exe),
        "-u",
        str(privtrace_main),

        "--dataset_file_name",
        str(input_path),

        "--result_file_name",
        str(output_file),

        "--total_epsilon",
        str(epsilon),

        "--epsilon_partition",
        ",".join(str(v) for v in epsilon_partition),

        "--trajectory_number_to_generate",
        str(trajectory_count),
    ]

    start_time = time.time()
    start_datetime = datetime.datetime.now()

    print("\n" + "=" * 100, flush=True)
    print(f"STARTING PrivTrace", flush=True)
    print(f"Started at: {start_datetime}", flush=True)
    print(f"Epsilon: {epsilon}", flush=True)
    print(f"Input: {input_path}", flush=True)
    print(f"Output: {output_file}", flush=True)
    print("=" * 100 + "\n", flush=True)

    run_command(command, cwd=privtrace_dir)

    elapsed = time.time() - start_time
    end_datetime = datetime.datetime.now()

    print("\n" + "=" * 100, flush=True)
    print("FINISHED PrivTrace", flush=True)
    print(f"Epsilon: {epsilon}", flush=True)
    print(f"Finished at: {end_datetime}", flush=True)
    print(f"Elapsed seconds: {elapsed:.2f}", flush=True)
    print(f"Output exists: {output_file.exists()}", flush=True)
    print(f"Output: {output_file}", flush=True)
    print("=" * 100 + "\n", flush=True)


def run_privtrace_pipeline(root_dir: Path, config: dict):
    shared = config["parameters"]
    cfg = config["dp_methods"]["privtrace"]

    privtrace_dir = root_dir / cfg.get("project_dir", "PrivTrace-main")
    privtrace_main = privtrace_dir / "main.py"

    python_exe = cfg.get("python", "python")

    input_path = resolve_path(root_dir, cfg["input_path"])
    output_root = resolve_path(root_dir, cfg["output_path"])

    epsilons = cfg.get("epsilon_values", shared["epsilon_values"])

    epsilon_partition = cfg.get("epsilon_partition", [0.2, 0.6, 0.2])
    trajectory_count = cfg.get("trajectory_count", -1)

    validate_privtrace_paths(
        privtrace_dir=privtrace_dir,
        privtrace_main=privtrace_main,
        input_path=input_path,
        python_exe=python_exe,
    )

    print("\nPrivTrace epsilon list:", epsilons, flush=True)

    for epsilon in epsilons:
        eps_label = epsilon_label(epsilon)
        output_file = output_root / eps_label / f"privtrace_{eps_label}.dat"

        run_privtrace_once(
            privtrace_dir=privtrace_dir,
            privtrace_main=privtrace_main,
            python_exe=python_exe,
            input_path=input_path,
            output_file=output_file,
            epsilon=epsilon,
            epsilon_partition=epsilon_partition,
            trajectory_count=trajectory_count,
        )