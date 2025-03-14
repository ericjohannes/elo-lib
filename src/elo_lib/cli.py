import click

from elo_lib.calculate_elo import handle as handle_calculate_elo
from elo_lib.chart_data import handle as handle_chart_data
from elo_lib.chart_elos import create_charts
from elo_lib.clean_seasons import handle as handle_clean_seasons
from elo_lib.get_games import get_games
from elo_lib.get_season import handle as handle_get_season
from elo_lib.revert_elo import revert_elo_file
from elo_lib.upcoming_projection import build_upcoming_projects
from elo_lib.update_elo import update_elo
from elo_lib.utils import League


@click.group()
def cli():
    pass


@click.command()
def hi():
    """Example script."""
    click.echo("Hello World!")


# input for now should be wphl_results_clean_data file
# suggested run like
#  `elolib calculate --input ../data/input/wphl_results_clean_data.csv --output-dir ../data/output`
@click.command()
@click.option(
    "--config",
    default="league.config",
    help="Path to config file containing paths and data about seasons.",
)
def calculate(config):
    """Calulcates Elos and outputs 3 files:
    1. league_all_results_with_elos.csv - file with all fixtures played so far with Elos and
    projections calculated.
    2. league_latest_elos - file with latest calculated Elos for each team and date calculated."""
    league = League(config=config)
    new_file = handle_calculate_elo(league)
    print(new_file)


# run like `elolib projections`
@click.command()
@click.option(
    "--config",
    default="league.config",
    help="Path to config file containing paths and data about seasons.",
)
def projections(config):
    """Builds projections for next 5 fixtures based on latest_elos.json."""
    league = League(config=config)
    new_file = build_upcoming_projects(league)
    print(new_file)


@click.command()
def chart():
    """Creates Elo chart for all teams and seasons."""
    create_charts()


# suggested run like
# `elolib revert --input ../data/output/league_latest_elos.json --output-dir ../data/output`
@click.command()
@click.option(
    "--input", prompt="path/to/file.json", help="File of team Elos to revert to the mean."
)
@click.option(
    "--output-dir", prompt="path/to/dir", help="Directory of where to save reverted Elos."
)
def revert(input, output_dir):
    """Reverts all latest team Elo's to the mean for the start of a new season."""
    new_file = revert_elo_file(input, output_dir)
    click.echo(f"{new_file}")


@click.command()
@click.option(
    "--input", prompt="path/to/file.json", help="Previous file of fixtures, scores and Elos."
)
@click.option(
    "--output-dir", prompt="path/to/dir", help="Directory of where to save new Elo results."
)
def update(input, output_dir):
    """Takes new fixture results from clean results file, input file of last calculated Elos and
    latest Elos for each team. Adds new Elo scores for new played fixtures and saves new latest Elos
     and new file of all fixtures with Elo scores."""
    new_file = update_elo(input, output_dir)
    click.echo(f"{new_file}")


# like elolib chartable --input ../data/output/all_results/wphl_elos_2024-11-24_19:37:35.csv /
# --output-dir ../data/output
@click.command()
@click.option(
    "--config",
    default="league.config",
    help="Path to config file containing paths and data about seasons.",
)
def chartable(config):
    """Creates a json file of each team's Elo over time, suitable for a line chart."""
    league = League(config=config)
    new_file = handle_chart_data(league)
    click.echo(new_file)


@click.command()
@click.option("--season-id", help="ID # of season. 5 = 2025 regular season, etc.")
@click.option("--output-path", prompt="path/to/output", help="Path to save new data to.")
def getgames(season_id, output_path):
    """Gets latest data on games played"""
    new_file = get_games(season_id, output_path)
    click.echo(f"{new_file}")


@click.command()
@click.argument("seasonid")
@click.option(
    "--config",
    default="league.config",
    help="Path to config file containing paths and data about seasons.",
)
@click.option("--output-path", help="Path to save new data to.")
def getseason(seasonid, config, output_path):
    """Gets all data for season with id SEASONID"""
    league = League(config=config, output_path=output_path)
    new_file = handle_get_season(seasonid, league)
    print(new_file)


@click.command()
@click.option(
    "--config",
    default="league.config",
    help="Path to config file containing paths and data about seasons.",
)
def cleandata(config):
    """Combaines all data of seasons into clean csv for analysis."""
    league = League(config=config)
    new_file = handle_clean_seasons(league)
    print(new_file)


cli.add_command(hi)
cli.add_command(calculate)
cli.add_command(projections)
cli.add_command(chart)
cli.add_command(revert)
cli.add_command(update)
cli.add_command(chartable)
cli.add_command(getgames)
cli.add_command(getseason)
cli.add_command(cleandata)
