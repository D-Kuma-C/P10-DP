import numpy as np
from math import log
from typing import Hashable, List, Dict, Any, Optional


Trajectory = List[Hashable]


def calc_kl(p: List[float], q: List[float]) -> float:
    """
    KL divergence.

    This assumes the Java calcKL skips terms where p_i == 0.
    Uses natural log unless your Java calcKL uses a different base.
    """
    total = 0.0

    for pi, qi in zip(p, q):
        if pi == 0:
            continue
        if qi == 0:
            raise ValueError("KL undefined when q_i is 0 and p_i > 0")
        total += pi * log(pi / qi)

    return total


def calc_jsd(orig_prob: List[float], syn_prob: List[float]) -> float:
    """
    Direct translation of Java calcJSD.
    """
    if len(orig_prob) != len(syn_prob):
        raise ValueError("Probability vectors must have the same length")

    avg_prob = [
        (orig_prob[i] + syn_prob[i]) / 2.0
        for i in range(len(orig_prob))
    ]

    return 0.5 * calc_kl(orig_prob, avg_prob) + 0.5 * calc_kl(syn_prob, avg_prob)


def get_nth_densest_cell(
    orig_trajs: List[Trajectory],
    grid_cells: List[Hashable],
    n: int,
) -> Hashable:
    """
    Equivalent to Main.getNthDensestCell(origDBgrid, grid, N).

    Counts every visit to every cell. Includes zero-count grid cells.
    n is 1-based.
    """
    if n < 1:
        raise ValueError("n must be >= 1")

    if n > len(grid_cells):
        raise ValueError(f"n={n} exceeds number of grid cells={len(grid_cells)}")

    cell_densities = {cell: 0 for cell in grid_cells}

    for traj in orig_trajs:
        for cell in traj:
            if cell not in cell_densities:
                raise ValueError(f"Trajectory contains cell {cell!r} not found in grid_cells")
            cell_densities[cell] += 1

    sorted_cells = sorted(
        cell_densities.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return sorted_cells[n - 1][0]


def get_trip_probs_as_list(
    trajs: List[Trajectory],
    grid_cells: List[Hashable],
    priv_budget: Optional[float] = None,
    add_laplace_noise: bool = False,
    rng: Optional[np.random.Generator] = None,
) -> List[float]:
    """
    Python version of TripDistribution(...).getTripProbsAsList().

    It builds a flattened grid_cells x grid_cells origin-destination matrix.

    If add_laplace_noise=True:
        noisy_count = count + Laplace(0, 1 / priv_budget)
        noisy_count is clipped at 0
        noisy_count is rounded to nearest integer

    If add_laplace_noise=False:
        the raw trip counts are normalized directly.
    """
    if rng is None:
        rng = np.random.default_rng()

    if add_laplace_noise and (priv_budget is None or priv_budget <= 0):
        raise ValueError("priv_budget must be positive when add_laplace_noise=True")

    cell_to_index = {cell: idx for idx, cell in enumerate(grid_cells)}
    size = len(grid_cells)

    trip_counts = np.zeros((size, size), dtype=float)

    for traj in trajs:
        if len(traj) == 0:
            continue

        start_cell = traj[0]
        end_cell = traj[-1]

        if start_cell not in cell_to_index:
            raise ValueError(f"Unknown start cell {start_cell!r}")
        if end_cell not in cell_to_index:
            raise ValueError(f"Unknown end cell {end_cell!r}")

        i = cell_to_index[start_cell]
        j = cell_to_index[end_cell]
        trip_counts[i, j] += 1.0

    if add_laplace_noise:
        scale = 1.0 / float(priv_budget)
        noise = rng.laplace(loc=0.0, scale=scale, size=(size, size))

        trip_counts = trip_counts + noise
        trip_counts = np.maximum(trip_counts, 0.0)
        trip_counts = np.round(trip_counts)

    total = trip_counts.sum()

    if total == 0:
        return [0.0 for _ in range(size * size)]

    trip_probs = trip_counts / total

    return trip_probs.flatten().tolist()


def get_markov_list(
    trajs: List[Trajectory],
    grid_cells: List[Hashable],
) -> List[float]:
    """
    Python version of Main.getMarkovList.

    Builds a flattened grid_cells x grid_cells transition probability matrix,
    normalized globally by the total number of transitions.
    """
    cell_to_index = {cell: idx for idx, cell in enumerate(grid_cells)}
    size = len(grid_cells)

    actual_counts = np.zeros((size, size), dtype=float)
    sum_all = 0.0

    for traj in trajs:
        for k in range(len(traj) - 1):
            this_cell = traj[k]
            next_cell = traj[k + 1]

            if this_cell not in cell_to_index:
                raise ValueError(f"Unknown this cell {this_cell!r}")
            if next_cell not in cell_to_index:
                raise ValueError(f"Unknown next cell {next_cell!r}")

            i = cell_to_index[this_cell]
            j = cell_to_index[next_cell]

            actual_counts[i, j] += 1.0
            sum_all += 1.0

    if sum_all == 0:
        return [0.0 for _ in range(size * size)]

    markov_probs = actual_counts / sum_all

    return markov_probs.flatten().tolist()


def evaluate_bayesian_attack(
    trip_prior: List[float],
    markov_prior: List[float],
    relevant_subset: List[Trajectory],
    grid_cells: List[Hashable],
    vartheta: float,
    posterior_trip_priv_budget: float = 100000.0,
    add_posterior_trip_noise: bool = False,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, Any]:
    """
    Python version of evaluateBayesianAttack.

    Java uses:
        new TripDistribution(relevantSubset, grid, 100000.0)

    In practice, that adds almost no noise. For deterministic scoring,
    keep add_posterior_trip_noise=False.
    """
    trip_posterior = get_trip_probs_as_list(
        trajs=relevant_subset,
        grid_cells=grid_cells,
        priv_budget=posterior_trip_priv_budget,
        add_laplace_noise=add_posterior_trip_noise,
        rng=rng,
    )

    markov_posterior = get_markov_list(
        trajs=relevant_subset,
        grid_cells=grid_cells,
    )

    trip_jsd = calc_jsd(trip_prior, trip_posterior)
    markov_jsd = calc_jsd(markov_prior, markov_posterior)

    return {
        "trip_jsd": trip_jsd,
        "markov_jsd": markov_jsd,
        "trip_passes": trip_jsd <= vartheta,
        "markov_passes": markov_jsd <= vartheta,
        "passes": trip_jsd <= vartheta and markov_jsd <= vartheta,
    }


def bayesian_attack_score_only(
    orig_trajs: List[Trajectory],
    syn_trajs: List[Trajectory],
    grid_cells: List[Hashable],
    vartheta: float = 0.1,
    sensitive_zone: Optional[Hashable] = None,
    nth_densest_cell: int = 10,
    prior_trip_priv_budget: Optional[float] = None,
    add_prior_trip_noise: bool = False,
    posterior_trip_priv_budget: float = 100000.0,
    add_posterior_trip_noise: bool = False,
    random_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Score-only version of AdaTrace Bayesian defense.

    Does not:
      - remove synthetic trajectories
      - generate new synthetic trajectories
      - modify original data
      - modify synthetic data

    Parameters:
      prior_trip_priv_budget:
        In AdaTrace, the original TripPrior comes from:
            new TripDistribution(origDBgrid, grid, budgetDistnWeights[2] * totalEpsilon)
        If you want exact noisy behavior, set this and add_prior_trip_noise=True.

      add_prior_trip_noise:
        False gives deterministic, noise-free comparison.
        True mimics AdaTrace's noisy TripDistribution prior.

      add_posterior_trip_noise:
        Java technically adds noise with budget 100000.0.
        False is recommended for stable scoring.
    """
    rng = np.random.default_rng(random_seed)

    if sensitive_zone is None:
        sensitive_zone = get_nth_densest_cell(
            orig_trajs=orig_trajs,
            grid_cells=grid_cells,
            n=nth_densest_cell,
        )

    trip_prior = get_trip_probs_as_list(
        trajs=orig_trajs,
        grid_cells=grid_cells,
        priv_budget=prior_trip_priv_budget,
        add_laplace_noise=add_prior_trip_noise,
        rng=rng,
    )

    markov_prior = get_markov_list(
        trajs=orig_trajs,
        grid_cells=grid_cells,
    )

    relevant_subset = [
        traj for traj in syn_trajs
        if sensitive_zone in traj
    ]

    if len(relevant_subset) == 0:
        return {
            "sensitive_zone": sensitive_zone,
            "relevant_subset_size": 0,
            "trip_jsd": None,
            "markov_jsd": None,
            "vartheta": vartheta,
            "passes": True,
            "reason": "No synthetic trajectories pass through the sensitive zone.",
        }

    scores = evaluate_bayesian_attack(
        trip_prior=trip_prior,
        markov_prior=markov_prior,
        relevant_subset=relevant_subset,
        grid_cells=grid_cells,
        vartheta=vartheta,
        posterior_trip_priv_budget=posterior_trip_priv_budget,
        add_posterior_trip_noise=add_posterior_trip_noise,
        rng=rng,
    )

    return {
        "sensitive_zone": sensitive_zone,
        "relevant_subset_size": len(relevant_subset),
        "vartheta": vartheta,
        **scores,
    }