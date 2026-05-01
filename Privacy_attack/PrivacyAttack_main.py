import pandas as pd

from Attack_model.reidentification_probability import reidentification_prob
from ConvertToFrames import *
from Attack_model.bayesian_attack import bayesian_attack_score_only
from geometry import Grid
from Parsing import parse_dat_trajectories, parse_dat_for_bayesian
from Attack_model.partial_sniffing import partial_sniffing_score_only
from Attack_model.outlier_leakage import outlier_leakage_score_only

# ##########################################
# ############ Reidentification ############

print("############ Reidentification BEGIN ############")
# This is for lat, lon
# orig, projection_info = convert_dat_to_dataframe(
#     "data/orig/brinkhoff_latlon.dat",
#     input_coordinates="latlon",
#     coordinate_order="lonlat",
#     return_projection_info=True,
# )
#
# synth = convert_dat_to_dataframe(
#     "data/synth/brinkhoff_latlon.dat-eps1.0-iteration1.dat",
#     input_coordinates="latlon",
#     coordinate_order="lonlat",
#     origin_lon=projection_info["origin_lon"],
#     origin_lat=projection_info["origin_lat"],
# )

# This is for x, y
orig = convert_dat_to_dataframe(
    "data/orig/brinkhoff.dat",
    input_coordinates="xy",
    time_period_hours=24,
    interval_minutes=15,
)

synth = convert_dat_to_dataframe(
    "data/synth/brinkhoff.dat-eps1.0-iteration1.dat",
    input_coordinates="xy",
    time_period_hours=12,
    interval_minutes=15,
)

score = reidentification_prob(
    synthetic_data=synth,
    original_data=orig,
    known_locations=3,
    number_of_test_users=40,
    random_state=0,
    show_progress=True,
)

print(f"Re-identification probability score: {score:.4f}")
print("############ Reidentification END ############")

# ##########################################
# ############ Bayesian Attack #############

print("############ Bayesian Attack BEGIN ############")
# This is for x,y
orig_trajs, syn_trajs, grid_cells, grid_info, projection_info = parse_dat_for_bayesian(
    original_path="data/orig/brinkhoff.dat",
    synthetic_path="data/synth/brinkhoff.dat-eps1.0-iteration1.dat",
    x_bins=20,
    y_bins=20,
    input_coordinates="xy",
)

# This is for lat, lon
# orig_trajs, syn_trajs, grid_cells, grid_info, projection_info = parse_dat_for_bayesian(
#     original_path="data/orig/my_latlon.dat",
#     synthetic_path="data/synth/my_latlon_synth.dat",
#     x_bins=20,
#     y_bins=20,
#     input_coordinates="latlon",
#     coordinate_order="lonlat",
# )


result = bayesian_attack_score_only(
    orig_trajs=orig_trajs,
    syn_trajs=syn_trajs,
    grid_cells=grid_cells,
    vartheta=0.1,
    nth_densest_cell=10,
)

print("Sensitive zone:", result["sensitive_zone"])
print("Relevant synthetic trajectories:", result["relevant_subset_size"])
print(f"Trip JSD: {result['trip_jsd']:.3f}")
print(f"Markov JSD: {result['markov_jsd']:.3f}")
print("Passes Bayesian defense:", result["passes"])
print("############ Bayesian Attack END ############")

# ##########################################
# ############ Partial Sniffing ############

print("############ Partial Sniffing BEGIN ############")
# This is for lat, lon
# orig_xy, projection_info = parse_dat_trajectories(
#     "data/orig/brinkhoff_latlon.dat",
#     input_coordinates="latlon",
#     coordinate_order="lonlat",
# )
#
# syn_xy, _ = parse_dat_trajectories(
#     "data/synth/brinkhoff_latlon.dat",
#     input_coordinates="latlon",
#     coordinate_order="lonlat",
#     origin_lon=projection_info["origin_lon"],
#     origin_lat=projection_info["origin_lat"],
# )


# This is for x, y
orig_xy = parse_dat_trajectories(
    "data/orig/brinkhoff.dat",
    input_coordinates="xy",
)

syn_xy = parse_dat_trajectories(
    "data/synth/brinkhoff.dat-eps1.0-iteration1.dat",
    input_coordinates="xy",
)

# Use the same bounds and cell count as your AdaTrace experiment.
grid = Grid(
    cell_count=20,
    min_x=0.0,
    max_x=25000.0,
    min_y=0.0,
    max_y=25000.0,
)


result = partial_sniffing_score_only(
    orig_xy=orig_xy,
    syn_xy=syn_xy,
    grid=grid,
    sniff_n=12,
    sensitive_n=10,
    intersection_threshold=2,
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
print("############ Partial Sniffing END ############")

# ##########################################
# ############ Outlier Leakage ############

print("############ Outlier Leakage BEGIN ############")
# This is for lat, lon
# orig_xy, projection_info = parse_dat_trajectories(
#     "data/orig/brinkhoff_latlon.dat",
#     input_coordinates="latlon",
#     coordinate_order="lonlat",
# )
#
# syn_xy, _ = parse_dat_trajectories(
#     "data/synth/brinkhoff_latlon.dat",
#     input_coordinates="latlon",
#     coordinate_order="lonlat",
#     origin_lon=projection_info["origin_lon"],
#     origin_lat=projection_info["origin_lat"],
# )


# This is for x, y
orig_xy = parse_dat_trajectories(
    "data/orig/brinkhoff.dat",
    input_coordinates="xy",
)

syn_xy = parse_dat_trajectories(
    "data/synth/brinkhoff.dat-eps1.0-iteration1.dat",
    input_coordinates="xy",
)


result = outlier_leakage_score_only(
    orig_xy=orig_xy,
    syn_xy=syn_xy,
    top_k_neighbors=50,
    n_outliers=200,
    closest_threshold=0.1,
    plausible_deniability_kappa=100,
    plausible_deniability_beta=0.05,
    exact_adatrace=True,
    mutate_like_java_between_stages=True,
    show_progress_inner=False,
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
    print("  Failed indices:", stage["failed_indices_unique"][:20], "..." if len(stage["failed_indices_unique"]) > 20 else "")

print("############ Outlier Leakage END ############")