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
