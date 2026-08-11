import sys
from config_parse import ConfigError, config_parse
from mazegen import MazeGenerator, MazeGeneratorError, SolverError, solve_bfs
from output_maze_writer import OutputWriterError, output_maze_writer


def run(config_path: str) -> int:
    """Runs the complete workflow: read the configuration,
    generate the maze, solve it, and write the output
    config_path: path to the configuration file
    Returns: int: Exit code (0 on success, 1 on error)"""
    try:
        config = config_parse(config_path)
    except ConfigError as err:
        print(f"Error in configuration: {err}")
        return 1

    try:
        generator = MazeGenerator(
            width=config.width, height=config.height, seed=config.seed
        )
        generator.generate(
            perfect=config.perfect, entry=config.entry, exit_=config.exit_
        )
    except MazeGeneratorError as err:
        print(f"Error generating maze: {err}")
        return 1

    try:
        solution_path = solve_bfs(
            generator.grid, entry=config.entry, exit_=config.exit_
        )
    except SolverError as err:
        print(f"Error solving maze: {err}")
        return 1

    try:
        output_maze_writer(
            path=config.output_file,
            grid=generator.grid,
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit_=config.exit_,
            solution_path=solution_path,
        )
    except OutputWriterError as err:
        print(f"Error writing output file: {err}")
        return 1

    print(f"Maze written to '{config.output_file}'")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    sys.exit(run(sys.argv[1]))
