import os
import random
import pandas as pd
from tqdm import tqdm

from stratify import assign_trip_length_groups, TRIP_GROUPS


def safe_label(value: str) -> str:
    return str(value).strip().replace(" ", "_").replace("/", "_")

class DistributionExperiment:
    def __init__(
            self,
            original_trajectories,
            synthetic_trajectories,
            epsilon,
            dp_model,
            trajectory_count_label,
            dataset_name,
            measures,
            roadmap,
            output_dir="data/output",
            max_pairs_per_comparison=10000,random_seed=42,
    ):
        self.original = original_trajectories
        self.synthetic = synthetic_trajectories
        self.epsilon = str(epsilon)
        self.dp_model = safe_label(dp_model)
        self.trajectory_count_label = safe_label(trajectory_count_label)
        self.dataset_name = safe_label(dataset_name)
        self.epi_label = f"epi_{safe_label(self.epsilon)}"
        self.file_stub = f"{self.dp_model}_{self.trajectory_count_label}_{self.dataset_name}_{self.epi_label}"
        self.measures = measures
        self.roadmap = roadmap
        self.output_dir = output_dir
        self.max_pairs = max_pairs_per_comparison
        random.seed(random_seed)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "summaries"), exist_ok=True)
        self.baseline_dir = os.path.join(self.output_dir, "baselines")
        os.makedirs(self.baseline_dir, exist_ok=True)
        for measure_name in self.measures: os.makedirs(os.path.join(self.output_dir, measure_name), exist_ok=True)

    def baseline_path(self, measure_name: str) -> str:
        filename = (
            f"{self.dataset_name}_{self.trajectory_count_label}_"
            f"{measure_name}_original_vs_original_"
            f"pairs_{self.max_pairs}.csv"
        )

        return os.path.join(self.baseline_dir, filename)

    def compute_or_load_original_baseline(self, measure_name, measure):
        baseline_path = self.baseline_path(measure_name)

        if os.path.exists(baseline_path):
            print(f"Loading cached O-O baseline: {baseline_path}")
            df = pd.read_csv(baseline_path)

            # Rewrite metadata so the baseline can be included in the current
            # DP-method/epsilon output file.
            df["epsilon"] = self.epsilon
            df["epsilon_label"] = self.epi_label
            df["dp_model"] = self.dp_model
            df["trajectory_count_label"] = self.trajectory_count_label
            df["dataset_name"] = self.dataset_name
            df["length_group"] = "all"

            return df.to_dict("records")

        print(f"Computing O-O baseline for {measure_name}...")
        pairs = self.sample_pairs(self.original, self.original, same_dataset=True)

        rows = self.compute_scores_no_progress(
            measure_name=measure_name,
            measure=measure,
            pairs=pairs,
            comparison_name="original_vs_original",
        )

        baseline_df = pd.DataFrame(rows)

        # Save with neutral metadata. It will be rewritten when loaded.
        baseline_df.to_csv(baseline_path, index=False)
        print(f"Saved O-O baseline: {baseline_path}")

        return rows


    def measure_path(self, measure_name: str, result_type: str) -> str:
        filename = f"{self.file_stub}.{result_type}.csv"
        return os.path.join(self.output_dir, measure_name, filename)

    def summary_path(self, result_type: str) -> str:
        filename = f"{self.file_stub}.{result_type}.csv"
        return os.path.join(self.output_dir, "summaries", filename)

    def sample_pairs(self, left, right, same_dataset=False):
        if same_dataset:
            n = len(left)
            all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        else:
            all_pairs = [(i, j) for i in range(len(left)) for j in range(len(right))]

        if len(all_pairs) > self.max_pairs:
            all_pairs = random.sample(all_pairs, self.max_pairs)

        return [(left[i], right[j]) for i, j in all_pairs]

    def compute_scores_no_progress(self, measure_name, measure, pairs, comparison_name, length_group="all"):
        rows = []

        for t1, t2 in tqdm(
                pairs,
                desc=f"{measure_name} {comparison_name}",
                leave=False,
            ):
            rows.append({
                "measure": measure_name,
                "comparison": comparison_name,
                "epsilon": self.epsilon,
                "epsilon_label": self.epi_label,
                "dp_model": self.dp_model,
                "trajectory_count_label": self.trajectory_count_label,
                "dataset_name": self.dataset_name,
                "length_group": length_group,
                "traj1_dataset": t1.dataset,
                "traj2_dataset": t2.dataset,
                "traj1": t1.traj_id,
                "traj2": t2.traj_id,
                "score": measure.compute(t1, t2, self.roadmap),
                "traj1_length_m": t1.length(self.roadmap),
                "traj2_length_m": t2.length(self.roadmap),
            })

        return rows

    @staticmethod
    def summarize(df):
        if df.empty:
            return pd.DataFrame()

        return df.groupby([
            "measure",
            "comparison",
            "epsilon",
            "epsilon_label",
            "dp_model",
            "trajectory_count_label",
            "dataset_name",
            "length_group",
        ], dropna=False)["score"].agg([
            "count",
            "mean",
            "std",
            "min",
            "median",
            "max",
        ]).reset_index()

    def run_distribution_comparisons(self):
        all_measure_summaries = []
        measure_items = list(self.measures.items())

        for measure_name, measure in tqdm(measure_items, desc="Distribution measures"):
            rows = []

            # O-O is independent of the DP method and epsilon, so cache it.
            rows.extend(
                self.compute_or_load_original_baseline(
                    measure_name=measure_name,
                    measure=measure,
                )
            )

            comparison_specs = [
                ("original_vs_synthetic", self.sample_pairs(self.original, self.synthetic, same_dataset=False)),
                ("synthetic_vs_synthetic", self.sample_pairs(self.synthetic, self.synthetic, same_dataset=True)),
            ]

            for comparison_name, pairs in tqdm(
                    comparison_specs,
                    desc=f"{measure_name} distribution comparisons",
                    leave=False,
            ):
                rows.extend(
                    self.compute_scores_no_progress(
                        measure_name,
                        measure,
                        pairs,
                        comparison_name,
                    )
                )

            df = pd.DataFrame(rows)

            raw_path = self.measure_path(measure_name, "distribution")
            df.to_csv(raw_path, index=False)
            print(f"Saved: {raw_path}")

            summary = self.summarize(df)
            summary_path = self.measure_path(measure_name, "summary")
            summary.to_csv(summary_path, index=False)
            print(f"Saved: {summary_path}")

            all_measure_summaries.append(summary)

        if all_measure_summaries:
            combined = pd.concat(all_measure_summaries, ignore_index=True)
            combined_path = self.summary_path("all_measures_distribution_summary")
            combined.to_csv(combined_path, index=False)
            print(f"Saved: {combined_path}")

    def run_stratified_original_synthetic(self):
        original_groups = assign_trip_length_groups(self.original, roadmap=self.roadmap)
        synthetic_groups = assign_trip_length_groups(self.synthetic, roadmap=self.roadmap)

        all_measure_summaries = []
        measure_items = list(self.measures.items())

        for measure_name, measure in tqdm(measure_items, desc="Stratified measures"):
            rows = []

            for group in tqdm(TRIP_GROUPS, desc=f"{measure_name} trip groups", leave=False):
                original_ids = set(
                    original_groups[original_groups["length_group"] == group]["traj_id"].tolist()
                )
                synthetic_ids = set(
                    synthetic_groups[synthetic_groups["length_group"] == group]["traj_id"].tolist()
                )

                left = [t for t in self.original if t.traj_id in original_ids]
                right = [t for t in self.synthetic if t.traj_id in synthetic_ids]

                if not left or not right:
                    continue

                pairs = self.sample_pairs(left, right, same_dataset=False)
                rows.extend(
                    self.compute_scores_no_progress(
                        measure_name,
                        measure,
                        pairs,
                        comparison_name="original_vs_synthetic",
                        length_group=group,
                    )
                )

            df = pd.DataFrame(rows)

            raw_path = self.measure_path(measure_name, "stratified")
            df.to_csv(raw_path, index=False)
            print(f"Saved: {raw_path}")

            summary = self.summarize(df)
            strat_summary_path = self.measure_path(measure_name, "stratified_summary")
            summary.to_csv(strat_summary_path, index=False)
            print(f"Saved: {strat_summary_path}")

            all_measure_summaries.append(summary)

        if all_measure_summaries:
            combined = pd.concat(all_measure_summaries, ignore_index=True)
            combined_path = self.summary_path("all_measures_stratified_summary")
            combined.to_csv(combined_path, index=False)
            print(f"Saved: {combined_path}")