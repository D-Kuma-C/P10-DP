import numpy as np
import pandas as pd
from tqdm.auto import tqdm


def reidentification_prob(
    synthetic_data,
    original_data,
    known_locations,
    number_of_test_users,
    random_state=0,
    show_progress=True,
):
    """
    Calculate the reidentification probability.

    Parameters
    ----------
    synthetic_data: pandas.DataFrame
        Synthetic data.
    original_data: pandas.DataFrame
        Original data.
    n: int
        Number of known locations.
    number_of_test_users: int
        Number of original users to test.
    random_state: int
        Random seed.
    show_progress: bool
        If True, show progress bars and stage messages.

    Returns
    -------
    score: float
    """

    if show_progress:
        tqdm.pandas()
        print("Sampling users and known times...")

    cols = original_data.columns
    sequence_len = original_data.shape[1]

    # sample users as initial information
    test_users = original_data.sample(
        number_of_test_users,
        random_state=random_state,
    )

    rng = np.random.default_rng(random_state)
    sample_sequence_time = rng.integers(
        sequence_len,
        size=(number_of_test_users, known_locations),
    )

    # sample times in which we know the locations for each user
    sample_sequence_time = pd.melt(
        pd.DataFrame(sample_sequence_time, index=test_users.index).reset_index(),
        id_vars=["User"],
        value_name="time",
    ).drop(["variable"], axis=1)

    sample_sequence_time["time"] = sample_sequence_time["time"].apply(
        lambda x: cols[x]
    )

    test_users = pd.melt(
        test_users.reset_index(),
        id_vars=["User"],
        var_name="time",
        value_name="location",
    )

    # join to get for each user the time and location that were sampled
    if show_progress:
        print("Merging sampled known locations...")

    test_users_known_locations = test_users.merge(
        sample_sequence_time,
        on=["User", "time"],
    )

    # find the synthetic users with similar location in the times sampled
    if show_progress:
        print("Melting synthetic data...")

    synthetic_data = synthetic_data.copy()
    synthetic_data.index.rename("synth_user", inplace=True)

    synthetic_melted_data = pd.melt(
        synthetic_data.reset_index(),
        id_vars="synth_user",
        var_name="time",
        value_name="synth_location",
    )

    if show_progress:
        print("Merging known locations with synthetic users...")

    test_users_known_locations_with_synthetic_users = (
        test_users_known_locations.merge(
            synthetic_melted_data,
            on=["time"],
            how="left",
        )
    )

    # Compare known original locations with synthetic locations
    if show_progress:
        print("Comparing known locations with synthetic users...")

        test_users_known_locations_with_synthetic_users["is_same"] = (
            test_users_known_locations_with_synthetic_users.progress_apply(
                lambda x: x.location == x.synth_location,
                axis=1,
            )
        )
    else:
        test_users_known_locations_with_synthetic_users["is_same"] = (
            test_users_known_locations_with_synthetic_users.apply(
                lambda x: x.location == x.synth_location,
                axis=1,
            )
        )

    if show_progress:
        print("Finding best-matching synthetic users...")

    # Average match score for each original user / synthetic user pair
    if show_progress:
        grouped = (
            test_users_known_locations_with_synthetic_users
            .groupby(["User", "synth_user"])
            .is_same
        )

        test_users_known_locations_with_synthetic_users = (
            grouped
            .progress_apply(lambda x: x.mean())
            .reset_index(name="is_same")
        )
    else:
        test_users_known_locations_with_synthetic_users = (
            test_users_known_locations_with_synthetic_users
            .groupby(["User", "synth_user"])
            .is_same
            .mean()
            .reset_index()
        )

    if show_progress:
        print("Finding maximum match score per user...")

    test_users_known_locations_with_synthetic_users["max_same"] = (
        test_users_known_locations_with_synthetic_users
        .groupby("User")
        .is_same
        .transform(lambda x: max(x))
    )

    # keep only users that had the most matches
    if show_progress:
        print("Filtering best-matching synthetic users...")

        best_match_mask = (
            test_users_known_locations_with_synthetic_users
            .progress_apply(
                lambda x: x.is_same == x.max_same,
                axis=1,
            )
        )
    else:
        best_match_mask = (
            test_users_known_locations_with_synthetic_users
            .apply(
                lambda x: x.is_same == x.max_same,
                axis=1,
            )
        )

    test_users_known_locations_with_synthetic_users = (
        test_users_known_locations_with_synthetic_users[
            best_match_mask
            & (test_users_known_locations_with_synthetic_users.max_same > 0.8)
            ]
    )

    # If no synthetic users pass the matching threshold, return 0.
    if test_users_known_locations_with_synthetic_users.empty:
        if show_progress:
            print("No synthetic users passed the matching threshold.")
        return 0.0

    # get the synthetic users entire sequences
    if show_progress:
        print("Retrieving full synthetic sequences for matched users...")

    test_users_known_locations_with_synthetic_users = (
        test_users_known_locations_with_synthetic_users[["User", "synth_user"]]
        .merge(
            synthetic_data.reset_index(),
            on="synth_user",
        )
        .drop(["synth_user"], axis=1)
    )

    test_users_known_locations_with_synthetic_users = pd.melt(
        test_users_known_locations_with_synthetic_users,
        id_vars=["User"],
        var_name="time",
        value_name="synth_location",
    )

    # for each real user get an estimated diary using the synthetic users
    if show_progress:
        print("Estimating diaries from matched synthetic users...")

    grouped = (
        test_users_known_locations_with_synthetic_users
        .groupby(["User", "time"])
        .synth_location
    )

    if show_progress:
        test_users_known_locations_with_synthetic_users = (
            grouped
            .progress_apply(lambda x: x.value_counts().index[0])
            .reset_index()
        )
    else:
        test_users_known_locations_with_synthetic_users = (
            grouped
            .apply(lambda x: x.value_counts().index[0])
            .reset_index()
        )

    # compare the estimated diaries with the real diaries
    if show_progress:
        print("Comparing estimated diaries with real diaries...")

    compare = test_users.merge(
        test_users_known_locations_with_synthetic_users,
        on=["User", "time"],
        how="left",
    )

    if show_progress:
        compare["is_same"] = compare.progress_apply(
            lambda x: 1 if x.location == x.synth_location else 0,
            axis=1,
        )
    else:
        compare["is_same"] = compare.apply(
            lambda x: 1 if x.location == x.synth_location else 0,
            axis=1,
        )

    compare = compare.groupby("User").is_same.mean()

    score = compare.mean()

    return score