import random
from mazegen.mazegen_types import MazeGrid, Wall, WALL_DELTA, WALL_OPPOSITE, Coordinate

ALL_WALLS_CLOSED = int(Wall.N | Wall.E | Wall.S | Wall.W)

class MazeGeneratorError(Exception):
    pass


class MazeGenerator:
    """Generates perfect mazes with loops
    width: Number of cells along the horizontal axis
    height: Number of cells along the vertical axis
    seed: Seed used for reproducible maze generation
    grid: The resulting maze grid (MazeGrid), indexed as grid[y][x]"""

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        """Initializes the maze generator with the specified maze dimensions.
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
        x: X-coordinate of the source cell
        y: Y-coordinate of the source cell
        Returns:
        list[tuple[Wall, int, int]]: Tuples containing (wall, nx, ny)
        of each neighboring cell within the grid."""

        result: list [tuple[Wall, int, int]] = []
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
        wall: Wall on the source cell (x, y) facing the neighboring cell(nx, ny)"""
        self.grid[y][x] &= ~int(wall) #It operates on the binary representation of integers and performs AND operation on each corresponding bit
        self.grid[ny][nx] &= ~int(WALL_OPPOSITE[wall])
    
    def backtracker(self) -> None:
        """Generates a perfect maze,randomly moves to an unvisited neighbor
        and removes the shared wall. When there are no more unvisited neighbors"""
        visited: set[Coordinate] = {(0, 0)}
        stack: list[Coordinate] = [(0, 0)]
 
        while stack:
            x, y = stack[-1]
            candidates = [
                (wall, nx, ny)
                for wall, nx, ny in self._neighbors(x, y)
                if (nx, ny) not in visited
            ]
 
            if not candidates:
                stack.pop()
                continue
 
            wall, nx, ny = self._rng.choice(candidates)
            self._carve(x, y, nx, ny, wall)
            visited.add((nx, ny))
            stack.append((nx, ny))


    def opens_3x3_block(self, x: int, y: int, nx: int, ny: int) -> bool:
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
 
                block = {(left + dx, top + dy) for dy in range(3) for dx in range(3)}
                if (x, y) not in block or (nx, ny) not in block:
                    continue
 
                if self.fully_open(block, x, y, nx, ny):
                    return True
 
        return False
    
    
    def fully_open(self, block: set[Coordinate], x: int, y: int, nx: int, ny: int) -> bool:
        """Simulates opening the candidate wall and checks whether the 3x3 block
        would have all of its internal walls open.
        Returns:
        bool: True if, after the simulated opening, all 12 internal walls of the 3x3 block would be open."""
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
    
    
    def add_loops(self, min_loops: int = 2, max_extra_ratio: float = 0.06) -> None:
        """adds loops (removes internal walls) to a perfect maze
        Converts the spanning tree into a graph with cycles for Pac-Man mode (PERFECT=False),
        while avoiding the creation of fully open 3x3 blocks
        min_loops: Minimum number of extra walls to attempt to remove
        max_extra_ratio: Fraction of the total number of cells used as the upper limit,
        preventing the maze from becoming too open."""

        max_extra = max(min_loops, int(self.width * self.height * max_extra_ratio))
        candidates: list[tuple[int, int, int, int, Wall]] = []
 
        for y in range(self.height):
            for x in range(self.width):
                for wall, nx, ny in self._neighbors(x, y):
                    if wall in (Wall.S, Wall.W):
                        continue
                    if self.grid[y][x] & int(wall):
                        candidates.append((x, y, nx, ny, wall))
 
        self._rng.shuffle(candidates)

        removed = 0
        for x, y, nx, ny, wall in candidates:
            if removed >= max_extra:
                break
            if self._opens_3x3_block(x, y, nx, ny):
                continue
            self._carve(x, y, nx, ny, wall)
            removed += 1


    def generate( self, perfect: bool, entry: Coordinate, exit_: Coordinate, algorithm: str = "backtracker") -> None:
        for (cx, cy), label in ((entry, "ENTRY"), (exit_, "EXIT")):
            if not (0 <= cx < self.width and 0 <= cy < self.height):
                raise MazeGeneratorError(f"{label} {(cx, cy)} is out of maze bounds")
        if entry == exit_:
            raise MazeGeneratorError("ENTRY and EXIT must be different cells")
 
        self.grid = self.blank_grid()
 
        if algorithm == "backtracker":
            self.backtracker()
        else:
            raise MazeGeneratorError(f"Unknown algorithm: {algorithm}")
 
        if not perfect:
            self.add_loops()
