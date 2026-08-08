from enum import IntFlag
"""
    IntFlag is ideal for configuration bits,
    and compact encodings where multiple boolean properties are stored
    inside a single integer.
"""

class MazeTypeError(Exception):
    pass


Coordinate = tuple[int, int]
"""An (x, y) position on the maze grid."""

MazeGrid = list[list[int]]
"""
The maze grid, indexed as grid[y][x].'y' is a row | 'x' is a column
Each value is a Wall-bitmask int (0-15) representing which walls
are closed for that cell.
"""


class Wall(IntFlag):
    """
    Each wall is a power of two so every direction occupies one unique bit.
    This lets walls combine into a single number using bitwise OR.
    Closed walls set their bit to 1; open walls leave it 0.
    """
    N = 1
    E = 2
    S = 4
    W = 8


def decode_bitmask(value: int) -> dict[str, bool]:  # for reading
    """
    Decode a wall-bitmask int (0-15) into a dict of open/closed walls.

    Args:
        value: wall-bitmask, 0-15, where each bit represents one wall.

    Returns:
        dict mapping "N"/"E"/"S"/"W" to True if that wall is closed.

    Raises:
        MazeTypeError: if value is outside 0-15.
    """
    if not 0 <= value <= 15:
        raise MazeTypeError(f"Invalid value for bitmask (0-15): {value}")
    flags = Wall(value)

    """
    "(flags & north)" → CHECK if wall is closed
    """

    north = bool(flags & Wall.N)
    east = bool(flags & Wall.E)  # Wall-E ≧w≦ hehehe
    south = bool(flags & Wall.S)
    west = bool(flags & Wall.W)

    return {
        "N": north,
        "E": east,
        "S": south,
        "W": west
    }


def encode_walls(north: bool, east: bool, south: bool, west: bool) -> int:  # for writing
    """
    Encode four wall states into a single wall-bitmask int.

    Args:
        north: True if the north wall is closed.
        east: True if the east wall is closed.
        south: True if the south wall is closed.
        west: True if the west wall is closed.

    Returns:
        Wall-bitmask int (0-15), combining the closed walls via their
        respective bit positions.
    """
    flags = Wall(0)
    if north:
        flags |= Wall.N
    if east:
        flags |= Wall.E
    if south:
        flags |= Wall.S
    if west:
        flags |= Wall.W

    return flags.value


"""When moving from a cell (x, y) to its neighboring cell (nx, ny)
the movement delta is (nx - x, ny - y)"""
WALL_DELTA: dict[Wall, Coordinate] = {
    Wall.N: (0, -1), #North: x stays the same, y decreases by 1 (row above)
    Wall.E: (1, 0), #East: x increases by 1, y stays the same
    Wall.S: (0, 1), #South: x stays the same, y increases by 1 (row below)
    Wall.W: (-1, 0), #West: x decreases by 1, y stays the same
}
"""Grid offset (dx, dy) when crossing each wall."""

WALL_OPPOSITE: dict[Wall, Wall] = {
    Wall.N: Wall.S,
    Wall.S: Wall.N,
    Wall.E: Wall.W,
    Wall.W: Wall.E,
}
"""Opposite wall, required to keep neighboring cells consistent."""

WALL_LETTER: dict[Wall, str] = {
    Wall.N: "N",
    Wall.E: "E",
    Wall.S: "S",
    Wall.W: "W",
}
"""Letter used in the solution_path of the output file (Chapter IV.5)."""