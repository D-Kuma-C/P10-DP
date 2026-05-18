import numpy as np
import os
import re
from pathlib import Path
import config.folder_and_file_names as config


class DataReader:

    def __init__(self):
        pass

    def read_trajectories_from_data_file(self, file_n):
        """
        Read trajectory file.

        Supports:
        1. Original PrivTrace behavior:
           --dataset_file_name simple_example.dat
           -> reads ./datasets/simple_example.dat

        2. Absolute or relative pipeline paths:
           --dataset_file_name C:/.../input/cleandata/porto/file.dat
           -> reads that exact file

           --dataset_file_name ../input/cleandata/porto/file.dat
           -> reads that relative file
        """
        input_path = Path(file_n)

        if input_path.is_absolute():
            file_name = input_path
        elif input_path.exists():
            file_name = input_path
        else:
            file_name = Path(".") / config.trajectory_data_folder / file_n

        if not file_name.exists():
            raise FileNotFoundError(f"Input trajectory file not found: {file_name}")

        trajectory_list = self.read_tra_data(file_name)
        return trajectory_list

    def read_tra_data(self, file_name):
        trajectory_list = []

        with open(file_name, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()

                if not line:
                    continue

                if line[0] == ">":
                    trajectory_data_carrier = line[3:]

                    raw_points = [p for p in trajectory_data_carrier.split(";") if p.strip()]
                    trajectory_points = []

                    for raw_point in raw_points:
                        parts = [p.strip() for p in raw_point.split(",")]

                        if len(parts) < 2:
                            continue

                        # PrivTrace expects only x,y or lon,lat.
                        # If timestamp exists, ignore it.
                        x = float(parts[0])
                        y = float(parts[1])

                        trajectory_points.append([x, y])

                    if len(trajectory_points) >= 2:
                        trajectory_array = np.array(trajectory_points, dtype=float)
                        trajectory_list.append(trajectory_array)

        return trajectory_list