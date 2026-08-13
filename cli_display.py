from mazegen import MazeGenerator, MazeGeneratorError, SolverError, solve_bfs
from mazegen.mazegen_types import Coordinate, MazeGrid, Wall, WALL_DELTA
from config_parse import MazeConfig
from output_maze_writer import OutputWriterError, output_maze_writer


# Reverse of WALL_LETTER: turn a solution_path letter back into a (dx, dy)
# step, so we can walk the path and mark which cells it passes through.
LETTER_DELTA: dict[str, Coordinate] = {
    "N": WALL_DELTA[Wall.N],  # "N" move north, which is (0, -1) in (dx, dy)
    "E": WALL_DELTA[Wall.E],  # "E" move east, which is (1, 0) in (dx, dy)
    "S": WALL_DELTA[Wall.S],  # "S" move south, which is (0, 1) in (dx, dy)
    "W": WALL_DELTA[Wall.W]   # "W" move west, which is (-1, 0) in (dx, dy)
}


WALL_COLOURS: list[str] = [
    "\033[0m",   # default
    "\033[31m",  # red
    "\033[33m",  # yellow
    "\033[34m",  # blue
    "\033[35m",  # magenta
    "\033[36m",  # cyan
]
RESET = "\033[0m"

ENTRY_CHAR = "E"
EXIT_CHAR = "X"
PATH_CHAR = "■"
PATH_COLOUR = "\033[92m"

PATTERN_CHAR = "█"
PATTERN_COLOUR = "\033[93m"


def path_cells(entry: Coordinate, solution_path: str) -> set[Coordinate]:
    """
    Walks solution_path from entry, returning every cell it visits.
    entry: (x, y) starting coordinate.
    solution_path: string of N/E/S/W letters, as returned by solve_bfs.
    Returns: set of (x, y) coordinates the path passes through,
    including entry itself.
    """
    x, y = entry
    cells = {(x, y)}
    for letter in solution_path:
        dx, dy = LETTER_DELTA[letter]
        x, y = x + dx, y + dy
        cells.add((x, y))
    return cells


def draw_maze(
    grid: MazeGrid,
    entry: Coordinate,
    exit_: Coordinate,
    solution_path: str,
    show_path: bool,
    colour_rot: int,
    pattern_cells: set[Coordinate]
) -> str:
    """
    Renders the maze as an ASCII grid.
    grid: Maze grid (MazeGrid), indexed as grid[y][x].
    entry: (x, y) of the entry cell, marked 'E'.
    exit_: (x, y) of the exit cell, marked 'X'.
    solution_path: N/E/S/W letters from solve_bfs; only used if show_path.
    show_path: if True, overlay the solution path with a coloured block.
    colour_rot: index into WALL_COLOURS used to colour the wall characters.
    pattern_cells: Coordinates of the hidden '42' pattern cells, marked
    with a coloured block so the pattern stands out.
    returns: str: multi-line ASCII rendering of the maze, ready to print.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    colour = WALL_COLOURS[colour_rot % len(WALL_COLOURS)]

    visited = path_cells(entry, solution_path) \
        if show_path and solution_path else set()

    def horizont_wall(open_: bool) -> str:
        """Horizontal wall segment: '---' line if closed, blank if open."""
        return "   " if open_ else f"{colour}---{RESET}"

    def vertical_wall(open_: bool) -> str:
        """Vertical wall character: three spaces if open, pipebar if closed."""
        return " " if open_ else f"{colour}|{RESET}"

    lines: list[str] = []

    # Top border: every cell's own north wall.
    top = f"{colour}+{RESET}"
    for x in range(width):
        wall = grid[0][x]
        top += horizont_wall(not (wall & Wall.N)) + f"{colour}+{RESET}"
    lines.append(top)

    for y in range(height):
        row = ""
        for x in range(width):
            wall = grid[y][x]
            row += vertical_wall(not (wall & Wall.W))  # right border of cell
            if (x, y) == entry:
                cell_char = ENTRY_CHAR
            elif (x, y) == exit_:
                cell_char = EXIT_CHAR
            elif (x, y) in pattern_cells:
                cell_char = f"{PATTERN_COLOUR}{PATTERN_CHAR}"
            elif (x, y) in visited:
                cell_char = f"{PATH_COLOUR}{PATH_CHAR}{RESET}"
            else:
                cell_char = " "
            row += f" {cell_char} "

        # right border of the row: east wall of the last cell.
        east_wall = grid[y][width - 1] if width else 0
        row += vertical_wall(not (east_wall & Wall.E))
        lines.append(row)

        # bottom border of this row: every cell's own south wall.
        bottom = f"{colour}+{RESET}"
        for x in range(width):
            wall = grid[y][x]
            bottom += horizont_wall(not (wall & Wall.S)) + f"{colour}+{RESET}"
        lines.append(bottom)

    return "\n".join(lines)


def cli_display(config: MazeConfig) -> int:
    """Interactive menu loop: generate/re-solve, toggle solution
    display, cycle wall colour, or quit. On quit, writes the current
    maze (grid + solution_path) to config.output_file.
    config: Parsed MazeConfig, used for width/height/seed/perfect/
    entry/exit_ on every (re)generation, and output_file on quit.
    Returns: int: Exit code (0 on success, 1 on error)."""
    generator = MazeGenerator(
        width=config.width, height=config.height, seed=config.seed
    )
    solution_path = ""
    show_path = False
    colour_rot = 0

    def regenerate() -> bool:
        """(Re)generates the maze and re-solves it, so solution_path
        is never stale relative to the current grid.
        Returns: bool: True on success, False if generation or solving
        failed (error already printed)."""
        nonlocal solution_path
        try:
            generator.generate(
                perfect=config.perfect, entry=config.entry, exit_=config.exit_
            )
        except MazeGeneratorError as err:
            print(f"Error generating maze: {err}")
            return False
        try:
            solution_path = solve_bfs(
                generator.grid, entry=config.entry, exit_=config.exit_
            )
        except SolverError as err:
            print(f"Error solving maze: {err}")
            return False
        return True

    if not regenerate():
        return 1

    while True:
        print()
        print(draw_maze(
            generator.grid, config.entry, config.exit_,
            solution_path, show_path, colour_rot, generator.pattern_cells,
        ))
        print()
        print('┌─ A-Maze-ing ──────────────────────┐')
        print('│  1. Re-generate a new maze        │')
        print('│  2. Show / Hide the shortest path │')
        print('│  3. Rotate the wall colours       │')
        print('│  4. Quit                          │')
        print('└───────────────────────────────────┘')

        choice = input("Choice(1-4)? >").strip()

        if choice == '1':
            regenerate()
        elif choice == '2':
            show_path = not show_path
        elif choice == '3':
            colour_rot = (colour_rot + 1) % len(WALL_COLOURS)
        elif choice == '4':
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
            print("Goodbye!")
            return 0
        else:
            print("Invalid choice")
