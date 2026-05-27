from pathlib import Path
from datetime import datetime
import argparse
import shutil
from datetime import datetime


ROOT_DIR = Path(__file__).resolve().parents[1]


def normalize_timestamp_to_fixed_date(timestamp: str, fixed_date: str = "1900-01-01") -> str:
    """
    Keeps hour/minute/second, but replaces the calendar date.

    Example:
        2013-07-01 14:29:21 -> 1900-01-01 14:29:21
    """
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    return f"{fixed_date} {dt.strftime('%H:%M:%S')}"


def find_default_dpstts_dir() -> Path:
    candidates = [
        ROOT_DIR / "dp-stts",
        ROOT_DIR / "DP-STTS",
        ROOT_DIR / "DP_STTS",
        ROOT_DIR / "DP-STTS-main",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # fallback
    return ROOT_DIR / "dp-stts"


def parse_timestamp(value: str) -> datetime:
    value = value.strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    raise ValueError(f"Could not parse timestamp: {value}")


def parse_dat_file(input_file: Path):
    """
    Reads .dat files like:

    #0:
    >0:-8.580051,41.159394,1900-01-01 14:29:21;
    #1:
    >0:-8.621037,41.161059,1900-01-01 14:22:56;-8.621109,41.160726,1900-01-01 14:23:11;

    Point format:
        lon,lat,timestamp
    """
    trajectories = []
    current_id = None

    with input_file.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                id_text = line.replace("#", "").replace(":", "").strip()
                current_id = int(id_text)
                continue

            if line.startswith(">"):
                if current_id is None:
                    continue

                point_text = line.split(":", 1)[1]
                raw_points = [p.strip() for p in point_text.split(";") if p.strip()]

                points = []

                for raw_point in raw_points:
                    parts = [p.strip() for p in raw_point.split(",")]

                    if len(parts) < 3:
                        continue

                    lon = float(parts[0])
                    lat = float(parts[1])
                    timestamp = parts[2]

                    # Validate timestamp now, so bad data is caught early.
                    parse_timestamp(timestamp)

                    points.append(
                        {
                            "lon": lon,
                            "lat": lat,
                            "timestamp": timestamp,
                        }
                    )

                if points:
                    trajectories.append(
                        {
                            "traj_id": current_id,
                            "points": points,
                        }
                    )

    return trajectories


def write_dpstts_raw_dat(trajectories, output_file: Path, normalize_dates: bool = True):
    """
    Writes a cleaned DP-STTS raw file using the same .dat structure.

    This keeps:
        lon,lat,timestamp

    Example:
        #0:
        >0:-8.580051,41.159394,1900-01-01 14:29:21;
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        new_id = 0

        for traj in trajectories:
            point_strings = []
            previous_dt = None

            for p in traj["points"]:
                timestamp = p["timestamp"]

                if normalize_dates:
                    timestamp = normalize_timestamp_to_fixed_date(
                        timestamp,
                        fixed_date="1900-01-01",
                    )

                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

                # Skip points that move backwards in normalized time.
                if previous_dt is not None and dt <= previous_dt:
                    continue

                point_strings.append(
                    f"{p['lon']},{p['lat']},{timestamp}"
                )

                previous_dt = dt

            if len(point_strings) < 2:
                continue

            f.write(f"#{new_id}:\n")
            f.write(">0:")
            f.write(";".join(point_strings))
            f.write(";\n")

            new_id += 1


def infer_bounds(trajectories):
    lon_values = []
    lat_values = []

    for traj in trajectories:
        for p in traj["points"]:
            lon_values.append(p["lon"])
            lat_values.append(p["lat"])

    if not lon_values or not lat_values:
        raise ValueError("No valid coordinates found.")

    lon_min = min(lon_values)
    lon_max = max(lon_values)
    lat_min = min(lat_values)
    lat_max = max(lat_values)

    return lon_min, lon_max, lat_min, lat_max


def apply_boundary_padding(lon_min, lon_max, lat_min, lat_max, padding_ratio: float):
    lon_span = lon_max - lon_min
    lat_span = lat_max - lat_min

    if lon_span == 0:
        lon_span = 0.000001

    if lat_span == 0:
        lat_span = 0.000001

    lon_pad = lon_span * padding_ratio
    lat_pad = lat_span * padding_ratio

    return (
        lon_min - lon_pad,
        lon_max + lon_pad,
        lat_min - lat_pad,
        lat_max + lat_pad,
    )


def infer_time_range(trajectories, fixed_date: str = "1900-01-01"):
    """
    Infer DP-STTS time range from trajectory start and end times only.

    start_time = minimum time-of-day of the first point in each trajectory
    end_time   = maximum time-of-day of the last point in each trajectory

    Dates are normalized to fixed_date.
    """
    start_times = []
    end_times = []

    for traj in trajectories:
        points = traj["points"]

        if not points:
            continue

        start_dt = parse_timestamp(points[0]["timestamp"])
        end_dt = parse_timestamp(points[-1]["timestamp"])

        start_times.append(start_dt.time())
        end_times.append(end_dt.time())

    if not start_times or not end_times:
        raise ValueError("No valid trajectory start/end timestamps found.")

    min_start_time = min(start_times)
    max_end_time = max(end_times)

    return (
        datetime.strptime(f"{fixed_date} {min_start_time}", "%Y-%m-%d %H:%M:%S"),
        datetime.strptime(f"{fixed_date} {max_end_time}", "%Y-%m-%d %H:%M:%S"),
    )


def write_boundary_file(parameters_dir: Path, lon_min, lon_max, lat_min, lat_max):
    """
    DP-STTS boundary.txt uses this order:

        left right bottom top

    For lon/lat:

        lon_min lon_max lat_min lat_max
    """
    boundary_file = parameters_dir / "boundary.txt"

    with boundary_file.open("w", encoding="utf-8") as f:
        f.write(f"{lon_min} {lon_max} {lat_min} {lat_max}\n")

    print(f"Wrote boundary: {boundary_file}")
    print(f"  left/lon_min   = {lon_min}")
    print(f"  right/lon_max  = {lon_max}")
    print(f"  bottom/lat_min = {lat_min}")
    print(f"  top/lat_max    = {lat_max}")


def write_cell_size_file(parameters_dir: Path, cell_h: int, cell_w: int):
    cell_size_file = parameters_dir / "cellSize.txt"

    with cell_size_file.open("w", encoding="utf-8") as f:
        f.write(f"{cell_h} {cell_w}\n")

    print(f"Wrote cell size: {cell_size_file}")
    print(f"  cellH = {cell_h}")
    print(f"  cellW = {cell_w}")
    print(f"  cellCount = {cell_h * cell_w}")


def write_time_file(
    parameters_dir: Path,
    start_time: datetime,
    end_time: datetime,
    full_day_time: bool = False,
    fixed_date: str = "1900-01-01",
):
    """
    DP-STTS should use a single-day time window.

    Therefore time.txt must use the same fixed date.
    """
    time_file = parameters_dir / "time.txt"

    if full_day_time:
        start_text = f"{fixed_date} 00:00:00"
        end_text = f"{fixed_date} 23:59:59"
    else:
        start_text = f"{fixed_date} {start_time.strftime('%H:%M:%S')}"
        end_text = f"{fixed_date} {end_time.strftime('%H:%M:%S')}"

    with time_file.open("w", encoding="utf-8") as f:
        f.write(start_text + "\n")
        f.write(end_text + "\n")

    print(f"Wrote time range: {time_file}")
    print(f"  start = {start_text}")
    print(f"  end   = {end_text}")



def write_time_step_file(parameters_dir: Path, time_step_minutes: int):
    time_step_file = parameters_dir / "timeStep.txt"

    with time_step_file.open("w", encoding="utf-8") as f:
        f.write(f"{time_step_minutes}\n")

    print(f"Wrote time step: {time_step_file}")
    print(f"  timestep = {time_step_minutes} minutes")


def cell_index(row: int, col: int, cell_w: int) -> int:
    return row * cell_w + col


def write_neighbor_file(parameters_dir: Path, cell_h: int, cell_w: int):
    """
    DP-STTS parameters.py reads:

        neighborFile_<cellH>.txt

    and expects 9 integers per cell.

    This creates 8-neighborhood + self, padded with -1.
    """
    neighbor_file = parameters_dir / f"neighborFile_{cell_h}.txt"

    with neighbor_file.open("w", encoding="utf-8") as f:
        for row in range(cell_h):
            for col in range(cell_w):
                neighbors = []

                # Put self first because DP-STTS treats staying in same cell specially.
                neighbors.append(cell_index(row, col, cell_w))

                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue

                        nr = row + dr
                        nc = col + dc

                        if 0 <= nr < cell_h and 0 <= nc < cell_w:
                            neighbors.append(cell_index(nr, nc, cell_w))

                # DP-STTS reads exactly 9 values.
                neighbors = neighbors[:9]
                while len(neighbors) < 9:
                    neighbors.append(-1)

                f.write(" ".join(str(n) for n in neighbors) + "\n")

    print(f"Wrote neighbor file: {neighbor_file}")

def parse_epsilon_list(value: str) -> list[float]:
    """
    Example:
        "0.5,1.0"
    """
    return [float(v.strip()) for v in value.split(",") if v.strip()]

def prepare_output_folders(output_root: Path, epsilons: list[float]):
    output_root.mkdir(parents=True, exist_ok=True)

    for epsilon in epsilons:
        eps_dir = output_root / f"eps_{epsilon}"
        eps_dir.mkdir(parents=True, exist_ok=True)
        print(f"Prepared output folder: {eps_dir}")

def prepare_dpstts_dataset(
    input_file: Path,
    dpstts_dir: Path,
    output_root: Path,
    epsilons: list[float],
    cell_h: int,
    cell_w: int,
    time_step_minutes: int,
    boundary_padding_ratio: float,
    force_full_day_time: bool,
    overwrite_output: bool,
):
    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    if not dpstts_dir.exists():
        raise FileNotFoundError(f"DP-STTS directory does not exist: {dpstts_dir}")

    data_dir = dpstts_dir / "data"
    raw_data_dir = data_dir / "raw_data"
    parameters_dir = data_dir / "parameters"
    output_dir = data_dir / "output"

    raw_data_dir.mkdir(parents=True, exist_ok=True)
    parameters_dir.mkdir(parents=True, exist_ok=True)

    if overwrite_output and output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    prepare_output_folders(output_root, epsilons)

    print(f"Reading input: {input_file}")
    trajectories = parse_dat_file(input_file)

    if not trajectories:
        raise ValueError("No trajectories were parsed from the input file.")

    print(f"Parsed trajectories: {len(trajectories)}")

    # DP-STTS comments mention Original.txt.
    original_file = raw_data_dir / "Original.txt"

    write_dpstts_raw_dat(trajectories, original_file, normalize_dates=True)

    print(f"Wrote raw DP-STTS file: {original_file}")

    lon_min, lon_max, lat_min, lat_max = infer_bounds(trajectories)
    lon_min, lon_max, lat_min, lat_max = apply_boundary_padding(
        lon_min,
        lon_max,
        lat_min,
        lat_max,
        boundary_padding_ratio,
    )

    if force_full_day_time:
        start_time = parse_timestamp("1900-01-01 00:00:00")
        end_time = parse_timestamp("1900-01-01 23:59:59")
    else:
        start_time, end_time = infer_time_range(
            trajectories,
            fixed_date="1900-01-01",
        )

    print(f"force_full_day_time = {force_full_day_time}")
    print(f"DP-STTS start_time  = {start_time}")
    print(f"DP-STTS end_time    = {end_time}")

    write_boundary_file(
        parameters_dir=parameters_dir,
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
    )

    write_cell_size_file(
        parameters_dir=parameters_dir,
        cell_h=cell_h,
        cell_w=cell_w,
    )

    write_time_file(
        parameters_dir=parameters_dir,
        start_time=start_time,
        end_time=end_time,
        full_day_time=False,
        fixed_date="1900-01-01",
    )

    write_time_step_file(
        parameters_dir=parameters_dir,
        time_step_minutes=time_step_minutes,
    )

    write_neighbor_file(
        parameters_dir=parameters_dir,
        cell_h=cell_h,
        cell_w=cell_w,
    )

    print("\nDP-STTS preparation complete.")
    print(f"DP-STTS dir: {dpstts_dir}")
    print(f"Raw data dir: {raw_data_dir}")
    print(f"Parameters dir: {parameters_dir}")
    print(f"Output dir: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare cleaned .dat trajectory data for DP-STTS."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to cleaned .dat file with lon,lat,timestamp points.",
    )

    parser.add_argument(
        "--dpstts-dir",
        default=str(find_default_dpstts_dir()),
        help="Path to DP-STTS project folder.",
    )

    parser.add_argument(
        "--output-root",
        required=True,
        help="Root output folder for final DP-STTS synthetic .dat files.",
    )

    parser.add_argument(
        "--epsilons",
        default="0.5,1.0",
        help="Comma-separated epsilons. Example: 0.5,1.0",
    )

    parser.add_argument(
        "--cell-h",
        type=int,
        default=6,
        help="Grid height / number of rows.",
    )

    parser.add_argument(
        "--cell-w",
        type=int,
        default=6,
        help="Grid width / number of columns.",
    )

    parser.add_argument(
        "--time-step",
        type=int,
        default=15,
        help="Time step in minutes.",
    )

    parser.add_argument(
        "--boundary-padding-ratio",
        type=float,
        default=0.00001,
        help="Small padding added to inferred spatial boundary.",
    )

    parser.add_argument(
        "--full-day-time",
        action="store_true",
        help="Use 00:00:00 to 23:59:59 instead of inferred min/max time.",
    )

    parser.add_argument(
        "--keep-old-output",
        action="store_true",
        help="Do not delete DP-STTS data/output folder.",
    )

    args = parser.parse_args()

    epsilons = parse_epsilon_list(args.epsilons)

    prepare_dpstts_dataset(
        input_file=Path(args.input),
        dpstts_dir=Path(args.dpstts_dir),
        output_root=Path(args.output_root),
        epsilons=epsilons,
        cell_h=args.cell_h,
        cell_w=args.cell_w,
        time_step_minutes=args.time_step,
        boundary_padding_ratio=args.boundary_padding_ratio,
        force_full_day_time=args.full_day_time,
        overwrite_output=not args.keep_old_output,
    )


if __name__ == "__main__":
    main()