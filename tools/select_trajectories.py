from pathlib import Path
import argparse
import random


def parse_args():
    parser = argparse.ArgumentParser(
        description="Randomly select N trajectories from a .dat file and write a cleaned subset."
    )

    parser.add_argument(
        "--input-file",
        required=True,
        help="Input .dat trajectory file.",
    )

    parser.add_argument(
        "--output-file",
        required=True,
        help="Output .dat subset file.",
    )

    parser.add_argument(
        "--number-of-trajectories",
        type=int,
        required=True,
        help="Number of trajectories to randomly select.",
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducible selection.",
    )

    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Rewrite selected trajectory IDs as #0, #1, #2, ...",
    )

    return parser.parse_args()


def parse_traj_id(header_line: str) -> int:
    """
    Supports:
        #0
        #0:
    """
    text = header_line.strip()
    text = text.replace("#", "").replace(":", "").strip()
    return int(text)


def read_dat_blocks(input_file: Path):
    """
    Returns:
        list of (original_traj_id, block_lines)
    """
    blocks = []
    current_id = None
    current_block = []

    with input_file.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                if current_id is not None and current_block:
                    blocks.append((current_id, current_block))

                current_id = parse_traj_id(stripped)
                current_block = [line]
            else:
                if current_id is not None:
                    current_block.append(line)

    if current_id is not None and current_block:
        blocks.append((current_id, current_block))

    return blocks


def write_subset(output_file: Path, selected_blocks, reindex: bool):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as out:
        for new_id, (original_id, block_lines) in enumerate(selected_blocks):
            if reindex:
                out.write(f"#{new_id}:\n")

                for line in block_lines[1:]:
                    out.write(line)
            else:
                for line in block_lines:
                    out.write(line)


def main():
    args = parse_args()

    input_file = Path(args.input_file)
    output_file = Path(args.output_file)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    blocks = read_dat_blocks(input_file)

    if args.number_of_trajectories > len(blocks):
        raise ValueError(
            f"Requested {args.number_of_trajectories} trajectories, "
            f"but only {len(blocks)} exist in {input_file}"
        )

    random.seed(args.random_seed)
    selected_blocks = random.sample(blocks, args.number_of_trajectories)

    # Sort by original ID for deterministic output order.
    selected_blocks = sorted(selected_blocks, key=lambda x: x[0])

    write_subset(
        output_file=output_file,
        selected_blocks=selected_blocks,
        reindex=args.reindex,
    )

    selected_ids = [traj_id for traj_id, _ in selected_blocks]

    print("Finished selecting trajectories.")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Total input trajectories: {len(blocks)}")
    print(f"Selected trajectories: {len(selected_blocks)}")
    print(f"Random seed: {args.random_seed}")
    print(f"Reindexed: {args.reindex}")
    print(f"First selected IDs: {selected_ids[:20]}")


if __name__ == "__main__":
    main()