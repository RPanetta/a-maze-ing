import random
import sys
from mazegen.mazegen_types import (
    MazeGrid, Wall, WALL_DELTA, WALL_OPPOSITE, Coordinate
)


ALL_WALLS_CLOSED = int(Wall.N | Wall.E | Wall.S | Wall.W)


""""42 pattern (1 = fully-walled cell, 0 = normal cell)
Layout: "4" (3 wide) + gap (1 wide) + "2" (3 wide) = 7 columns, 5 rows"""
PATTERN_42: list[list[int]] = [
    [1, 0, 1,  0,  1, 1, 1],
    [1, 0, 1,  0,  0, 0, 1],
    [1, 1, 1,  0,  1, 1, 1],
    [0, 0, 1,  0,  1, 0, 0],
    [0, 0, 1,  0,  1, 1, 1],
]
PATTERN_42_HEIGHT: int = 5
PATTERN_42_WIDTH: int = 7

"""Min maze dim required to embed the pattern
with 2-cell padding on each side"""
MIN_WIDTH: int = PATTERN_42_WIDTH + 4
MIN_HEIGHT: int = PATTERN_42_HEIGHT + 4


class MazeGeneratorError(Exception):
    pass


class MazeGenerator:
    """Generates perfect mazes with loops
    width: Number of cells along the horizontal axis
    height: Number of cells along the vertical axis
    seed: Seed used for reproducible maze generation
    grid: The resulting maze grid (MazeGrid), indexed as grid[y][x]"""

    def __init__(self, width: int, height: int, seed: int | None = None
                 ) -> None:

        """Initializes the maze generator with the specified maze dimensions.
        width: Number of columns (>= 1).
        height: Number of rows (>= 1).
        seed: Optional seed for reproducible generation.
        If None, a random system seed is used
        Raises:
        MazeGeneratorError: If width or height is not positive"""

        if width < 1 or height < 1:
            raise MazeGeneratorError(
                "width and height must be positive integers"
            )

        self.width: int = width
        self.height: int = height
        self.seed: int | None = seed
        self._rng: random.Random = random.Random(seed)
        self.grid: MazeGrid = self.blank_grid()
        self.pattern_cells: set[Coordinate] = set()

    def blank_grid(self) -> MazeGrid:
        """Creates a new grid with all four walls closed in every cell
        Returns:
        MazeGrid: A width x height matrix where each cell
        is initialized to 15 (0xF)"""
        return [
            [ALL_WALLS_CLOSED for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def add_42_pattern(self) -> None:
        """Draws the 42 pattern in the center of the maze.
        If the maze is too small, prints a warning to stderr"""

        if self.width < MIN_WIDTH or self.height < MIN_HEIGHT:
            sys.stderr.write(
                "Warning: Maze dimensions too small for '42' pattern\n"
            )
            return

        start_x = (self.width - PATTERN_42_WIDTH) // 2
        start_y = (self.height - PATTERN_42_HEIGHT) // 2

        for py in range(PATTERN_42_HEIGHT):
            for px in range(PATTERN_42_WIDTH):
                if PATTERN_42[py][px] == 1:
                    gx = start_x + px
                    gy = start_y + py
                    self.pattern_cells.add((gx, gy))
                    # the cell is completely enclosed
                    self.grid[gy][gx] = ALL_WALLS_CLOSED

    def neighbors(self, x: int, y: int) -> list[tuple[Wall, int, int]]:
        """Lists the valid neighbors (within the grid) of a cell
        x: X-coordinate of the source cell
        y: Y-coordinate of the source cell
        Returns:
        list[tuple[Wall, int, int]]: Tuples containing (wall, nx, ny)
        of each neighboring cell within the grid."""

        result: list[tuple[Wall, int, int]] = []
        for wall, (dx, dy) in WALL_DELTA.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                result.append((wall, nx, ny))
        return result

    def carve(self, x: int, y: int, nx: int, ny: int, wall: Wall) -> None:
        """Opens the shared wall between two neighboring cells
        x: X-coordinate of the source cell
        y: Y-coordinate of the source cell
        nx: X-coordinate of the neighboring cell.
        ny: Y-coordinate of the neighboring cell
        wall: Wall on the source cell (x, y)
        facing the neighboring cell(nx, ny)"""
        self.grid[y][x] &= ~int(wall)
        self.grid[ny][nx] &= ~int(WALL_OPPOSITE[wall])

    def backtracker(self, start: Coordinate) -> None:
        """
        Generates a perfect maze,randomly moves to an unvisited neighbor
        and removes the shared wall when there are no more unvisited neighbors
        """
        visited: set[Coordinate] = {start}
        stack: list[Coordinate] = [start]

        while stack:
            x, y = stack[-1]
            candidates = [
                (wall, nx, ny)
                for wall, nx, ny in self.neighbors(x, y)
                if (nx, ny) not in visited
                and (nx, ny) not in self.pattern_cells
            ]

            if not candidates:
                stack.pop()
                continue

            wall, nx, ny = self._rng.choice(candidates)
            self.carve(x, y, nx, ny, wall)
            visited.add((nx, ny))
            stack.append((nx, ny))

    def opens_3x3_block(
        self, x: int, y: int, nx: int, ny: int
    ) -> bool:
        """Checks whether opening the wall between (x, y) and (nx, ny)
        would create a fully open 3x3 block of cells
        Returns:
        bool: True if opening this wall would create a fully open 3x3 area. """
        for top in (y - 2, y - 1, y):
            for left in (x - 2, x - 1, x):
                if top < 0 or left < 0:
                    continue
                if top + 3 > self.height or left + 3 > self.width:
                    continue

                block = {
                    (left + dx, top + dy)
                    for dy in range(3)
                    for dx in range(3)
                }
                if (x, y) not in block or (nx, ny) not in block:
                    continue

                if self.fully_open(block, x, y, nx, ny):
                    return True

        return False

    def fully_open(
        self, block: set[Coordinate], x: int, y: int, nx: int, ny: int
    ) -> bool:
        """
        Simulates opening the candidate wall and checks whether the 3x3 block
        would have all of its internal walls open.
        Returns:
        bool: True if, after the simulated opening,
        all 12 internal walls of the 3x3 block would be open.
        """
        for bx, by in block:
            walls = self.grid[by][bx]
            for wall, (dx, dy) in WALL_DELTA.items():
                neighbor = (bx + dx, by + dy)
                if neighbor not in block:
                    continue

                is_candidate = (bx, by, neighbor[0], neighbor[1]) in (
                    (x, y, nx, ny),
                    (nx, ny, x, y),
                )
                wall_is_open = is_candidate or not (walls & int(wall))
                if not wall_is_open:
                    return False

        return True

    def add_loops(
        self, min_loops: int = 2, max_extra_ratio: float = 0.06
    ) -> None:
        """
        Adds loops (removes internal walls) to a perfect maze
        Converts the spanning tree into a graph with cycles (PERFECT=False),
        while avoiding the creation of fully open 3x3 blocks
        min_loops: Minimum number of extra walls to attempt to remove
        max_extra_ratio: Fraction of the total number of cells used as
        the upper limit, preventing the maze from becoming too open.
        """

        max_extra = max(
            min_loops, int(self.width * self.height * max_extra_ratio)
        )
        candidates: list[tuple[int, int, int, int, Wall]] = []

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.pattern_cells:
                    continue
                for wall, nx, ny in self.neighbors(x, y):
                    if wall in (Wall.S, Wall.W):
                        continue
                    if (nx, ny) in self.pattern_cells:
                        continue
                    if self.grid[y][x] & int(wall):
                        candidates.append((x, y, nx, ny, wall))

        self._rng.shuffle(candidates)

        removed = 0
        for x, y, nx, ny, wall in candidates:
            if removed >= max_extra:
                break
            if self.opens_3x3_block(x, y, nx, ny):
                continue
            self.carve(x, y, nx, ny, wall)
            removed += 1

    def is_dead_end(self, x: int, y: int) -> bool:
        """Checks if a cell is a dead-end (has 3 closed walls)"""
        if (x, y) in self.pattern_cells:
            return False
        return bin(self.grid[y][x]).count('1') == 3

    def remove_dead_end(self, max_tolerated: int = 2) -> None:
        """Eliminates dead-ends by opening walls toward valid neighbors"""
        dead_ends: list[Coordinate] = []
        for y in range(self.height):
            for x in range(self.width):
                if self.is_dead_end(x, y):
                    dead_ends.append((x, y))

        self._rng.shuffle(dead_ends)

        while len(dead_ends) > max_tolerated:
            x, y = dead_ends.pop()
            if not self.is_dead_end(x, y):
                continue
            
            candidates = []
            for wall, nx, ny in self.neighbors(x, y):
                if (self.grid[y][x] & int(wall)) and (nx, ny) not in self.pattern_cells:
                    if not self.opens_3x3_block(x, y, nx, ny):
                        candidates.append((wall, nx, ny))
            if candidates:
                wall, nx, ny = self._rng.choice(candidates)
                self.carve(x, y, nx, ny, wall)

    def generate(
        self,
        perfect: bool,
        entry: Coordinate,
        exit_: Coordinate,
        algorithm: str = "backtracker"
    ) -> None:

        """Runs the main maze generation workflow."""

        for (cx, cy), label in ((entry, "ENTRY"), (exit_, "EXIT")):
            if not (0 <= cx < self.width and 0 <= cy < self.height):
                raise MazeGeneratorError(
                    f"{label} {(cx, cy)} is out of maze bounds"
                )
        if entry == exit_:
            raise MazeGeneratorError("ENTRY and EXIT must be different cells")

        self.grid = self.blank_grid()
        self.pattern_cells.clear()
        
        if perfect == True:
            self.add_42_pattern()

        if entry in self.pattern_cells or exit_ in self.pattern_cells:
            raise MazeGeneratorError(
                "ENTRY or EXIT conflicts with '42' pattern cells"
            )

        if algorithm == "backtracker":
            self.backtracker(entry)
        else:
            raise MazeGeneratorError(f"Unknown algorithm: {algorithm}")

        if not perfect:
            self.add_loops()
            self.remove_dead_end()
