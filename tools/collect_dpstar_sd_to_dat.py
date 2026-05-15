from pathlib import Path
import argparse
import re
from tqdm import tqdm


ROOT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_SD_ROOT = (
    ROOT_DIR
    / "DP-Star"
    / "data"
    / "Geolife Trajectories 1.3"
    / "SD"
)

DEFAULT_OUTPUT_ROOT = ROOT_DIR / "input" / "dpstar_synthetic"


def epsilon_from_folder_name(folder_name: str) -> str:
    """
    Extract epsilon from folder names like:
        sd_final_epsilon_0.1
        sd_final_epsilon_1.0
    """
    match = re.search(r"sd_final_epsilon_(.+)$", folder_name)

    if not match:
        raise ValueError(f"Could not extract epsilon from folder name: {folder_name}")

    return match.group(1)


def extract_user_number(path: Path) -> int:
    """
    Extract user/trajectory number from filenames like:
        traj_0000000.txt
        traj_0000001.txt
        traj_123.txt
    """
    match = re.search(r"traj_(\d+)", path.stem)

    if match:
        return int(match.group(1))

    # fallback: first number in filename
    match = re.search(r"(\d+)", path.stem)
    if match:
        return int(match.group(1))

    raise ValueError(f"Could not extract user number from filename: {path.name}")


def read_dpstar_txt_trajectory(txt_file: Path):
    """
    Reads one DP-Star final trajectory file.

    Input format per line:
        lat,lon

    Returns:
        list[tuple[lon, lat]]
    """
    points = []

    with txt_file.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                continue

            parts = [p.strip() for p in line.split(",")]

            if len(parts) < 2:
                continue

            lat = float(parts[0])
            lon = float(parts[1])

            points.append((lon, lat))

    return points


def write_dat_for_epsilon_folder(epsilon_folder: Path, output_root: Path):
    epsilon = epsilon_from_folder_name(epsilon_folder.name)

    output_dir = output_root / f"eps_{epsilon}"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"dpstar_eps_{epsilon}.dat"

    txt_files = sorted(
        [
            p for p in epsilon_folder.iterdir()
            if p.is_file() and p.name.startswith("traj_")
        ],
        key=extract_user_number,
    )

    if not txt_files:
        print(f"Skipping {epsilon_folder}: no .txt files found.")
        return

    written_count = 0

    with output_file.open("w", encoding="utf-8") as out:
        for txt_file in tqdm(
                txt_files,
                desc=f"Converting epsilon {epsilon}",
                unit="traj",
        ):
            user_number = extract_user_number(txt_file)
            points = read_dpstar_txt_trajectory(txt_file)

            if len(points) < 2:
                continue

            out.write(f"#{user_number}\n")
            out.write(">0:")

            point_strings = [
                f"{lon},{lat}"
                for lon, lat in points
            ]

            out.write(";".join(point_strings))
            out.write("\n")

            written_count += 1

    print(f"Created {output_file}")
    print(f"Trajectories written: {written_count}")


def collect_all(sd_root: Path, output_root: Path):
    if not sd_root.exists():
        raise FileNotFoundError(f"SD root folder does not exist: {sd_root}")

    epsilon_folders = sorted(
        [
            p for p in sd_root.iterdir()
            if p.is_dir() and p.name.startswith("sd_final_epsilon_")
        ],
        key=lambda p: float(epsilon_from_folder_name(p.name)),
    )

    if not epsilon_folders:
        raise FileNotFoundError(
            f"No sd_final_epsilon_* folders found inside: {sd_root}"
        )

    output_root.mkdir(parents=True, exist_ok=True)

    for epsilon_folder in tqdm(
        epsilon_folders,
        desc="Processing epsilon folders",
        unit="eps",
    ):
        write_dat_for_epsilon_folder(
            epsilon_folder=epsilon_folder,
            output_root=output_root,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Convert DP-Star sd_final_epsilon_* txt outputs into .dat files."
    )

    parser.add_argument(
        "--sd-root",
        default=str(DEFAULT_SD_ROOT),
        help="Path to DP-Star SD folder containing sd_final_epsilon_* folders.",
    )

    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Output root folder. Default: root/input/dpstar_synthetic",
    )

    args = parser.parse_args()

    collect_all(
        sd_root=Path(args.sd_root),
        output_root=Path(args.output_root),
    )


if __name__ == "__main__":
    main()