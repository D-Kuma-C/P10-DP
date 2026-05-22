from pathlib import Path
import os
import sys
import shutil

from pipelines.common import resolve_path, run_command


def find_adatrace_xy_outputs(output_root: Path):
    results = []

    for eps_dir in sorted(output_root.glob("eps_*")):
        if not eps_dir.is_dir():
            continue

        epsilon = eps_dir.name.replace("eps_", "")

        for dat_file in sorted(eps_dir.glob("*.dat")):
            results.append((epsilon, dat_file))

    if not results:
        raise FileNotFoundError(f"No AdaTrace x,y .dat files found under: {output_root}")

    return results


def convert_adatrace_outputs_to_gps(root_dir: Path, config: dict):
    cfg = config["dp_methods"]["adatrace"]

    xy_output_root = resolve_path(root_dir, cfg["output_path"])
    gps_output_root = resolve_path(root_dir, cfg["gps_output_path"])

    convert_script = root_dir / "tools" / "convert_cartesian_to_gps.py"

    python_exe = cfg.get("python", "python")

    source_crs = cfg.get("target_crs", "EPSG:32629")
    target_crs = cfg.get("source_crs", "EPSG:4326")

    if not convert_script.exists():
        raise FileNotFoundError(f"Missing converter script: {convert_script}")

    for epsilon, xy_file in find_adatrace_xy_outputs(xy_output_root):
        gps_file = gps_output_root / f"eps_{epsilon}" / xy_file.name

        command = [
            str(python_exe),
            str(convert_script),

            "--input",
            str(xy_file),

            "--output",
            str(gps_file),

            "--source-crs",
            source_crs,

            "--target-crs",
            target_crs,
        ]

        print("\nConverting AdaTrace synthetic x,y to lon,lat...")
        print(f"Epsilon: {epsilon}")
        print(f"Input x,y: {xy_file}")
        print(f"Output lon,lat: {gps_file}")

        run_command(command, cwd=root_dir)


def get_adatrace_output_dir(output_root: Path, epsilon):
    return output_root / f"eps_{epsilon}"


def validate_adatrace_paths(adatrace_dir, src_dir, commons_math_jar, kd_jar, input_gps, convert_script):
    required_paths = [
        adatrace_dir,
        src_dir,
        commons_math_jar,
        kd_jar,
        input_gps,
        convert_script,
    ]

    missing = [p for p in required_paths if not p.exists()]

    if missing:
        missing_text = "\n".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing required AdaTrace files/folders:\n{missing_text}"
        )


def clean_build_folder(build_dir: Path):
    build_dir.mkdir(parents=True, exist_ok=True)

    for item in build_dir.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def get_java_files(src_dir: Path):
    java_files = []

    for file_path in src_dir.rglob("*.java"):
        if file_path.name == "Wigner3jGUI.java":
            continue

        java_files.append(str(file_path))

    if not java_files:
        raise FileNotFoundError(f"No Java files found in {src_dir}")

    return java_files


def prepare_adatrace_dataset(root_dir: Path, python_exe, convert_script, input_gps, input_xy, target_crs):
    command = [
        str(python_exe),
        str(convert_script),

        "--input",
        str(input_gps),

        "--output",
        str(input_xy),

        "--target-crs",
        str(target_crs),
    ]

    print("\nPreparing AdaTrace dataset...")
    run_command(command, cwd=root_dir)

    if not input_xy.exists() or input_xy.stat().st_size == 0:
        raise FileNotFoundError(
            f"AdaTrace converted input was not created or is empty:\n{input_xy}"
        )


def compile_adatrace(adatrace_dir, src_dir, build_dir, commons_math_jar, kd_jar):
    clean_build_folder(build_dir)
    java_files = get_java_files(src_dir)

    classpath = os.pathsep.join([
        str(commons_math_jar),
        str(kd_jar),
    ])

    command = [
        "javac",
        "-d",
        str(build_dir),
        "-cp",
        classpath,
        *java_files,
    ]

    print("\nCompiling AdaTrace...")
    run_command(command, cwd=adatrace_dir)

    main_class = build_dir / "Main.class"

    if not main_class.exists():
        raise FileNotFoundError(
            f"Compilation finished, but Main.class was not found:\n{main_class}"
        )

    print("\nAdaTrace compiled successfully.")


def run_adatrace(
    adatrace_dir,
    build_dir,
    commons_math_jar,
    kd_jar,
    input_xy,
    output_dir,
    epsilon,
    iterations,
    cell_count,
    interp,
    attacks_on,
    budget_weights,
):
    main_class = build_dir / "Main.class"

    if not main_class.exists():
        raise FileNotFoundError(f"Main.class was not found:\n{main_class}")

    output_dir.mkdir(parents=True, exist_ok=True)

    classpath = os.pathsep.join([
        str(build_dir),
        str(commons_math_jar),
        str(kd_jar),
    ])

    budget_weights_text = ",".join(str(w) for w in budget_weights)

    command = [
        "java",
        "-Duser.language=en",
        "-Duser.region=US",
        "-cp",
        classpath,
        "Main",

        "--input",
        str(input_xy),

        "--output-dir",
        str(output_dir),

        "--epsilon",
        str(epsilon),

        "--iterations",
        str(iterations),

        "--cell-count",
        str(cell_count),

        "--interp",
        str(interp).lower(),

        "--attacks-on",
        str(attacks_on).lower(),

        "--budget-weights",
        budget_weights_text,
    ]

    print("\nRunning AdaTrace...")
    print(f"Epsilon: {epsilon}")
    print(f"Output dir: {output_dir}")
    run_command(command, cwd=adatrace_dir)
    print(f"\nAdaTrace finished for epsilon {epsilon}.")


def run_adatrace_pipeline(root_dir: Path, config: dict):
    shared = config["parameters"]
    cfg = config["dp_methods"]["adatrace"]

    adatrace_dir = root_dir / cfg.get("project_dir", "adatrace")
    src_dir = adatrace_dir / "src"
    build_dir = adatrace_dir / "build"

    commons_math_jar = adatrace_dir / "commons-math3-3.4.1.jar"
    kd_jar = adatrace_dir / "kd.jar"

    convert_script = root_dir / "tools" / "convert_gps_to_cartesian.py"

    input_gps = resolve_path(root_dir, cfg["input_path"])
    input_xy = resolve_path(root_dir, cfg["xy_input_path"])
    output_root = resolve_path(root_dir, cfg["output_path"])

    python_exe = cfg.get("python", sys.executable)
    target_crs = cfg.get("target_crs", "EPSG:32629")

    epsilons = shared["epsilon_values"]
    cell_count = shared["grid_size"]

    iterations = cfg.get("iterations", 1)
    interp = cfg.get("interp", True)
    attacks_on = cfg.get("attacks_on", True)

    budget_weights = cfg.get(
        "epsilon_allocation",
        shared.get("epsilon_allocation", [0.05, 0.35, 0.50, 0.10]),
    )

    validate_adatrace_paths(
        adatrace_dir=adatrace_dir,
        src_dir=src_dir,
        commons_math_jar=commons_math_jar,
        kd_jar=kd_jar,
        input_gps=input_gps,
        convert_script=convert_script,
    )

    prepare_adatrace_dataset(
        root_dir=root_dir,
        python_exe=python_exe,
        convert_script=convert_script,
        input_gps=input_gps,
        input_xy=input_xy,
        target_crs=target_crs,
    )

    compile_adatrace(
        adatrace_dir=adatrace_dir,
        src_dir=src_dir,
        build_dir=build_dir,
        commons_math_jar=commons_math_jar,
        kd_jar=kd_jar,
    )

    for epsilon in epsilons:
        run_adatrace(
            adatrace_dir=adatrace_dir,
            build_dir=build_dir,
            commons_math_jar=commons_math_jar,
            kd_jar=kd_jar,
            input_xy=input_xy,
            output_dir=get_adatrace_output_dir(output_root, epsilon),
            epsilon=epsilon,
            iterations=iterations,
            cell_count=cell_count,
            interp=interp,
            attacks_on=attacks_on,
            budget_weights=budget_weights,
        )