from mazegen.mazegen_types import MazeGrid, Coordinate, WALL_DELTA, WALL_LETTER
from collections import deque

class SolverError(Exception):
    pass


def solve_bfs(grid: MazeGrid, entry: Coordinate, exit_: Coordinate) -> str:
    """Calculates the shortest path between two cells using BFS
    grid: Maze grid (MazeGrid), indexed as grid[y][x]
    entry: Coordinates (x, y) of the entry cell
    exit_: Coordinates (x, y) of the exit cell
    Returns: str: Sequence of N/E/S/W letters representing the shortest path from entry to exit.
    Returns an empty string if entry == exit_.
    SolverError: If entry or exit_ is outside the grid boundaries,
    or if no path exists between the two cells (the maze is not fully connected)"""
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    for (cx, cy), label in ((entry, "ENTRY"), (exit_, "EXIT")):
        if not (0 <= cx < width and 0 <= cy < height):
            raise SolverError(f"{label} coordinate {(cx, cy)} is out of bounds")

    if entry == exit_:
        return ""

    visited: set[Coordinate] = {entry}
    queue: deque[tuple[Coordinate, str]] = deque() #deque: it's a type of data structure that allows to add and remove elements from both ends efficiently
    queue.append((entry, ""))

    while queue:
        (cx, cy), path = queue.popleft()

        if (cx, cy) == exit_:
            return path

        walls = grid[cy][cx]

        for wall, (dx, dy) in WALL_DELTA.items():
            if walls & int(wall):
                continue

            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in visited:
                continue

            visited.add((nx, ny))
            queue.append(((nx, ny), path + WALL_LETTER[wall]))

    raise SolverError(f"No path found between {entry} and {exit_}")
