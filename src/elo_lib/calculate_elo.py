import json
import math
import os

import numpy as np
import pandas as pd

from elo_lib.utils import (
    LATEST_ELOS_FN,
    RESULTS_ELOS_FN,
    clean_name,
    expected_result,
    revert_current_elo_to_mean,
)

# followed the steps here https://grant592.github.io/elo-ratings/
# got a lot of pointers from 538
# https://fivethirtyeight.com/methodology/how-our-nhl-predictions-work/
current_season = None


def k_value() -> int:
    """
    weight matches more if stakes are higher. based on trial and error
    """
    # 6 is what 538 uses for NHL
    # https://fivethirtyeight.com/methodology/how-our-nhl-predictions-work/
    k = 6

    # TODO: explore if k should be different for playoffs
    # if fixture_type == 'playoffs':
    #     k = 15
    return k


def actual_result(goals_home: int, goals_away: int) -> [float, float]:
    """
    returns points each team won as [<home team's points>, <away team's
    points>]. 1 for winning, .5 each for tying
    """
    if goals_home < goals_away:
        return [0, 1]
    if goals_home > goals_away:
        return [1, 0]
    elif goals_home == goals_away:
        return [0.5, 0.5]


def calculate_movm(goals_home: int, goals_away: int):
    """
    calculates margin of victory multiplyer. Based on 538's https://fivethirtyeight.com/methodology/
    how-our-nhl-predictions-work/
    """
    mov = abs(goals_home - goals_away)

    return 0.6686 * math.log(mov) + 0.8048


# TODO: Consdier adding this per 538
# https://fivethirtyeight.com/methodology/how-our-nhl-predictions-work/
# def calculate_autocorrelation_adjustment():
#     autocorrelation_adjustment = 2.05 / (WinnerEloDiff * 0.001 + 2.05)

#     return autocorrelation_adjustment


def calculate_elo(
    elo_home: int,
    elo_away: int,
    expected_win_home,
    expected_win_away,
    goals_home: int,
    goals_away: int,
) -> [int, int]:
    """
    calculate the new elos from one fixture
    """
    k = k_value()
    actual_win_home, actual_win_away = actual_result(goals_home, goals_away)
    movm = calculate_movm(goals_home, goals_away)

    elo_new_home = elo_home + k * movm * (actual_win_home - expected_win_home)
    elo_new_away = elo_away + k * movm * (actual_win_away - expected_win_away)

    return [int(np.round(elo_new_home)), int(np.round(elo_new_away))]


def handle_row(row, current_elo: dict):
    """
    Get current elos for teams. Calculate elo changes from one fixture. Save those results and save
    new currenty elo.
    """
    # skip games that don't have scores yet
    if "Final" not in row["time"]:
        return row

    home = row["home_team"]
    away = row["away_team"]

    # in case these are new teams
    if home not in current_elo["teams"]:
        current_elo["teams"][home] = 1300

    if away not in current_elo["teams"]:
        current_elo["teams"][away] = 1300

    # if season changes revert to mean and update season
    if row["season"] > current_elo["current_season"]:
        current_elo = revert_current_elo_to_mean(current_elo, row["season"])

    elif row["season"] < current_elo["current_season"]:
        raise Exception("Games out of order.")

    start_elo_home = current_elo["teams"][home]
    start_elo_away = current_elo["teams"][away]

    # how many times out of 100 would each team win
    expected_win_home, expected_win_away = expected_result(start_elo_home, start_elo_away)

    elo_new_home, elo_new_away = calculate_elo(
        start_elo_home,
        start_elo_away,
        expected_win_home,
        expected_win_away,
        row["home_score"],
        row["away_score"],
    )

    current_elo["teams"][home] = elo_new_home
    current_elo["teams"][away] = elo_new_away

    row["elo_after_home"] = elo_new_home
    row["elo_after_away"] = elo_new_away

    row["elo_before_home"] = start_elo_home
    row["elo_before_away"] = start_elo_away

    row["expected_win_home"] = expected_win_home
    row["expected_win_away"] = expected_win_away

    # update date of current elo to date of latest game, ie this row
    current_elo["date"] = row["date"].strftime("%Y-%m-%d")
    return row


def structure_chartable_df(output_df: pd.DataFrame) -> pd.DataFrame:
    # make df with all "after" elos over time so it's easier to work with

    filtered_df = output_df[output_df["time"].str.contains("Final")]
    after_elos_home_df = filtered_df[
        [
            "date",
            "home_team",
            "elo_after_home",
        ]
    ].rename(columns={"home_team": "team", "elo_after_home": "elo"})
    after_elos_away_df = filtered_df[
        [
            "date",
            "away_team",
            "elo_after_away",
        ]
    ].rename(columns={"away_team": "team", "elo_after_away": "elo"})
    after_elos_all = pd.concat([after_elos_home_df, after_elos_away_df])
    after_elos_all = after_elos_all.sort_values("date")
    return after_elos_all


def get_earliest_season(input_data_df) -> int:
    """
    Takes df of all results and returns the earliest season it finds.
    """
    input_data_df = input_data_df.sort_values("date")
    return input_data_df["season"].iloc[0]


def handle(league):
    # the running "current elo". Save it as a file well at the end for the front end?
    current_elo = {"date": None, "teams": dict()}
    output_path = os.path.join(league.elos_output_path, RESULTS_ELOS_FN)
    output_path_latest_elos = os.path.join(league.elos_output_path, LATEST_ELOS_FN)
    input_path = os.path.join(league.clean_output_path, "league_all_results.csv")
    input_data_df = pd.read_csv(input_path)
    input_data_df["date"] = pd.to_datetime(input_data_df.date)

    # sort by data just to be sure
    input_data_df = input_data_df.sort_values("date")

    input_data_df["home_team"] = input_data_df["home_team"].apply(clean_name)
    input_data_df["away_team"] = input_data_df["away_team"].apply(clean_name)

    # make empty columns for new data
    input_data_df["elo_after_home"] = None
    input_data_df["elo_after_away"] = None
    input_data_df["elo_before_home"] = None
    input_data_df["elo_before_away"] = None
    input_data_df["expected_win_home"] = None
    input_data_df["expected_win_away"] = None

    current_elo["current_season"] = get_earliest_season(input_data_df)

    output_df = input_data_df.apply(handle_row, args=(current_elo,), axis=1)

    output_df.to_csv(os.path.join(output_path), index=False)

    # save latest elos
    with open(output_path_latest_elos, "w") as f:
        json.dump(current_elo, f)

    print(output_path)
    # total_elo = 0
    # for key in current_elo.keys():
    #     total_elo += current_elo[key]

    # print(f"average final elo is 1300: {total_elo / 6}")
