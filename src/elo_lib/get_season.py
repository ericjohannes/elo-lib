import json
import os
import requests

params = {
    "feed": "modulekit",
    "view": "schedule",
    "location": "homeaway",
    "key": "446521baf8c38984",
    "client_code": "pwhl",
    "site_id": "0",
    "league_id": "1",
    "lang": "en",
    "fmt": "json",
}


def insert_seasonid(season_id: str, url: str) -> str:
    """
    for leagues where the seasonid is part of the url and not a parameter
    """
    return url.replace("<season_id>", season_id)


def drill_down(keys: list[str], data) -> dict:
    """
    For a list of keys, drills into an object to return data at last key.
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def handle(seasonid, league):
    """
    Gets all data for a season based on its id. Gets data from url specified in config object and
    saves it to location specified by config object.

    the `league` object should have several properties:
        `url_contains_id`: bool - tells whether the season id is part of the path in the url
        `param_id

    """
    url = league.url
    if league.url_contains_id:  # ex: nwsl
        url = insert_seasonid(seasonid, url)
    elif league.param_id:  # ex: wphl
        params["season_id"] = seasonid

    r = requests.get(url, params=league.params)
    data = r.json()
    fn = f"season_{seasonid}.json"
    output_path = os.path.join(league.output_path, fn)
    
    matches = drill_down(league.matches_path, data)
    with open(output_path, "w") as f:
        json.dump(matches, f)
    return output_path
