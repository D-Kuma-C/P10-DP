import os
import pandas as pd
from itertools import combinations

from trajectory import Trajectory
from measures.lors import LORS
from measures.lcrs import LCRS
from parser import load_dat_trajectories
from tqdm import tqdm

def build_dummy_trajectories():
    return [
        Trajectory(traj_id=1, segment_ids=[1, 2]),
        Trajectory(traj_id=2, segment_ids=[2, 3]),
        Trajectory(traj_id=3, segment_ids=[1, 2, 3]),
    ]


def run_measure(name, measure, trajectories, output_dir="../data/output"):
    os.makedirs(output_dir, exist_ok=True)

    traj_ids = [t.traj_id for t in trajectories]

    # Create square similarity matrix
    matrix = pd.DataFrame(
        index=traj_ids,
        columns=traj_ids,
        dtype=float
    )

    total_pairs = (len(trajectories) * (len(trajectories) + 1)) // 2
    progress = tqdm(total=total_pairs, desc=f"Running {name}")

    for i in range(len(trajectories)):
        t1 = trajectories[i]

        for j in range(i, len(trajectories)):
            t2 = trajectories[j]

            if i == j:
                score = 0.0
            else:
                score = measure.compute(t1, t2)

            # Fill upper triangle
            matrix.loc[t1.traj_id, t2.traj_id] = score

            # Fill symmetric lower triangle
            matrix.loc[t2.traj_id, t1.traj_id] = score

            progress.update(1)

    progress.close()

    output_path = f"{output_dir}/{name}_scores.csv"
    matrix.to_csv(output_path)

    print(f"Saved pairwise score matrix: {output_path}")


if __name__ == "__main__":

    input_file = "../data/input/brinkhoff.dat"

    if os.path.exists(input_file):
        print(f"Loading trajectories from: {input_file}")
        trajectories = load_dat_trajectories(input_file)
        print(f"Loaded {len(trajectories)} trajectories")
    else:
        print("No .dat file found in data/input/. Using dummy trajectories instead.")
        trajectories = build_dummy_trajectories()

    run_measure("LORS", LORS, trajectories)
    run_measure("LCRS", LCRS, trajectories)