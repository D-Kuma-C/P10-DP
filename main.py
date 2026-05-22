from pathlib import Path
import subprocess
import sys

from pipelines.common import load_config
from pipelines.dataset_selection_pipeline import run_dataset_selection
from pipelines.adatrace_pipeline import (
    run_adatrace_pipeline,
    convert_adatrace_outputs_to_gps,
)
from pipelines.dpstar_pipeline import run_dpstar_pipeline
from pipelines.privtrace_pipeline import run_privtrace_pipeline
from pipelines.dpstts_pipeline import run_dpstts_pipeline
from pipelines.mapmatching_pipeline import run_mapmatching_for_method
from pipelines.similarity_pipeline import run_similarity_for_method
from pipelines.privacy_attack_pipeline import (
    run_privacy_attacks_for_adatrace,
    run_privacy_attacks_for_dpstar,
    run_privacy_attacks_for_privtrace,
    run_privacy_attacks_for_dpstts,
)


ROOT_DIR = Path(__file__).resolve().parent

def main():
    try:
        config = load_config(ROOT_DIR)
        dp_methods = config["dp_methods"]
        privacy_cfg = config.get("privacy_attack", {})
        privacy_enabled = privacy_cfg.get("enabled", False)
        privacy_only = privacy_cfg.get("run_without_generation", False)
        similarity_cfg = config.get("trajectory_similarity", {})
        similarity_enabled = similarity_cfg.get("enabled", False)

        selected_dataset = run_dataset_selection(ROOT_DIR, config)

        if selected_dataset is not None:
            print(f"\nSelected dataset ready: {selected_dataset}")

        # if dp_methods["adatrace"].get("enabled", False):
        #     if not privacy_only:
        #         run_adatrace_pipeline(ROOT_DIR, config)
        #         # Converts AdaTrace x,y synthetic output into lon,lat copies
        #         # for map-matching and trajectory similarity.
        #         convert_adatrace_outputs_to_gps(ROOT_DIR, config)
        #         run_mapmatching_for_method(ROOT_DIR, config, "adatrace")
        #
        #     if privacy_enabled:
        #         run_privacy_attacks_for_adatrace(ROOT_DIR, config)
        #
        #     if similarity_enabled:
        #         run_similarity_for_method(ROOT_DIR, config, "adatrace")
        #
        # if dp_methods["dp-star"].get("enabled", False):
        #     if not privacy_only:
        #         run_dpstar_pipeline(ROOT_DIR, config)
        #         run_mapmatching_for_method(ROOT_DIR, config, "dp-star")
        #
        #     if privacy_enabled:
        #         run_privacy_attacks_for_dpstar(ROOT_DIR, config)
        #
        #     if similarity_enabled:
        #         run_similarity_for_method(ROOT_DIR, config, "dp-star")
        #
        # if dp_methods["dp-stts"].get("enabled", False):
        #     if not privacy_only:
        #         run_dpstts_pipeline(ROOT_DIR, config)
        #         run_mapmatching_for_method(ROOT_DIR, config, "dp-stts")
        #
        #     if privacy_enabled:
        #         run_privacy_attacks_for_dpstts(ROOT_DIR, config)
        #
        #     if similarity_enabled:
        #         run_similarity_for_method(ROOT_DIR, config, "dp-stts")
        #
        # if dp_methods["privtrace"].get("enabled", False):
        #     if not privacy_only:
        #         run_privtrace_pipeline(ROOT_DIR, config)
        #         run_mapmatching_for_method(ROOT_DIR, config, "privtrace")
        #
        #     if privacy_enabled:
        #         run_privacy_attacks_for_privtrace(ROOT_DIR, config)
        #
        #     if similarity_enabled:
        #         run_similarity_for_method(ROOT_DIR, config, "privtrace")

    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed with exit code {e.returncode}")
        sys.exit(e.returncode)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
