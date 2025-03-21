import click

from elo_lib.calculate_elo import handle as handle_calculate_elo
from elo_lib.chart_data import handle as handle_chart_data
from elo_lib.clean_seasons import handle as handle_clean_seasons
from elo_lib.get_season import handle as handle_get_season
from elo_lib.upcoming_projection import handle as handle_projection
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
    new_file = handle_projection(league)
    print(new_file)


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
@click.option("--output-path", help="Path to save new data to.")
def getallseasons(config, output_path):
    """Gets all data for all seasons for this league."""
    league = League(config=config, output_path=output_path)
    for season in league.seasons:
        new_file = handle_get_season(season["season_id"], league)
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
cli.add_command(chartable)
cli.add_command(getseason)
cli.add_command(getallseasons)
cli.add_command(cleandata)
