import os
import pandas as pd

from Attack_model.reidentification_probability import reidentification_prob
from ConvertToFrames import convert_dat_to_dataframe
from Attack_model.bayesian_attack import bayesian_attack_score_only
from geometry import Grid
from Parsing import parse_dat_trajectories, parse_dat_for_bayesian
from Attack_model.partial_sniffing import partial_sniffing_score_only
from Attack_model.outlier_leakage import outlier_leakage_score_only

from cli_args import parse_args, should_run, validate_args

def safe_epsilon_name(epsilon: float) -> str:
    """
    Converts epsilon to filename-safe format.
    Example:
        1.0 -> epi_1.0
        0.5 -> epi_0.5
    """
    return f"epi_{epsilon}"


def get_attack_output_dir(args, attack_name: str) -> str:
    """
    Creates and returns output directory for a given attack.
    Example:
        data/output/bayesian/
    """
    attack_dir = os.path.join(args.output_path, attack_name)
    os.makedirs(attack_dir, exist_ok=True)
    return attack_dir


def get_result_filename(args, attack_name: str) -> str:
    """
    Builds a CSV filename containing dataset, model, and epsilon.
    Example:
        brinkhoff_adatrace_epi_1.0_bayesian.csv
    """
    epsilon_name = safe_epsilon_name(args.epsilon)

    filename = (
        f"{args.dataset_name}_"
        f"{args.model_name}_"
        f"{epsilon_name}_"
        f"{attack_name}.csv"
    )

    return filename


def save_attack_csv(args, attack_name: str, rows):
    """
    Saves attack results as a CSV file.

    rows can be:
        - a dictionary for one-row CSV
        - a list of dictionaries for multi-row CSV
    """
    attack_dir = get_attack_output_dir(args, attack_name)
    filename = get_result_filename(args, attack_name)
    output_file = os.path.join(attack_dir, filename)

    if isinstance(rows, dict):
        rows = [rows]

    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)

    print(f"Saved {attack_name} results to: {output_file}")

def load_xy_trajectories(args):
    """
    Loads original and synthetic trajectories as x,y coordinates.

    If the input data is lat/lon, both datasets are converted to local meters.
    The synthetic dataset uses the same projection origin as the original dataset.
    """

    if args.input_coordinates == "xy":
        orig_xy = parse_dat_trajectories(
            args.orig_path,
            input_coordinates="xy",
        )

        syn_xy = parse_dat_trajectories(
            args.synth_path,
            input_coordinates="xy",
        )

        projection_info = None

    else:
        orig_xy, projection_info = parse_dat_trajectories(
            args.orig_path,
            input_coordinates="latlon",
            coordinate_order=args.coordinate_order,
        )

        syn_xy, _ = parse_dat_trajectories(
            args.synth_path,
            input_coordinates="latlon",
            coordinate_order=args.coordinate_order,
            origin_lon=projection_info["origin_lon"],
            origin_lat=projection_info["origin_lat"],
        )

    return orig_xy, syn_xy, projection_info


def run_reidentification(args):
    print("############ Reidentification BEGIN ############")

    if args.input_coordinates == "xy":
        orig = convert_dat_to_dataframe(
            args.orig_path,
            input_coordinates="xy",
            time_period_hours=args.time_period_hours,
            interval_minutes=args.interval_minutes,
            n_clusters=args.n_clusters,
            random_state=args.random_state,
        )

        synth = convert_dat_to_dataframe(
            args.synth_path,
            input_coordinates="xy",
            time_period_hours=args.time_period_hours,
            interval_minutes=args.interval_minutes,
            n_clusters=args.n_clusters,
            random_state=args.random_state,
        )

    else:
        orig, projection_info = convert_dat_to_dataframe(
            args.orig_path,
            input_coordinates="latlon",
            coordinate_order=args.coordinate_order,
            time_period_hours=args.time_period_hours,
            interval_minutes=args.interval_minutes,
            n_clusters=args.n_clusters,
            random_state=args.random_state,
            return_projection_info=True,
        )

        synth = convert_dat_to_dataframe(
            args.synth_path,
            input_coordinates="latlon",
            coordinate_order=args.coordinate_order,
            origin_lon=projection_info["origin_lon"],
            origin_lat=projection_info["origin_lat"],
            time_period_hours=args.time_period_hours,
            interval_minutes=args.interval_minutes,
            n_clusters=args.n_clusters,
            random_state=args.random_state,
        )

    score = reidentification_prob(
        synthetic_data=synth,
        original_data=orig,
        known_locations=args.known_locations,
        number_of_test_users=args.test_users,
        random_state=args.random_state,
        show_progress=args.reid_show_progress,
    )

    print(f"Re-identification probability score: {score:.4f}")
    save_attack_csv(
        args=args,
        attack_name="reidentification",
        rows={
            "dataset": args.dataset_name,
            "model": args.model_name,
            "epsilon": args.epsilon,
            "input_coordinates": args.input_coordinates,
            "coordinate_order": args.coordinate_order,
            "time_period_hours": args.time_period_hours,
            "interval_minutes": args.interval_minutes,
            "known_locations": args.known_locations,
            "test_users": args.test_users,
            "random_state": args.random_state,
            "n_clusters": args.n_clusters,
            "reidentification_probability": score,
        },
    )
    print("############ Reidentification END ############")


def run_bayesian(args):
    print("############ Bayesian Attack BEGIN ############")

    orig_trajs, syn_trajs, grid_cells, grid_info, projection_info = parse_dat_for_bayesian(
        original_path=args.orig_path,
        synthetic_path=args.synth_path,
        x_bins=args.grid_size,
        y_bins=args.grid_size,
        input_coordinates=args.input_coordinates,
        coordinate_order=args.coordinate_order,
        remove_consecutive_duplicates=args.remove_consecutive_duplicates,
    )

    result = bayesian_attack_score_only(
        orig_trajs=orig_trajs,
        syn_trajs=syn_trajs,
        grid_cells=grid_cells,
        vartheta=args.vartheta,
        nth_densest_cell=args.sensitive_n,
    )

    print("Sensitive zone:", result["sensitive_zone"])
    print("Relevant synthetic trajectories:", result["relevant_subset_size"])

    if result["trip_jsd"] is None:
        print("Trip JSD: None")
    else:
        print(f"Trip JSD: {result['trip_jsd']:.3f}")

    if result["markov_jsd"] is None:
        print("Markov JSD: None")
    else:
        print(f"Markov JSD: {result['markov_jsd']:.3f}")

    print("Passes Bayesian defense:", result["passes"])

    bayesian_risk = None

    if result["trip_jsd"] is not None and result["markov_jsd"] is not None:
        bayesian_risk = (result["trip_jsd"] + result["markov_jsd"]) / 2.0

    save_attack_csv(
        args=args,
        attack_name="bayesian",
        rows={
            "dataset": args.dataset_name,
            "model": args.model_name,
            "epsilon": args.epsilon,
            "input_coordinates": args.input_coordinates,
            "coordinate_order": args.coordinate_order,
            "grid_size": args.grid_size,
            "vartheta": args.vartheta,
            "sensitive_n": args.sensitive_n,
            "sensitive_zone": result["sensitive_zone"],
            "relevant_subset_size": result["relevant_subset_size"],
            "trip_jsd": result["trip_jsd"],
            "markov_jsd": result["markov_jsd"],
            "bayesian_risk": bayesian_risk,
            "trip_passes": result.get("trip_passes"),
            "markov_passes": result.get("markov_passes"),
            "passes": result["passes"],
        },
    )
    print("############ Bayesian Attack END ############")


def run_partial_sniffing(args):
    print("############ Partial Sniffing BEGIN ############")

    orig_xy, syn_xy, projection_info = load_xy_trajectories(args)

    grid = Grid(
        cell_count=args.grid_size,
        min_x=args.grid_min_x,
        max_x=args.grid_max_x,
        min_y=args.grid_min_y,
        max_y=args.grid_max_y,
    )

    result = partial_sniffing_score_only(
        orig_xy=orig_xy,
        syn_xy=syn_xy,
        grid=grid,
        sniff_n=args.sniff_n,
        sensitive_n=args.sensitive_n,
        intersection_threshold=args.intersection_threshold,
    )

    print("Sniff region:", result["sniff_region"])
    print("Sensitive zone:", result["sensitive_zone"])
    print("Sniffed original trajectories:", result["sniffed_original_count"])
    print("Matched trajectories:", result["matched_count"])
    print("No match count:", result["no_match_count"])
    print("Failing synthetic trajectories unique:", result["failing_synthetic_count_unique"])
    print("Failures by intersection:", result["failures_by_intersection"])
    print("Failures by sensitive zone:", result["failures_by_sensitive_zone"])
    print("Failing synthetic indices:", result["failing_synthetic_indices_unique"])

    total_synthetic = len(syn_xy)

    partial_risk = (
        result["failing_synthetic_count_unique"] / total_synthetic
        if total_synthetic > 0
        else None
    )

    save_attack_csv(
        args=args,
        attack_name="partial_sniffing",
        rows={
            "dataset": args.dataset_name,
            "model": args.model_name,
            "epsilon": args.epsilon,
            "input_coordinates": args.input_coordinates,
            "coordinate_order": args.coordinate_order,
            "grid_size": args.grid_size,
            "grid_min_x": args.grid_min_x,
            "grid_max_x": args.grid_max_x,
            "grid_min_y": args.grid_min_y,
            "grid_max_y": args.grid_max_y,
            "sniff_n": args.sniff_n,
            "sensitive_n": args.sensitive_n,
            "intersection_threshold": args.intersection_threshold,
            "sniff_region": result["sniff_region"],
            "sensitive_zone": result["sensitive_zone"],
            "total_synthetic_trajectories": total_synthetic,
            "sniffed_original_count": result["sniffed_original_count"],
            "matched_count": result["matched_count"],
            "no_match_count": result["no_match_count"],
            "failing_event_count": result["failing_event_count"],
            "failing_synthetic_count_unique": result["failing_synthetic_count_unique"],
            "failures_by_intersection": result["failures_by_intersection"],
            "failures_by_sensitive_zone": result["failures_by_sensitive_zone"],
            "partial_sniffing_risk": partial_risk,
            "failing_synthetic_indices_unique": ";".join(
                map(str, result["failing_synthetic_indices_unique"])
            ),
        },
    )

    print("############ Partial Sniffing END ############")


def run_outlier_leakage(args):
    print("############ Outlier Leakage BEGIN ############")

    orig_xy, syn_xy, projection_info = load_xy_trajectories(args)

    result = outlier_leakage_score_only(
        orig_xy=orig_xy,
        syn_xy=syn_xy,
        top_k_neighbors=args.top_k_neighbors,
        n_outliers=args.n_outliers,
        closest_threshold=args.closest_threshold,
        plausible_deniability_kappa=args.plausible_deniability_kappa,
        plausible_deniability_beta=args.plausible_deniability_beta,
        exact_adatrace=args.exact_adatrace,
        plausible_deniability_sample_size=args.plausible_deniability_sample_size,
        random_state=args.random_state,
        mutate_like_java_between_stages=args.mutate_like_java_between_stages,
        show_progress_inner=args.outlier_show_progress_inner,
    )

    print("Original synthetic count:", result["original_synthetic_count"])
    print("Final count if removals were applied:", result["final_working_synthetic_count_if_removed"])
    print("Estimated removed count:", result["estimated_removed_count_if_removed"])
    print("Total failed events:", result["total_failed_events"])

    for stage in result["stages"]:
        print()
        print("Stage:", stage["stage"])
        print("  Outliers raw:", stage["outlier_count_raw"])
        print("  Outliers unique:", stage["outlier_count_unique"])
        print("  Failed raw:", stage["failed_count_raw"])
        print("  Failed unique:", stage["failed_count_unique"])
        print(
            "  Failed indices:",
            stage["failed_indices_unique"][:20],
            "..." if len(stage["failed_indices_unique"]) > 20 else "",
        )

    rows = []

    for stage in result["stages"]:
        outlier_risk_stage = (
            stage["failed_count_unique"] / result["original_synthetic_count"]
            if result["original_synthetic_count"] > 0
            else None
        )

        rows.append(
            {
                "dataset": args.dataset_name,
                "model": args.model_name,
                "epsilon": args.epsilon,
                "input_coordinates": args.input_coordinates,
                "coordinate_order": args.coordinate_order,
                "stage": stage["stage"],
                "top_k_neighbors": args.top_k_neighbors,
                "n_outliers": args.n_outliers,
                "closest_threshold": args.closest_threshold,
                "plausible_deniability_kappa": args.plausible_deniability_kappa,
                "plausible_deniability_beta": args.plausible_deniability_beta,
                "exact_adatrace": args.exact_adatrace,
                "mutate_like_java_between_stages": args.mutate_like_java_between_stages,
                "original_synthetic_count": result["original_synthetic_count"],
                "final_working_synthetic_count_if_removed": result[
                    "final_working_synthetic_count_if_removed"
                ],
                "estimated_removed_count": result["estimated_removed_count_if_removed"],
                "total_failed_events": result["total_failed_events"],
                "outlier_count_raw": stage["outlier_count_raw"],
                "outlier_count_unique": stage["outlier_count_unique"],
                "failed_count_raw": stage["failed_count_raw"],
                "failed_count_unique": stage["failed_count_unique"],
                "outlier_stage_risk": outlier_risk_stage,
                "failed_indices_unique": ";".join(
                    map(str, stage["failed_indices_unique"])
                ),
            }
        )

    overall_outlier_risk = (
        result["estimated_removed_count_if_removed"] / result["original_synthetic_count"]
        if result["original_synthetic_count"] > 0
        else None
    )

    rows.append(
        {
            "dataset": args.dataset_name,
            "model": args.model_name,
            "epsilon": args.epsilon,
            "input_coordinates": args.input_coordinates,
            "coordinate_order": args.coordinate_order,
            "stage": "overall",
            "top_k_neighbors": args.top_k_neighbors,
            "n_outliers": args.n_outliers,
            "closest_threshold": args.closest_threshold,
            "plausible_deniability_kappa": args.plausible_deniability_kappa,
            "plausible_deniability_beta": args.plausible_deniability_beta,
            "exact_adatrace": args.exact_adatrace,
            "mutate_like_java_between_stages": args.mutate_like_java_between_stages,
            "original_synthetic_count": result["original_synthetic_count"],
            "final_working_synthetic_count_if_removed": result[
                "final_working_synthetic_count_if_removed"
            ],
            "estimated_removed_count": result["estimated_removed_count_if_removed"],
            "total_failed_events": result["total_failed_events"],
            "outlier_count_raw": None,
            "outlier_count_unique": None,
            "failed_count_raw": result["total_failed_events"],
            "failed_count_unique": result["estimated_removed_count_if_removed"],
            "outlier_stage_risk": overall_outlier_risk,
            "failed_indices_unique": None,
        }
    )

    save_attack_csv(
        args=args,
        attack_name="outlier_leakage",
        rows=rows,
    )

    print("############ Outlier Leakage END ############")


def main():
    args = parse_args()
    validate_args(args)

    os.makedirs(args.output_path, exist_ok=True)

    if should_run(args, "reid"):
        run_reidentification(args)

    if should_run(args, "bayesian"):
        run_bayesian(args)

    if should_run(args, "partial"):
        run_partial_sniffing(args)

    if should_run(args, "outlier"):
        run_outlier_leakage(args)


if __name__ == "__main__":
    main()