from tqdm import tqdm

from cli_args import parse_args
from parser import load_dat_trajectories
from network_modes import build_network_with_osmnx, load_prebuilt_network
from experiment import DistributionExperiment

from measures.netedr import NetEDR
from measures.neterp import NetERP
from measures.tp import TP
from measures.lors import LORS


if __name__ == "__main__":
    args = parse_args()

    stages = tqdm(total=5, desc="Pipeline stages")

    original = load_dat_trajectories(args.original, dataset="original")
    synthetic = load_dat_trajectories(args.synthetic, dataset="synthetic")
    stages.update(1)

    all_trajectories = original + synthetic

    if args.network_mode == "osmnx":
        if args.place is None:
            raise ValueError("--place is required when --network-mode osmnx")

        roadmap, all_trajectories = build_network_with_osmnx(
            trajectories=all_trajectories,
            place=args.place,
            output_dir=args.network_output_dir,
        )

    else:
        if args.nodes is None or args.edges is None or args.segments is None:
            raise ValueError(
                "--nodes, --edges, and --segments are required when --network-mode prebuilt"
            )

        roadmap, all_trajectories = load_prebuilt_network(
            trajectories=all_trajectories,
            nodes_file=args.nodes,
            edges_file=args.edges,
            segments_file=args.segments,
        )

    print("Original trajectories:", len(original))
    print("Synthetic trajectories:", len(synthetic))

    print("Original avg points:", sum(len(t.points) for t in original) / max(len(original), 1))
    print("Synthetic avg points:", sum(len(t.points) for t in synthetic) / max(len(synthetic), 1))

    print("Original max points:", max((len(t.points) for t in original), default=0))
    print("Synthetic max points:", max((len(t.points) for t in synthetic), default=0))

    stages.update(1)

    original = [t for t in all_trajectories if t.dataset == "original"]
    synthetic = [t for t in all_trajectories if t.dataset == "synthetic"]

    #roadmap.precompute_distances_for_trajectories(original + synthetic)


    def print_point_stats(name, trajectories):
        counts = [len(t.points) for t in trajectories]
        seg_counts = [len(t.segment_ids) for t in trajectories]

        if not counts:
            print(f"{name}: no trajectories")
            return

        print(f"{name} trajectories: {len(trajectories)}")
        print(f"{name} point count min/avg/max: {min(counts)} / {sum(counts) / len(counts):.2f} / {max(counts)}")
        print(
            f"{name} segment count min/avg/max: {min(seg_counts)} / {sum(seg_counts) / len(seg_counts):.2f} / {max(seg_counts)}")


    print_point_stats("Original", original)
    print_point_stats("Synthetic", synthetic)

    dp_model_normalized = args.dp_model.lower().replace("-", "_")

    measures = {
        "NetEDR": NetEDR(match_threshold=args.netedr_threshold),
        "NetERP": NetERP(gap_cost=args.neterp_gap_cost),
        "LORS": LORS(),
    }

    if dp_model_normalized == "dpstts":
        measures["TP"] = TP()
    else:
        print(f"Skipping TP for {args.dp_model}, because synthetic trajectories do not contain reliable timestamps.")

    stages.update(1)

    experiment = DistributionExperiment(
        original_trajectories=original,
        synthetic_trajectories=synthetic,
        epsilon=args.epsilon,
        dp_model=args.dp_model,
        trajectory_count_label=args.trajectory_count_label,
        dataset_name=args.dataset_name,
        measures=measures,
        roadmap=roadmap,
        output_dir=args.output_dir,
        max_pairs_per_comparison=args.max_pairs,
        random_seed=args.random_seed,
    )

    stages.update(1)

    experiment.run_distribution_comparisons()
    experiment.run_stratified_original_synthetic()

    stages.update(1)
    stages.close()