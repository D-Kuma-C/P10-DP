# from pyproj import Transformer
#
# input_file = r"C:\Users\test\Desktop\Uni\P10-DP\input\cleandata\porto\porto_time_lines-20000_p-3_d-0.05_s-40_t-15min_start-20130107_end-20140630_small_500.dat"
# output_file = r"C:\Users\test\Desktop\Uni\P10-DP\input\cleandata\porto\porto_500.dat"
#
# # WGS84 lon/lat -> Web Mercator x/y
# transformer = Transformer.from_crs("EPSG:4326", "EPSG:32629", always_xy=True)
#
# with open(input_file, "r", encoding="utf-8") as f:
#     lines = f.readlines()
#
# with open(output_file, "w", encoding="utf-8") as out:
#     for line in lines:
#         line = line.strip()
#
#         if not line:
#             continue
#
#         if line.startswith("#"):
#             out.write(line + "\n")
#
#         elif line.startswith(">0:"):
#             points = line[3:].split(";")
#             new_points = []
#
#             for p in points:
#                 p = p.strip()
#                 if not p:
#                     continue
#
#                 parts = p.split(",")
#
#                 if len(parts) < 2:
#                     continue
#
#                 lon = float(parts[0])
#                 lat = float(parts[1])
#
#                 x, y = transformer.transform(lon, lat)
#
#                 # AdaTrace input: x,y only
#                 new_points.append(f"{x},{y}")
#
#             out.write(">0:" + ";".join(new_points) + ";\n")
#
# print("Conversion complete.")

from pathlib import Path
import argparse
from pyproj import Transformer


def convert_gps_to_cartesian(input_file: Path, output_file: Path, target_crs: str):
    """
    Converts .dat trajectory data from:

        lon,lat,timestamp

    to:

        x,y

    The output is intended for AdaTrace.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    transformer = Transformer.from_crs(
        "EPSG:4326",
        target_crs,
        always_xy=True,
    )

    trajectory_count = 0
    point_count = 0

    with input_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    with output_file.open("w", encoding="utf-8") as out:
        for raw_line in lines:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                out.write(line + "\n")
                trajectory_count += 1
                continue

            if line.startswith(">"):
                point_text = line.split(":", 1)[1]
                raw_points = point_text.split(";")

                converted_points = []

                for raw_point in raw_points:
                    raw_point = raw_point.strip()

                    if not raw_point:
                        continue

                    parts = [p.strip() for p in raw_point.split(",")]

                    if len(parts) < 2:
                        continue

                    lon = float(parts[0])
                    lat = float(parts[1])

                    x, y = transformer.transform(lon, lat)

                    converted_points.append(f"{x:.8f},{y:.8f}")
                    point_count += 1

                out.write(">0:" + ";".join(converted_points) + ";\n")

    print("Conversion complete.")
    print(f"Input GPS file: {input_file}")
    print(f"Output x,y file: {output_file}")
    print(f"Target CRS: {target_crs}")
    print(f"Trajectories: {trajectory_count}")
    print(f"Points: {point_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert GPS lon,lat .dat trajectories to Cartesian x,y .dat trajectories for AdaTrace."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input GPS .dat file with lon,lat,timestamp points.",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path plus filename for output x,y .dat file.",
    )

    parser.add_argument(
        "--target-crs",
        default="EPSG:32629",
        help="Target projected CRS. Default is EPSG:32629 for Porto / UTM zone 29N.",
    )

    args = parser.parse_args()

    convert_gps_to_cartesian(
        input_file=Path(args.input),
        output_file=Path(args.output),
        target_crs=args.target_crs,
    )


if __name__ == "__main__":
    main()