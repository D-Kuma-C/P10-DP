import pandas as pd

from Attack_model.reidentification_probability import reidentification_prob
from ConvertToFrames import *
from ParserToBayesian import *
from Attack_model.bayesian_attack import bayesian_attack_score_only
from geometry import Grid
from ParserToPartial import parse_dat_trajectories
from Attack_model.partial_sniffing import partial_sniffing_score_only

# orig = pd.DataFrame(
#     [
#         [1,1,1,1,2,2,2,2,1,1,1,1],
#         [1,1,1,2,2,2,2,1,1,1,1,1],
#         [2,2,2,2,3,3,3,3,2,2,2,2],
#         [2,2,2,2,4,4,4,4,4,2,2,2],
#         [1,1,1,1,3,3,3,3,3,3,1,1],
#         [2,2,3,3,3,3,3,2,2,2,2,2],
#         [2,2,2,2,2,2,4,4,4,4,4,2],
#     ],
#     columns=[f"1_Hour{i}" for i in range(12)]
# ).astype(str)
# orig['User'] = range(len(orig))
# orig = orig.set_index('User')
#
#
# synth = pd.DataFrame(
#     [
#         [1,1,1,1,2,2,2,2,1,1,1,1],
#         [1,1,1,2,2,2,2,1,1,1,1,1],
#         [2,2,2,2,3,3,3,3,2,2,2,2],
#         [2,2,2,2,4,4,4,4,4,2,2,2],
#         [2,2,2,2,1,1,1,1,1,2,2,2]
#     ],
#     columns=[f"1_Hour{i}" for i in range(12)]
# ).astype(str)

# ##########################################
# ############ Reidentification ############
# orig = convert_dat_to_dataframe("data/orig/brinkhoff.dat")
# synth = convert_dat_to_dataframe("data/synth/brinkhoff.dat-eps1.0-iteration1.dat")
#
#
# print("Reidentification probability score", reidentification_prob(synth, orig, 3, 3))

# ##########################################
# ############ Bayesian Attack #############
# orig_points = parse_dat_trajectories("data/orig/brinkhoff.dat")
# syn_points = parse_dat_trajectories("data/synth/brinkhoff.dat-eps1.0-iteration1.dat")
#
# grid_info, grid_cells = build_grid_from_data(
#     point_datasets=[orig_points, syn_points],
#     x_bins=20,
#     y_bins=20,
# )
#
# orig_trajs = convert_points_to_cells(
#     orig_points,
#     grid_info,
#     remove_consecutive_duplicates=True,
# )
#
# syn_trajs = convert_points_to_cells(
#     syn_points,
#     grid_info,
#     remove_consecutive_duplicates=True,
# )
#
# result = bayesian_attack_score_only(
#     orig_trajs=orig_trajs,
#     syn_trajs=syn_trajs,
#     grid_cells=grid_cells,
#     vartheta=0.1,
#     nth_densest_cell=10,
# )
#
# print("Sensitive zone:", result["sensitive_zone"])
# print("Relevant synthetic trajectories:", result["relevant_subset_size"])
# print(f"Trip JSD: {result['trip_jsd']:.3f}")
# print(f"Markov JSD: {result['markov_jsd']:.3f}")
# print("Passes Bayesian defense:", result["passes"])

# ##########################################
# ############ Partial Sniffing ############
orig_xy = parse_dat_trajectories("data/orig/brinkhoff.dat")
syn_xy = parse_dat_trajectories("data/synth/brinkhoff.dat-eps1.0-iteration1.dat")

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

