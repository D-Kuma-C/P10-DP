from pathlib import Path
import subprocess
import sys
import shutil
import os
import datetime
import time
import re


ROOT_DIR = Path(__file__).resolve().parent

#CONDA_EXE = r"C:\Users\test\Anaconda3\condabin\conda.bat"

DP_STAR_PYTHON = r"C:\Users\test\anaconda3\envs\dp-star\python.exe"


# -----------------------------
# AdaTrace paths
# -----------------------------
ADATRACE_DIR = ROOT_DIR / "adatrace"

SRC_DIR = ADATRACE_DIR / "src"
BUILD_DIR = ADATRACE_DIR / "build"

COMMONS_MATH_JAR = ADATRACE_DIR / "commons-math3-3.4.1.jar"
KD_JAR = ADATRACE_DIR / "kd.jar"

ADATRACE_INPUT_GPS = Path(
    r"C:\Users\test\Desktop\Uni\P10-DP\input\cleandata\porto\porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630_small_500.dat"
)

ADATRACE_INPUT_XY = Path(
    r"C:\Users\test\Desktop\Uni\P10-DP\input\cleandata\porto\porto_500_xy.dat"
)

ADATRACE_TARGET_CRS = "EPSG:32629"

ADATRACE_PYTHON = sys.executable


# -----------------------------
# DP-Star paths
# -----------------------------
DP_STAR_DIR = ROOT_DIR / "DP_Star"
DP_STAR_MAIN = DP_STAR_DIR / "dp_star_main.py"

PREPARE_DPSTAR_SCRIPT = ROOT_DIR / "tools" / "prepare_dpstar_dataset.py"
COLLECT_DPSTAR_SCRIPT = ROOT_DIR / "tools" / "collect_dpstar_sd_to_dat.py"

#DP_STAR_CONDA_ENV = "dp-star"

# -----------------------------
# PrivTrace paths
# -----------------------------

PRIVTRACE_DIR = ROOT_DIR / "PrivTrace-main"
PRIVTRACE_MAIN = PRIVTRACE_DIR / "main.py"

# Use the Python executable from the environment where PrivTrace dependencies are installed.
PRIVTRACE_PYTHON = r"C:\Users\test\anaconda3\envs\db_code_py310\python.exe"

# -----------------------------
# DP-STTS config
# -----------------------------

DP_STTS_DIR = ROOT_DIR / "DP_STTS"

DP_STTS_PREPARE_SCRIPT = ROOT_DIR / "tools" / "prepare_dpstts_dataset.py"
DP_STTS_TPM_SCRIPT = DP_STTS_DIR / "TPM.py"

#DP_STTS_PYTHON = sys.executable
# Or use a specific environment python:
DP_STTS_PYTHON = Path(r"C:\Users\test\anaconda3\envs\db_code_py310\python.exe")

# DP_STTS_DATASET = "Porto"
#
# DP_STTS_EPSILONS = [0.5, 1.0]
#
# DP_STTS_CELL_H = 6
# DP_STTS_CELL_W = 6
# DP_STTS_TIME_STEP = 15
#
# DP_STTS_ITERATIONS = 1
# DP_STTS_EPSILON_PREFIX_RATIO = 0.5
#
DP_STTS_RANDOM_SEED = None


# -----------------------------
# AdaTrace parameters
# -----------------------------

ADATRACE_INPUT = ADATRACE_INPUT_XY

ADATRACE_OUTPUT_ROOT = ROOT_DIR / "input" / "adatrace_synthetic"

ADATRACE_EPSILONS = [0.5,1.0]

ADATRACE_ITERATIONS = 3

ADATRACE_CELL_COUNT = 20 # 6 x 6 = 36 cell count

ADATRACE_INTERP = True

ADATRACE_ATTACKS_ON = True

# Format: grid, markov, trip, length
ADATRACE_BUDGET_WEIGHTS = [0.05, 0.35, 0.50, 0.10]

# -----------------------------
# DP-Star parameters
# -----------------------------

DP_STAR_CLEAN_INPUT = (
    ROOT_DIR
    / "input"
    / "cleandata"
    / "porto"
    / "porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630_small_500.dat"
)

DP_STAR_OUTPUT_ROOT = ROOT_DIR / "input" / "dpstar_synthetic"

DP_STAR_SCALING_RATE = 500

DP_STAR_EPSILONS = [0.1, 0.5, 1.0, 2.0]

DP_STAR_N_TOP_GRID = 15

DP_STAR_BETA_FACTOR = 80

# ag, td, markov, mle
DP_STAR_EPSILON_ALLOC = [1 / 9, 3 / 9, 4 / 9, 1 / 9]

# Keep as None to use the number of prepared trajectories.
DP_STAR_SYNTHETIC_COUNT = None

# -----------------------------
# PrivTrace parameters
# -----------------------------

PRIVTRACE_INPUT = (
    ROOT_DIR
    / "input"
    / "cleandata"
    / "porto"
    / "porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630_small_500.dat"
)

PRIVTRACE_OUTPUT_ROOT = ROOT_DIR / "input" / "privtrace_synthetic"

PRIVTRACE_EPSILONS = [0.5, 1.0]

# grid, Markov, guidepost/order-2
PRIVTRACE_EPSILON_PARTITION = [0.2, 0.6, 0.2]

# -1 means PrivTrace generates the same number as the original input.
PRIVTRACE_TRAJECTORY_COUNT = -1

# -----------------------------
# DP_STTS parameters
# -----------------------------

DP_STTS_INPUT = (
    ROOT_DIR
    / "input"
    / "cleandata"
    / "porto"
    / "porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630_small_500.dat"
)

DP_STTS_OUTPUT_ROOT = ROOT_DIR / "input" / "dpstts_synthetic"

DP_STTS_EPSILONS = [0.1, 0.5, 1.0, 2.0]

DP_STTS_DATASET = "Porto"

DP_STTS_CELL_H = 6
DP_STTS_CELL_W = 6

DP_STTS_TIME_STEP = 15  # minutes

DP_STTS_ITERATIONS = 1

DP_STTS_EPSILON_PREFIX_RATIO = 0.5


# -----------------------------
# Privacy attack config
# -----------------------------

PRIVACY_ATTACK_DIR = ROOT_DIR / "Privacy_attack"
PRIVACY_ATTACK_SCRIPT = PRIVACY_ATTACK_DIR / "PrivacyAttack_main.py"

PRIVACY_ATTACK_PYTHON = sys.executable

PRIVACY_OUTPUT_ROOT = ROOT_DIR / "output" / "Privacy"

PRIVACY_DATASET_NAME = "porto"
PRIVACY_TRAJECTORY_COUNT_LABEL = "500"

PRIVACY_ATTACKS = {
    "reid": "reidentification",
    "bayesian": "bayesian",
    "partial": "partial",
    "outlier": "outlier",
}

# General attack parameters
PRIVACY_GRID_SIZE = 20
PRIVACY_TIME_PERIOD_HOURS = 7.5
PRIVACY_INTERVAL_MINUTES = 1

# Re-identification
PRIVACY_KNOWN_LOCATIONS = 3
PRIVACY_TEST_USERS = 3
PRIVACY_RANDOM_STATE = 0
PRIVACY_N_CLUSTERS = 4

# Bayesian
PRIVACY_VARTHETA = 0.1
PRIVACY_SENSITIVE_N = 10

# Partial sniffing
PRIVACY_SNIFF_N = 12
PRIVACY_INTERSECTION_THRESHOLD = 5

# Outlier leakage
PRIVACY_TOP_K_NEIGHBORS = 50
PRIVACY_N_OUTLIERS = 200
PRIVACY_CLOSEST_THRESHOLD = 0.1
PRIVACY_PLAUSIBLE_DENIABILITY_KAPPA = 100
PRIVACY_PLAUSIBLE_DENIABILITY_BETA = 0.05


def run_command(command, cwd=None):
    print()
    print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in command))
    print()

    subprocess.run(
        [str(x) for x in command],
        cwd=cwd,
        check=True,
    )

def prepare_dpstar_dataset():
    """
    Converts cleaned .dat input into DP-Star working files:
        Trajectories/
        MDL/
        GPS_trajs_range.pkl
        MDL_trajs_range.pkl
        trajs_file_name_list.pkl

    Also deletes/recreates:
        Middleware/
        SD/
    """
    if not PREPARE_DPSTAR_SCRIPT.exists():
        raise FileNotFoundError(f"Missing script: {PREPARE_DPSTAR_SCRIPT}")

    if not DP_STAR_CLEAN_INPUT.exists():
        raise FileNotFoundError(f"Missing DP-Star cleaned input: {DP_STAR_CLEAN_INPUT}")

    command = [
        DP_STAR_PYTHON,
        str(PREPARE_DPSTAR_SCRIPT),
        "--input",
        str(DP_STAR_CLEAN_INPUT),
        "--scaling-rate",
        str(DP_STAR_SCALING_RATE),
    ]

    if DP_STAR_SYNTHETIC_COUNT is not None:
        command.extend([
            "--max-trajectories",
            str(DP_STAR_SYNTHETIC_COUNT),
        ])


    print("\n############ DP-Star BEGIN ############")

    print("\nPreparing DP-Star dataset...")
    run_command(command, cwd=ROOT_DIR)
    print("\nDP-Star dataset prepared.")


def run_dp_star():
    """
    Runs DP-Star model generation using parameters.
    Input/output folders are handled by prepare_dpstar_dataset.py
    and collect_dpstar_sd_to_dat.py.
    """
    if not DP_STAR_MAIN.exists():
        raise FileNotFoundError(f"Missing DP-Star main file: {DP_STAR_MAIN}")

    epsilons = ",".join(str(e) for e in DP_STAR_EPSILONS)
    epsilon_alloc = ",".join(str(v) for v in DP_STAR_EPSILON_ALLOC)

    command = [
        DP_STAR_PYTHON,
        str(DP_STAR_MAIN),

        "--epsilons",
        epsilons,

        "--n-top-grid",
        str(DP_STAR_N_TOP_GRID),

        "--beta-factor",
        str(DP_STAR_BETA_FACTOR),

        "--epsilon-alloc",
        epsilon_alloc,

        "--mapping-rate",
        str(DP_STAR_SCALING_RATE),
    ]

    if DP_STAR_SYNTHETIC_COUNT is not None:
        command.extend([
            "--synthetic-count",
            str(DP_STAR_SYNTHETIC_COUNT),
        ])

    print("\nRunning DP-Star...")
    run_command(command, cwd=DP_STAR_DIR)
    print("\nDP-Star finished.")


def collect_dpstar_outputs():
    """
    Converts DP-Star final txt outputs into .dat files:

        DP-Star/data/Geolife Trajectories 1.3/SD/sd_final_epsilon_*/
        ->
        root/input/dpstar_synthetic/eps_*/dpstar_eps_*.dat
    """
    if not COLLECT_DPSTAR_SCRIPT.exists():
        raise FileNotFoundError(f"Missing script: {COLLECT_DPSTAR_SCRIPT}")

    sd_root = (
        DP_STAR_DIR
        / "data"
        / "Geolife Trajectories 1.3"
        / "SD"
    )

    command = [
        DP_STAR_PYTHON,
        str(COLLECT_DPSTAR_SCRIPT),

        "--sd-root",
        str(sd_root),

        "--output-root",
        str(DP_STAR_OUTPUT_ROOT),
    ]

    print("\nCollecting DP-Star outputs into .dat files...")
    run_command(command, cwd=ROOT_DIR)
    print("\nDP-Star .dat outputs created.")

    print("\n############ DP-Star END ############")


def get_adatrace_output_dir(epsilon):
    return ADATRACE_OUTPUT_ROOT / f"eps_{epsilon}"


def validate_adatrace_paths():
    required_paths = [
        ADATRACE_DIR,
        SRC_DIR,
        COMMONS_MATH_JAR,
        KD_JAR,
        ADATRACE_INPUT,
    ]

    missing = [p for p in required_paths if not p.exists()]

    if missing:
        missing_text = "\n".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing required AdaTrace files/folders:\n{missing_text}"
        )


def clean_build_folder():
    """
    Delete every file and folder inside the AdaTrace build folder
    before compiling.

    The build folder itself is kept/recreated.
    """
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    for item in BUILD_DIR.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def get_java_files():
    java_files = []

    for file_path in SRC_DIR.rglob("*.java"):
        # Exclude this because it imports old Java Applet classes.
        if file_path.name == "Wigner3jGUI.java":
            continue

        java_files.append(str(file_path))

    if not java_files:
        raise FileNotFoundError(f"No Java files found in {SRC_DIR}")

    return java_files

def prepare_adatrace_dataset():
    command = [
        str(ADATRACE_PYTHON),
        str(ROOT_DIR / "tools" / "convert_gps_to_cartesian.py"),

        "--input",
        str(ADATRACE_INPUT_GPS),

        "--output",
        str(ADATRACE_INPUT_XY),

        "--target-crs",
        ADATRACE_TARGET_CRS,
    ]

    print("\nPreparing AdaTrace dataset...")
    print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in command))
    print()

    subprocess.run(
        command,
        cwd=ROOT_DIR,
        check=True,
    )

def compile_adatrace():
    validate_adatrace_paths()
    clean_build_folder()

    java_files = get_java_files()

    classpath = os.pathsep.join([
        str(COMMONS_MATH_JAR),
        str(KD_JAR),
    ])

    command = [
        "javac",
        "-d",
        str(BUILD_DIR),
        "-cp",
        classpath,
        *java_files,
    ]

    print("Compiling AdaTrace...")
    print(" ".join(f'"{x}"' if " " in x else x for x in command))
    print()

    subprocess.run(
        command,
        cwd=ADATRACE_DIR,
        check=True,
    )

    main_class = BUILD_DIR / "Main.class"

    if not main_class.exists():
        raise FileNotFoundError(
            f"Compilation finished, but Main.class was not found:\n{main_class}"
        )

    print("\nAdaTrace compiled successfully.")


def run_adatrace(epsilon):
    main_class = BUILD_DIR / "Main.class"

    if not main_class.exists():
        raise FileNotFoundError(
            f"Main.class was not found:\n{main_class}"
        )

    adatrace_output_dir = get_adatrace_output_dir(epsilon)
    adatrace_output_dir.mkdir(parents=True, exist_ok=True)

    classpath = os.pathsep.join([
        str(BUILD_DIR),
        str(COMMONS_MATH_JAR),
        str(KD_JAR),
    ])

    budget_weights = ",".join(str(w) for w in ADATRACE_BUDGET_WEIGHTS)

    command = [
        "java",
        "-cp",
        classpath,
        "Main",

        "--input",
        str(ADATRACE_INPUT),

        "--output-dir",
        str(adatrace_output_dir),

        "--epsilon",
        str(epsilon),

        "--iterations",
        str(ADATRACE_ITERATIONS),

        "--cell-count",
        str(ADATRACE_CELL_COUNT),

        "--interp",
        str(ADATRACE_INTERP).lower(),

        "--attacks-on",
        str(ADATRACE_ATTACKS_ON).lower(),

        "--budget-weights",
        budget_weights,
    ]

    print("\nRunning AdaTrace...")
    print(" ".join(f'"{x}"' if " " in x else x for x in command))
    print()

    subprocess.run(
        command,
        cwd=ADATRACE_DIR,
        check=True,
    )

    print("\nAdaTrace finished.")

def validate_privtrace_paths():
    required_paths = [
        PRIVTRACE_DIR,
        PRIVTRACE_MAIN,
        PRIVTRACE_DIR / "config" / "folder_and_file_names.py",
        PRIVTRACE_DIR / "config" / "parameter_setter.py",
        PRIVTRACE_DIR / "config" / "parameter_carrier.py",
        PRIVTRACE_DIR / "tools" / "data_reader.py",
        PRIVTRACE_INPUT,
    ]

    missing = [p for p in required_paths if not p.exists()]

    if missing:
        missing_text = "\n".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing required PrivTrace files/folders:\n{missing_text}"
        )

    python_path = Path(PRIVTRACE_PYTHON)
    if not python_path.exists():
        raise FileNotFoundError(
            f"PrivTrace Python executable not found:\n{python_path}"
        )

def run_adatrace_pipeline():
    prepare_adatrace_dataset()
    compile_adatrace()

    for epsilon in ADATRACE_EPSILONS:
        run_adatrace(epsilon)


def epsilon_label(epsilon):
    return f"eps_{epsilon}"


def run_privtrace():
    """
    Runs PrivTrace once per epsilon.

    Each epsilon is a separate Python process.
    """
    validate_privtrace_paths()

    epsilon_partition = ",".join(str(v) for v in PRIVTRACE_EPSILON_PARTITION)
    total_runs = len(PRIVTRACE_EPSILONS)

    print("\nPrivTrace epsilon list:", PRIVTRACE_EPSILONS, flush=True)

    for run_index, epsilon in enumerate(PRIVTRACE_EPSILONS, start=1):
        eps_label = f"eps_{epsilon}"

        output_file = (
            PRIVTRACE_OUTPUT_ROOT
            / eps_label
            / f"privtrace_{eps_label}.dat"
        )

        command = [
            PRIVTRACE_PYTHON,
            "-u",  # unbuffered output
            str(PRIVTRACE_MAIN),

            "--dataset_file_name",
            str(PRIVTRACE_INPUT),

            "--result_file_name",
            str(output_file),

            "--total_epsilon",
            str(epsilon),

            "--epsilon_partition",
            epsilon_partition,

            "--trajectory_number_to_generate",
            str(PRIVTRACE_TRAJECTORY_COUNT),
        ]

        start_time = time.time()
        start_datetime = datetime.datetime.now()

        print("\n" + "=" * 100, flush=True)
        print(f"STARTING PrivTrace run {run_index}/{total_runs}", flush=True)
        print(f"Started at: {start_datetime}", flush=True)
        print(f"Epsilon: {epsilon}", flush=True)
        print(f"Input: {PRIVTRACE_INPUT}", flush=True)
        print(f"Output: {output_file}", flush=True)
        print("Command:", flush=True)
        print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in command), flush=True)
        print("=" * 100 + "\n", flush=True)

        run_command(command, cwd=PRIVTRACE_DIR)

        elapsed = time.time() - start_time
        end_datetime = datetime.datetime.now()

        print("\n" + "=" * 100, flush=True)
        print(f"FINISHED PrivTrace run {run_index}/{total_runs}", flush=True)
        print(f"Epsilon: {epsilon}", flush=True)
        print(f"Finished at: {end_datetime}", flush=True)
        print(f"Elapsed seconds: {elapsed:.2f}", flush=True)
        print(f"Output exists: {output_file.exists()}", flush=True)
        print(f"Output: {output_file}", flush=True)
        print("=" * 100 + "\n", flush=True)


def validate_dpstts_paths():
    required_paths = [
        DP_STTS_DIR,
        DP_STTS_PREPARE_SCRIPT,
        DP_STTS_TPM_SCRIPT,
        DP_STTS_INPUT,
    ]

    missing = [p for p in required_paths if not p.exists()]

    if missing:
        missing_text = "\n".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing required DP-STTS files/folders:\n{missing_text}"
        )

def format_epsilon_list(epsilons):
    return ",".join(str(eps) for eps in epsilons)

def prepare_dpstts_dataset():
    validate_dpstts_paths()

    command = [
        str(DP_STTS_PYTHON),
        str(DP_STTS_PREPARE_SCRIPT),

        "--input",
        str(DP_STTS_INPUT),

        "--dpstts-dir",
        str(DP_STTS_DIR),

        "--output-root",
        str(DP_STTS_OUTPUT_ROOT),

        "--epsilons",
        format_epsilon_list(DP_STTS_EPSILONS),

        "--cell-h",
        str(DP_STTS_CELL_H),

        "--cell-w",
        str(DP_STTS_CELL_W),

        "--time-step",
        str(DP_STTS_TIME_STEP),

        "--full-day-time",
    ]

    print("\nPreparing DP-STTS dataset...")
    print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in command))
    print()

    subprocess.run(
        command,
        cwd=ROOT_DIR,
        check=True,
    )

    print("\nDP-STTS dataset prepared.")

def run_dpstts():
    validate_dpstts_paths()

    command = [
        str(DP_STTS_PYTHON),
        str(DP_STTS_TPM_SCRIPT),

        "--dataset",
        DP_STTS_DATASET,

        "--epsilons",
        format_epsilon_list(DP_STTS_EPSILONS),

        "--iterations",
        str(DP_STTS_ITERATIONS),

        "--epsilon-prefix-ratio",
        str(DP_STTS_EPSILON_PREFIX_RATIO),

        "--output-root",
        str(DP_STTS_OUTPUT_ROOT),
    ]

    if DP_STTS_RANDOM_SEED is not None:
        command.extend([
            "--random-seed",
            str(DP_STTS_RANDOM_SEED),
        ])

    print("\nRunning DP-STTS...")
    print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in command))
    print()

    subprocess.run(
        command,
        cwd=DP_STTS_DIR,
        check=True,
    )

    print("\nDP-STTS finished.")

def run_dpstts_pipeline():
    prepare_dpstts_dataset()
    run_dpstts()

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


def validate_privacy_attack_paths():
    required_paths = [
        PRIVACY_ATTACK_SCRIPT,
    ]

    missing = [p for p in required_paths if not p.exists()]

    if missing:
        missing_text = "\n".join(str(p) for p in missing)
        raise FileNotFoundError(
            f"Missing required privacy attack files:\n{missing_text}"
        )


def run_privacy_attack_for_file(
    model_name: str,
    original_path: Path,
    synthetic_path: Path,
    epsilon: str,
    input_coordinates: str,
    coordinate_order: str = "lonlat",
):
    validate_privacy_attack_paths()

    iteration_label = extract_iteration_label(synthetic_path)

    if not original_path.exists():
        raise FileNotFoundError(f"Original file does not exist: {original_path}")

    if not synthetic_path.exists():
        raise FileNotFoundError(f"Synthetic file does not exist: {synthetic_path}")

    for attack_arg, output_folder_name in PRIVACY_ATTACKS.items():
        output_path = (
                PRIVACY_OUTPUT_ROOT
                / model_name
                / f"eps_{epsilon}"
                / iteration_label
        )
        output_path.mkdir(parents=True, exist_ok=True)

        command = [
            str(PRIVACY_ATTACK_PYTHON),
            str(PRIVACY_ATTACK_SCRIPT),

            "--orig-path",
            str(original_path),

            "--synth-path",
            str(synthetic_path),

            "--output-path",
            str(output_path),

            "--dataset-name",
            PRIVACY_DATASET_NAME,

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
            str(PRIVACY_GRID_SIZE),

            "--time-period-hours",
            str(PRIVACY_TIME_PERIOD_HOURS),

            "--interval-minutes",
            str(PRIVACY_INTERVAL_MINUTES),

            "--known-locations",
            str(PRIVACY_KNOWN_LOCATIONS),

            "--test-users",
            str(PRIVACY_TEST_USERS),

            "--random-state",
            str(PRIVACY_RANDOM_STATE),

            "--n-clusters",
            str(PRIVACY_N_CLUSTERS),

            "--vartheta",
            str(PRIVACY_VARTHETA),

            "--sensitive-n",
            str(PRIVACY_SENSITIVE_N),

            "--sniff-n",
            str(PRIVACY_SNIFF_N),

            "--intersection-threshold",
            str(PRIVACY_INTERSECTION_THRESHOLD),

            "--top-k-neighbors",
            str(PRIVACY_TOP_K_NEIGHBORS),

            "--n-outliers",
            str(PRIVACY_N_OUTLIERS),

            "--closest-threshold",
            str(PRIVACY_CLOSEST_THRESHOLD),

            "--plausible-deniability-kappa",
            str(PRIVACY_PLAUSIBLE_DENIABILITY_KAPPA),

            "--plausible-deniability-beta",
            str(PRIVACY_PLAUSIBLE_DENIABILITY_BETA),
        ]

        print("\nRunning privacy attack...")
        print(f"Attack: {attack_arg}")
        print(f"Model: {model_name}")
        print(f"Epsilon: {epsilon}")
        print(f"Original: {original_path}")
        print(f"Synthetic: {synthetic_path}")
        print(f"Output: {output_path}")
        print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in command))
        print()

        subprocess.run(
            command,
            cwd=ROOT_DIR,
            check=True,
        )

    print("\nPrivacy attacks finished.")

def run_privacy_attacks_for_dpstts():
    synthetic_root = ROOT_DIR / "input" / "dpstts_synthetic"

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            model_name="dp_stts",
            original_path=DP_STTS_INPUT,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="latlon",
            coordinate_order="lonlat",
        )

def run_privacy_attacks_for_adatrace():
    synthetic_root = ROOT_DIR / "input" / "adatrace_synthetic"

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            model_name="adatrace",
            original_path=ADATRACE_INPUT_XY,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="xy",
        )

def run_privacy_attacks_for_dpstar():
    synthetic_root = ROOT_DIR / "input" / "dpstar_synthetic"

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            model_name="dp_star",
            original_path=DP_STAR_CLEAN_INPUT,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="latlon",
            coordinate_order="lonlat",
        )

def run_privacy_attacks_for_privtrace():
    synthetic_root = ROOT_DIR / "input" / "privtrace_synthetic"

    for epsilon, synthetic_file in find_synthetic_files_for_model(synthetic_root):
        run_privacy_attack_for_file(
            model_name="privtrace",
            original_path=PRIVTRACE_INPUT,
            synthetic_path=synthetic_file,
            epsilon=epsilon,
            input_coordinates="latlon",
            coordinate_order="lonlat",
        )

def main():
    try:
        # AdaTrace
        #run_adatrace_pipeline()

        #run_privacy_attacks_for_adatrace()

        # DP-Star
        # prepare_dpstar_dataset()
        # run_dp_star()
        # collect_dpstar_outputs()
        run_privacy_attacks_for_dpstar()

        # PrivTrace
        #run_privtrace()
        run_privacy_attacks_for_privtrace()

        # DP_STTS
        #run_dpstts_pipeline()
        run_privacy_attacks_for_dpstts()

    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()