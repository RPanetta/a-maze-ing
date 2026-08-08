import random
from mazegen.mazegen_types import MazeGrid, Wall, WALL_DELTA

ALL_WALLS_CLOSED = int(Wall.N | Wall.E | Wall.S | Wall.W)

class MazeGeneratorError(Exception):
    pass


class MazeGenerator:
    """Generates perfect mazes or Pac-Man-style mazes with loops.
    Attributes:
    width: Number of cells along the horizontal axis
    height: Number of cells along the vertical axis
    seed: Seed used for reproducible maze generation
    grid: The resulting maze grid (MazeGrid), indexed as grid[y][x]"""

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        """Initializes the maze generator with the specified maze dimensions.
        Args:
        width: Number of columns (>= 1).
        height: Number of rows (>= 1).
        seed: Optional seed for reproducible generation. If None, a random system seed is used
        Raises:
        MazeGeneratorError: If width or height is not positive"""
        if width < 1 or height < 1:
            raise MazeGeneratorError("width and height must be positive integers")

        self.width: int = width
        self.height: int = height
        self.seed: int | None = seed

        self._rng: random.Random = random.Random(seed)
        self.grid: MazeGrid = self._blank_grid()


    def blank_grid(self) -> MazeGrid:
        """Creates a new grid with all four walls closed in every cell
        Returns:
        MazeGrid: A width x height matrix where each cell is initialized to 15 (0xF)"""
        return [
            [ALL_WALLS_CLOSED for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def neighbors(self, x: int, y: int) -> list[tuple[Wall, int, int]]:
        """Lists the valid neighbors (within the grid) of a cell
        Args:
        x: X-coordinate of the source cell
        y: Y-coordinate of the source cell
        Returns:
        list[tuple[Wall, int, int]]: Tuples containing the wall, x-coordinate,
        and y-coordinate of each neighboring cell within the grid."""

        result: list [tuple[Wall, int, int]] = []
        for wall, (dx, dy) in WALL_DELTA.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                result.append((wall, nx, ny))
        return result
