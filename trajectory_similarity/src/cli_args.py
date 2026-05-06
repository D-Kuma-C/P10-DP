import argparse


def parse_args():
    """
    Parse command-line arguments for the trajectory similarity experiment.

    This module keeps all CLI configuration separate from main.py so the main
    script only handles pipeline orchestration.
    """
    parser = argparse.ArgumentParser(
        description="Run road-network trajectory similarity distribution experiments."
    )

    # Path to the original/private/reference trajectory file.
    # Expected format: .dat file containing trajectories as lon,lat,time sequences.
    parser.add_argument(
        "--original",
        required=True,
        help="Path to the original trajectory .dat file."
    )

    # Path to one synthetic trajectory file for one epsilon/privacy-budget value.
    # The project is designed to process one synthetic file at a time.
    parser.add_argument(
        "--synthetic",
        required=True,
        help="Path to the synthetic trajectory .dat file for one epsilon value."
    )

    # Privacy budget used to generate the synthetic trajectories.
    # This becomes part of the output filename as epi_<epsilon>.
    # Example: --epsilon 1.0 -> epi_1.0
    parser.add_argument(
        "--epsilon",
        required=True,
        help="Privacy budget value for the synthetic file, for example 0.1, 0.5, or 1.0."
    )

    # Name of the DP/synthetic trajectory generation model.
    # This becomes part of the output filename.
    # Example: adatrace_20k_tdrive_epi_1.0.distribution.csv
    parser.add_argument(
        "--dp-model",
        required=True,
        help="Name of the DP model, for example adatrace, privtrace, or dpstar."
    )

    # User-facing trajectory-count label.
    # This is intentionally a label rather than calculated automatically, because
    # experiments often use names like 20k, 50k, 100k, sample_5k, etc.
    parser.add_argument(
        "--trajectory-count-label",
        required=True,
        help="Trajectory-count label to include in output filenames, for example 20k."
    )

    # Dataset name used in the experiment.
    # This becomes part of the output filename.
    # Examples: tdrive, geolife, porto.
    parser.add_argument(
        "--dataset-name",
        required=True,
        help="Dataset name to include in output filenames, for example tdrive, geolife, or porto."
    )

    # Road-network construction mode.
    # osmnx: build road network and segment IDs from lon/lat trajectory points.
    # prebuilt: load existing nodes.csv, edges.csv, and trajectory_segments.csv.
    parser.add_argument(
        "--network-mode",
        choices=["osmnx", "prebuilt"],
        required=True,
        help="Road-network mode: 'osmnx' to build from OSMnx, or 'prebuilt' to load existing files."
    )

    # City/place name for OSMnx graph download.
    # Required only when --network-mode osmnx.
    # Example: --place "Porto, Portugal"
    parser.add_argument(
        "--place",
        default=None,
        help="Place name for OSMnx road-network download. Required for --network-mode osmnx."
    )

    # Path to prebuilt nodes.csv.
    # Required only when --network-mode prebuilt.
    # Expected columns: node_id, lon, lat.
    parser.add_argument(
        "--nodes",
        default=None,
        help="Path to prebuilt nodes.csv. Required for --network-mode prebuilt."
    )

    # Path to prebuilt edges.csv.
    # Required only when --network-mode prebuilt.
    # Expected columns: edge_id, start_node, end_node, length.
    parser.add_argument(
        "--edges",
        default=None,
        help="Path to prebuilt edges.csv. Required for --network-mode prebuilt."
    )

    # Path to prebuilt trajectory segment sequences.
    # Required only when --network-mode prebuilt.
    # Expected columns: dataset, traj_id, order, segment_id.
    parser.add_argument(
        "--segments",
        default=None,
        help="Path to prebuilt trajectory_segments.csv. Required for --network-mode prebuilt."
    )

    # Root output directory.
    # Measure-specific folders are created directly inside this directory.
    # Example: data/output/NetEDR/adatrace_20k_tdrive_epi_1.0.distribution.csv
    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Root output directory for measure folders and summaries. Default: data/output."
    )

    # Directory where generated network files are saved when using OSMnx mode.
    # Files written here include nodes.csv, edges.csv, and trajectory_segments.csv.
    parser.add_argument(
        "--network-output-dir",
        default="data/network",
        help="Directory for generated network files in OSMnx mode. Default: data/network."
    )

    # Maximum number of trajectory pairs sampled for each comparison type.
    # Prevents all-vs-all comparisons from exploding for large datasets.
    # Applies separately to original-vs-original, original-vs-synthetic,
    # synthetic-vs-synthetic, and each stratified group.
    parser.add_argument(
        "--max-pairs",
        type=int,
        default=10000,
        help="Maximum number of sampled trajectory pairs per comparison. Default: 10000."
    )

    # Random seed for reproducible pair sampling.
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducible pair sampling. Default: 42."
    )

    # NetEDR match threshold in meters.
    # If road-network distance between two points is <= threshold,
    # substitution cost is 0; otherwise substitution cost is 1.
    parser.add_argument(
        "--netedr-threshold",
        type=float,
        default=1000.0,
        help="NetEDR match threshold in meters. Default: 1000.0."
    )

    # NetERP gap cost.
    # The original Java code used a hard-coded gap point. This Python version
    # uses a configurable constant gap penalty to avoid dataset-specific hidden nodes.
    parser.add_argument(
        "--neterp-gap-cost",
        type=float,
        default=1.0,
        help="NetERP constant gap cost. Default: 1.0."
    )

    return parser.parse_args()