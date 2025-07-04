import click
import cv2 as cv
import numpy as np
import os

from gaps import utils
from gaps.genetic_algorithm import GeneticAlgorithm
from gaps.size_detector import SizeDetector
from gaps.individual import FitnessType

DEFAULT_GENERATIONS: int = 20
DEFAULT_POPULATION: int = 200

MIN_PIECE_SIZE: int = 32
MAX_PIECE_SIZE: int = 128


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "ignore_unknown_options": True,
    }
)
def cli() -> None:
    """Solve or create puzzles with square pieces."""


def _validate_piece_size(_context: click.Context, _param: str, value: int) -> int:
    if value < MIN_PIECE_SIZE:
        raise click.BadParameter(f"Minimum piece size is {MIN_PIECE_SIZE} pixels")

    if value > MAX_PIECE_SIZE:
        raise click.BadParameter(f"Maximum piece size is {MAX_PIECE_SIZE} pixels")

    return value


def _validate_positive_integer(_context: click.Context, _param: str, value: int) -> int:
    if value <= 0:
        raise click.BadParameter("Should be a positive integer.")

    return value


@click.command()
@click.argument("puzzle", type=click.Path(exists=True, readable=True))
@click.option(
    "-s",
    "--size",
    type=int,
    help="Size of single square puzzle piece in pixels. Autodetected if not specified.",
)
@click.option(
    "-g",
    "--generations",
    type=int,
    show_default=True,
    default=DEFAULT_GENERATIONS,
    callback=_validate_positive_integer,
    help="The number of generations for genetic algorithm.",
)
@click.option(
    "-p",
    "--population",
    type=int,
    show_default=True,
    default=DEFAULT_POPULATION,
    callback=_validate_positive_integer,
    help="The size of the initial population for genetic algorithm.",
)
@click.option(
    "-ft",
    "--fitness_type",
    type=int,
    show_default=True,
    default=1,
)
@click.option(
    "-d",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="If enabled, shows the best individual after each generation.",
)
def run(
    puzzle: str,
    size: int,
    generations: int,
    population: int,
    fitness_type : int,
    debug: bool,
) -> None:
    """Run puzzle solver.

    \b
    PUZZLE is the input puzzle image with square pieces.
    SOLUTION is the output image file for solved puzzle.

    Examples:

    $ gaps run puzzle.jpg --size=32 --generations=100 --population=1000

    """

    input_puzzle = cv.imread(puzzle)
    puzzle_name = os.path.splitext(os.path.basename(puzzle))[0]

    if size is None:
        detector = SizeDetector(input_puzzle)
        size = detector.detect()

    

    click.echo(f"Population: {population}")
    click.echo(f"Generations: {generations}")
    click.echo(f"Piece size: {size}")

    solution_basename = f'{puzzle_name}_p{population}_g{generations}_s{size}_ft{fitness_type}'
    solution_path = os.path.join("solutions",solution_basename)

    os.makedirs(solution_path,exist_ok=True)

    ga = GeneticAlgorithm(
        image=input_puzzle,
        piece_size=size,
        population_size=population,
        generations=generations,
        fitness_type=FitnessType(fitness_type),
    )

    result, fittest_list = ga.start_evolution(debug)
    output_image = result.to_image()

    cv.imwrite(os.path.join(solution_path,solution_basename + '_solution.jpg'), output_image)

    for i,f in enumerate(fittest_list):
        img = f.to_image()
        cv.imwrite(os.path.join(solution_path,solution_basename + f'_{i}.jpg'), img)

    click.echo("Puzzle solved")


@click.command()
@click.argument("image", type=click.Path(exists=True, readable=True))
@click.argument("puzzle", type=click.Path(writable=True))
@click.option(
    "-s",
    "--size",
    type=int,
    show_default=True,
    default=MAX_PIECE_SIZE,
    callback=_validate_piece_size,
    help="Size of single square puzzle piece in pixels.",
)
def create(image: str, puzzle: str, size: int) -> None:
    """Create jigsaw puzzle with square pieces.

    \b
    IMAGE is the input image file to create puzzle.
    PUZZLE is the output puzzle image with square pieces.

    Examples:

    $ gaps create image.jpg puzzle.jpg --size=32

    """

    input_image = cv.imread(image)
    pieces, rows, columns = utils.flatten_image(input_image, size)

    # Randomize pieces in order to make puzzle
    np.random.shuffle(pieces)

    # Create puzzle by stacking pieces
    output_image = utils.assemble_image(pieces, rows, columns)

    cv.imwrite(puzzle, output_image)

    click.echo(f"\nCreated puzzle with {len(pieces)} pieces")


cli.add_command(run, name="run")
cli.add_command(create, name="create")

if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
