from pathlib import Path
import argparse


def copy_first_n_trajectories(input_file: Path, output_file: Path, n: int):
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    current_header = None

    with input_file.open("r", encoding="utf-8") as infile, output_file.open("w", encoding="utf-8") as outfile:
        for raw_line in infile:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                if written >= n:
                    break

                current_header = f"#{written}"
                continue

            if line.startswith(">"):
                if current_header is None:
                    continue

                outfile.write(current_header + "\n")
                outfile.write(line + "\n")
                written += 1
                current_header = None

                if written >= n:
                    break

    print(f"Created: {output_file}")
    print(f"Trajectories written: {written}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a smaller .dat trajectory file for testing."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to the original .dat file.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Path to output .dat file. If omitted, output is created beside input.",
    )

    parser.add_argument(
        "--n",
        type=int,
        default=500,
        help="Number of trajectories to keep. Default: 500.",
    )

    args = parser.parse_args()

    input_file = Path(args.input)

    if args.output is None:
        output_file = input_file.with_name(
            input_file.stem + f"_small_{args.n}" + input_file.suffix
        )
    else:
        output_file = Path(args.output)

    copy_first_n_trajectories(
        input_file=input_file,
        output_file=output_file,
        n=args.n,
    )


if __name__ == "__main__":
    main()