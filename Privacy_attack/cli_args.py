import argparse


# AdaTrace default values from the Java attack code:
ADATRACE_VARTHETA = 0.1
ADATRACE_SENSITIVE_N = 10
ADATRACE_SNIFF_N = 12
ADATRACE_INTERSECTION_THRESHOLD = 5

ADATRACE_TOP_K_NEIGHBORS = 50
ADATRACE_N_OUTLIERS = 200
ADATRACE_CLOSEST_THRESHOLD = 0.1
ADATRACE_PLAUSIBLE_DENIABILITY_KAPPA = 100
ADATRACE_PLAUSIBLE_DENIABILITY_BETA = 0.05


VALID_ATTACKS = ["reid", "bayesian", "partial", "outlier", "all"]


def parse_args():
    """
    Parses command-line arguments for the privacy attack evaluation.

    Default behavior:
        - Runs all attacks.
        - Uses AdaTrace attack parameters where applicable.
        - Uses x,y input coordinates.
        - Uses 20x20 grid.
        - Uses 24 hours with 15-minute intervals for re-identification.
    """

    parser = argparse.ArgumentParser(
        description="Run privacy attacks on original and synthetic trajectory datasets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ============================================================
    # Dataset parameters
    # ============================================================

    parser.add_argument(
        "--orig-path",
        default="data/orig/brinkhoff.dat",
        help="Path to the original trajectory dataset.",
    )

    parser.add_argument(
        "--synth-path",
        default="data/synth/brinkhoff.dat-eps1.0-iteration1.dat",
        help="Path to the synthetic trajectory dataset.",
    )

    parser.add_argument(
        "--output-path",
        default="data/output/",
        help=(
            "Directory where result files should be saved. "
            "Default is data/output/."
        ),
    )

    parser.add_argument(
        "--dataset-name",
        choices=["tdrive", "geolife", "porto", "brinkhoff"],
        default="brinkhoff",
        help="Dataset name used in output CSV filenames.",
    )

    parser.add_argument(
        "--model-name",
        choices=["adatrace", "privtrace", "dp_star", "dp_stts"],
        default="adatrace",
        help="DP model name used in output CSV filenames.",
    )

    parser.add_argument(
        "--epsilon",
        type=float,
        default=1.0,
        help="Privacy budget epsilon used in output CSV filenames.",
    )

    parser.add_argument(
        "--input-coordinates",
        choices=["xy", "latlon"],
        default="xy",
        help=(
            "Coordinate format of the input file. "
            "'xy' means the file already contains projected x,y coordinates. "
            "'latlon' means the file contains latitude/longitude coordinates."
        ),
    )

    parser.add_argument(
        "--coordinate-order",
        choices=["lonlat", "latlon"],
        default="lonlat",
        help=(
            "Coordinate order when --input-coordinates latlon is used. "
            "'lonlat' means each pair is longitude,latitude. "
            "'latlon' means each pair is latitude,longitude."
        ),
    )

    parser.add_argument(
        "--attacks",
        nargs="+",
        choices=VALID_ATTACKS,
        default=["all"],
        help=(
            "Which privacy attacks to run. "
            "Use 'all' to run re-identification, Bayesian, partial sniffing, and outlier leakage."
        ),
    )

    # ============================================================
    # Grid parameters
    # ============================================================

    parser.add_argument(
        "--grid-size",
        type=int,
        default=20,
        help="Grid size N for an N x N grid.",
    )

    parser.add_argument(
        "--grid-min-x",
        type=float,
        default=0.0,
        help="Minimum x coordinate for the grid used in Partial Sniffing.",
    )

    parser.add_argument(
        "--grid-max-x",
        type=float,
        default=25000.0,
        help="Maximum x coordinate for the grid used in Partial Sniffing.",
    )

    parser.add_argument(
        "--grid-min-y",
        type=float,
        default=0.0,
        help="Minimum y coordinate for the grid used in Partial Sniffing.",
    )

    parser.add_argument(
        "--grid-max-y",
        type=float,
        default=25000.0,
        help="Maximum y coordinate for the grid used in Partial Sniffing.",
    )

    parser.add_argument(
        "--remove-consecutive-duplicates",
        action="store_true",
        default=False,
        help=(
            "Remove consecutive duplicate grid cells when converting trajectories "
            "to cell sequences for Bayesian attack."
        ),
    )

    # ============================================================
    # Re-identification parameters
    # ============================================================

    parser.add_argument(
        "--time-period-hours",
        type=float,
        default=24,
        help=(
            "Total time period represented by each trajectory for re-identification. "
            "For example, 24 means one full day."
        ),
    )

    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=15,
        help=(
            "Time interval used for re-identification binning. "
            "For example, 15 gives 96 bins for a 24-hour trajectory."
        ),
    )

    parser.add_argument(
        "--known-locations",
        type=int,
        default=3,
        help="Number of known locations/time bins assumed known by the attacker.",
    )

    parser.add_argument(
        "--test-users",
        type=int,
        default=3,
        help="Number of original users sampled for the re-identification attack.",
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=0,
        help="Random seed used for reproducible re-identification sampling.",
    )

    parser.add_argument(
        "--n-clusters",
        type=int,
        default=4,
        help="Number of KMeans spatial regions used for re-identification.",
    )

    parser.add_argument(
        "--reid-show-progress",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show progress bars for the re-identification attack.",
    )

    # ============================================================
    # Bayesian inference parameters
    # ============================================================

    parser.add_argument(
        "--vartheta",
        type=float,
        default=ADATRACE_VARTHETA,
        help="AdaTrace Bayesian inference threshold VARTHETA.",
    )

    parser.add_argument(
        "--sensitive-n",
        type=int,
        default=ADATRACE_SENSITIVE_N,
        help=(
            "Nth densest original grid cell used as the sensitive zone. "
            "AdaTrace default is 10."
        ),
    )

    # ============================================================
    # Partial sniffing parameters
    # ============================================================

    parser.add_argument(
        "--sniff-n",
        type=int,
        default=ADATRACE_SNIFF_N,
        help=(
            "Nth densest original grid cell used as the sniff region. "
            "AdaTrace default is 12."
        ),
    )

    parser.add_argument(
        "--intersection-threshold",
        type=int,
        default=ADATRACE_INTERSECTION_THRESHOLD,
        help=(
            "Minimum number of near-identical points needed to fail "
            "the Partial Sniffing intersection check."
        ),
    )

    # ============================================================
    # Outlier leakage parameters
    # ============================================================

    parser.add_argument(
        "--top-k-neighbors",
        type=int,
        default=ADATRACE_TOP_K_NEIGHBORS,
        help="Number of nearest neighbors used for kNN outlier scoring.",
    )

    parser.add_argument(
        "--n-outliers",
        type=int,
        default=ADATRACE_N_OUTLIERS,
        help="Number of outlier candidates considered in Outlier Leakage.",
    )

    parser.add_argument(
        "--closest-threshold",
        type=float,
        default=ADATRACE_CLOSEST_THRESHOLD,
        help="Closest-distance threshold used in Outlier Leakage.",
    )

    parser.add_argument(
        "--plausible-deniability-kappa",
        type=int,
        default=ADATRACE_PLAUSIBLE_DENIABILITY_KAPPA,
        help="Kappa parameter for Outlier Leakage plausible deniability.",
    )

    parser.add_argument(
        "--plausible-deniability-beta",
        type=float,
        default=ADATRACE_PLAUSIBLE_DENIABILITY_BETA,
        help="Beta parameter for Outlier Leakage plausible deniability.",
    )

    parser.add_argument(
        "--plausible-deniability-sample-size",
        type=int,
        default=1000,
        help=(
            "Number of original trajectories sampled for outlier plausible-deniability checks. "
            "Use 0 or negative to compare against all originals."
        ),
    )

    parser.add_argument(
        "--exact-adatrace",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Preserve AdaTrace behavior exactly in Outlier Leakage, including "
            "the quirks present in the Java implementation."
        ),
    )

    parser.add_argument(
        "--mutate-like-java-between-stages",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Simulate AdaTrace removals between Outlier Leakage stages. "
            "If disabled, all stages evaluate the original synthetic dataset."
        ),
    )

    parser.add_argument(
        "--outlier-show-progress-inner",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Show inner progress bars inside Outlier Leakage plausible-deniability checks. "
            "This is usually noisy, so the default is False."
        ),
    )

    return parser.parse_args()


def should_run(args, attack_name: str) -> bool:
    """
    Returns True if a given attack should run.
    """
    return "all" in args.attacks or attack_name in args.attacks


def validate_args(args):
    """
    Validates command-line argument combinations.
    """

    selected_attacks = set(args.attacks)

    if "all" in selected_attacks and len(selected_attacks) > 1:
        raise ValueError("Use either '--attacks all' or a list of specific attacks, not both.")

    if args.time_period_hours <= 0:
        raise ValueError("--time-period-hours must be positive.")

    if args.interval_minutes <= 0:
        raise ValueError("--interval-minutes must be positive.")

    total_minutes = args.time_period_hours * 60

    if total_minutes % args.interval_minutes != 0:
        raise ValueError(
            "--time-period-hours * 60 must be divisible by --interval-minutes."
        )

    if args.grid_size <= 0:
        raise ValueError("--grid-size must be positive.")

    if args.known_locations <= 0:
        raise ValueError("--known-locations must be positive.")

    if args.test_users <= 0:
        raise ValueError("--test-users must be positive.")

    if args.n_clusters <= 0:
        raise ValueError("--n-clusters must be positive.")

    if args.n_outliers <= 0:
        raise ValueError("--n-outliers must be positive.")

    if args.top_k_neighbors <= 0:
        raise ValueError("--top-k-neighbors must be positive.")