from pathlib import Path
import subprocess
import json


def load_config(root_dir: Path, config_name: str = "config.json") -> dict:
    config_path = root_dir / config_name

    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_path(root_dir: Path, value):
    """
    Resolve paths from config.json.

    Relative paths are relative to project root.
    Absolute paths stay absolute.
    None stays None.
    """
    if value is None or value == "":
        return None

    path = Path(value)

    if path.is_absolute():
        return path

    return root_dir / path


def run_command(command, cwd=None):
    print()
    print(" ".join(f'"{x}"' if " " in str(x) else str(x) for x in command))
    print()

    subprocess.run(
        [str(x) for x in command],
        cwd=cwd,
        check=True,
    )


def format_epsilon_list(epsilons):
    return ",".join(str(eps) for eps in epsilons)


def epsilon_label(epsilon):
    return f"eps_{epsilon}"