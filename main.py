from pathlib import Path
import subprocess
import sys
import shutil
import os
import datetime
import time


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
# AdaTrace parameters
# -----------------------------

ADATRACE_INPUT = ROOT_DIR / "input" / "cleandata" / "porto" / "porto_20k.dat"

ADATRACE_OUTPUT_DIR = ROOT_DIR / "input" / "adatrace_synthetic"

ADATRACE_EPSILON = 1.0

ADATRACE_ITERATIONS = 5

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
    / "porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630.dat"
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

DP_STTS_INPUT = ROOT_DIR / "input" / "cleandata" / "porto" / "porto_small_500.dat"

DP_STTS_OUTPUT_ROOT = ROOT_DIR / "input" / "dpstts_synthetic"

DP_STTS_EPSILONS = [0.1, 0.5, 1.0, 2.0]

DP_STTS_DATASET_NAME = "Porto"

DP_STTS_CELL_H = 6
DP_STTS_CELL_W = 6

DP_STTS_TIME_STEP = 15  # minutes

DP_STTS_ITERATIONS = 1

DP_STTS_EPSILON_PREFIX_RATIO = 0.5



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


def run_adatrace():
    main_class = BUILD_DIR / "Main.class"

    if not main_class.exists():
        raise FileNotFoundError(
            f"Main.class was not found:\n{main_class}"
        )

    ADATRACE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
        str(ADATRACE_OUTPUT_DIR),

        "--epsilon",
        str(ADATRACE_EPSILON),

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


def main():
    try:
        # AdaTrace
        # compile_adatrace()
        # run_adatrace()

        # DP-Star
        # prepare_dpstar_dataset()
        # run_dp_star()
        # collect_dpstar_outputs()

        # PrivTrace
        run_privtrace()

    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()