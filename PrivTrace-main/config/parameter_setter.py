import numpy as np
import argparse
from pathlib import Path
import config.folder_and_file_names as fname


class ParSetter:

    def __init__(self):
        pass

    def parse_epsilon_partition(self, value):
        """
        Parse epsilon partition from command line.

        Example:
            --epsilon_partition 0.2,0.6,0.2
        """
        if isinstance(value, np.ndarray):
            return value

        if isinstance(value, list):
            return np.array(value, dtype=float)

        parts = [float(x.strip()) for x in str(value).split(",") if x.strip()]
        arr = np.array(parts, dtype=float)

        if len(arr) != 3:
            raise ValueError(
                "epsilon_partition must contain exactly 3 values, for example: 0.2,0.6,0.2"
            )

        if not np.isclose(arr.sum(), 1.0):
            raise ValueError(
                f"epsilon_partition must sum to 1.0, but got {arr.sum()}"
            )

        return arr

    def set_up_args(
        self,
        dataset_file_name=None,
        epsilon=False,
        epsilon_partition=False,
        level1_parameter=False,
        level2_parameter=False,
    ):
        parser = argparse.ArgumentParser()

        # Input trajectory file.
        # Can be a file inside datasets/, or an absolute/relative path from where PrivTrace is run.
        parser.add_argument(
            "--dataset_file_name",
            type=str,
            default=fname.dataset_file_name,
        )

        # Output synthetic trajectory file.
        # Can be absolute or relative.
        parser.add_argument(
            "--result_file_name",
            type=str,
            default=fname.result_file_name,
        )

        parser.add_argument(
            "--subdividing_inner_parameter",
            type=float,
            default=100,
        )

        parser.add_argument(
            "--total_epsilon",
            type=float,
            default=2.0,
        )

        # Use string parsing instead of type=np.ndarray.
        # Example: --epsilon_partition 0.2,0.6,0.2
        parser.add_argument(
            "--epsilon_partition",
            type=str,
            default="0.2,0.6,0.2",
        )

        # -1 means generate the same number of trajectories as the original dataset.
        parser.add_argument(
            "--trajectory_number_to_generate",
            type=int,
            default=-1,
        )

        args = vars(parser.parse_args())

        args["epsilon_partition"] = self.parse_epsilon_partition(args["epsilon_partition"])

        if epsilon is not False:
            args["total_epsilon"] = epsilon

        if epsilon_partition is not False:
            args["epsilon_partition"] = self.parse_epsilon_partition(epsilon_partition)

        if level1_parameter is not False:
            args["level1_divide_inner_parameter"] = level1_parameter

        if level2_parameter is not False:
            args["subdividing_inner_parameter"] = level2_parameter

        if dataset_file_name is not None:
            args["dataset_file_name"] = dataset_file_name

        return args