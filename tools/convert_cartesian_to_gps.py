from pathlib import Path
import argparse
from pyproj import Transformer


def convert_xy_to_gps(input_file: Path, output_file: Path, source_crs: str, target_crs: str):
    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    transformer = Transformer.from_crs(
        source_crs,
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

                    x = float(parts[0])
                    y = float(parts[1])

                    lon, lat = transformer.transform(x, y)

                    converted_points.append(f"{lon:.8f},{lat:.8f}")
                    point_count += 1

                out.write(">0:" + ";".join(converted_points) + ";\n")

    print("Cartesian x,y to GPS lon,lat conversion complete.")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Source CRS: {source_crs}")
    print(f"Target CRS: {target_crs}")
    print(f"Trajectories: {trajectory_count}")
    print(f"Points: {point_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert AdaTrace x,y .dat output back to GPS lon,lat .dat."
    )

    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)

    parser.add_argument(
        "--source-crs",
        default="EPSG:32629",
        help="Source projected CRS. Default: EPSG:32629.",
    )

    parser.add_argument(
        "--target-crs",
        default="EPSG:4326",
        help="Target GPS CRS. Default: EPSG:4326.",
    )

    args = parser.parse_args()

    convert_xy_to_gps(
        input_file=Path(args.input),
        output_file=Path(args.output),
        source_crs=args.source_crs,
        target_crs=args.target_crs,
    )


if __name__ == "__main__":
    main()