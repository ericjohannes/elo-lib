import json
import math
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

RESULTS_ELOS_FN = "league_all_results_with_elos.csv"
CHART_DATA_FN = "chartable_wphl_elos.json"
LATEST_ELOS_FN = "latest_elos.json"
GAME_PROJECTIONS_FN = "game_projections.json"


def revert_elo_to_mean(season_ending_elo: int) -> int:
    """
    To account for reversion to mean, new players, coach etc. Bring an Elo 1/3 back to 1300
    """

    difference = season_ending_elo - 1300
    new_elo = season_ending_elo - (difference / 3)
    return int(np.round(new_elo))


def revert_current_elo_to_mean(current_elo: dict, current_season: int):
    """
    Takes current elo dict and reverts all elo to the mean
    """
    for team, elo in current_elo["teams"].items():
        current_elo["teams"][team] = revert_elo_to_mean(elo)
    current_elo["current_season"] = current_season
    return current_elo


def time_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


def expected_result(elo_home: int, elo_away: int) -> List[np.float64]:
    # 538 uses 50 for nfl https://fivethirtyeight.com/methodology/how-our-nhl-predictions-work/
    HOME_ADVANTAGE = 50

    # TODO: see if playoff adjustment of 1.25 should go here per
    # https://fivethirtyeight.com/methodology/how-our-nhl-predictions-work/
    rating_home = 10 ** ((elo_home + HOME_ADVANTAGE) / 400)
    rating_away = 10 ** (elo_away / 400)
    expected_score_home = rating_home / (rating_home + rating_away)

    return [expected_score_home, 1 - expected_score_home]


def clean_name(name: str) -> str:
    name = name.strip().replace(" ", "_").lower()
    if name == "montreal":
        name = standardize_montreal(name)
    return name


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


def actual_result(goals_home: int, goals_away: int) -> List[float]:
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


def calculate_elo(
    elo_home: int,
    elo_away: int,
    expected_win_home,
    expected_win_away,
    goals_home: int,
    goals_away: int,
) -> List[int]:
    """
    calculate the new elos from one fixture
    """
    k = k_value()
    actual_win_home, actual_win_away = actual_result(goals_home, goals_away)
    movm = calculate_movm(goals_home, goals_away)

    elo_new_home = elo_home + k * movm * (actual_win_home - expected_win_home)
    elo_new_away = elo_away + k * movm * (actual_win_away - expected_win_away)

    return [int(np.round(elo_new_home)), int(np.round(elo_new_away))]


def standardize_montreal(team: str) -> str:
    """
    adds accent to montréal
    """
    return team.replace("e", "é")


def structure_chartable_df(output_df: pd.DataFrame) -> pd.DataFrame:
    # make df with all "after" elos over time so it's easier to work with

    filtered_df = output_df[output_df["time"].str.lower().str.contains("final")]
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
    after_elos_all = pd.concat([after_elos_home_df, after_elos_away_df], ignore_index=True)

    after_elos_all = after_elos_all.sort_values("date")

    pivoted_elo_df = after_elos_all.pivot(index="date", columns="team")
    pivoted_elo_df.columns = [y for x, y in pivoted_elo_df.columns]
    return pivoted_elo_df


def drop_nans(input_dict: dict) -> dict:
    """
    drop key-values pairs if value is NaN two levels in
    """
    input_dict.items()
    output_dict = {
        k: {k1: v1 for k1, v1 in sub_dict.items() if not math.isnan(v1)}
        for k, sub_dict in input_dict.items()
    }
    return output_dict


class League:
    """
    Class to hold configuration of a leuage.
    """

    def __init__(self, config, output_path=None):
        self.configpath = config
        # first get values from config file
        self.read_config(config)
        # overright with ones from command line
        if output_path:
            self.output_path = output_path
        self.valid = self.validate_config()

    def read_config(self, config_fp: str) -> dict:
        """
        reads in the config data and returns it as a dict
        """
        with open(config_fp, "r") as f:
            config_data = json.load(f)
            for k, v in config_data.items():
                setattr(self, k, v)

    def validate_config(self):
        required_properties = ["output_path"]
        for property in required_properties:
            if not hasattr(self, property):
                raise Exception(f"{property} must be defined from command line or in config")
        return True
