from mazegen.mazegen_types import Coordinate, MazeGrid


class OutputWriterError(Exception):
    pass


def to_hex_digit(value: int) -> str:
    if not (0 <= value <= 15):
        raise OutputWriterError(f"Invalid value to convert hex: {value}")
    return format(value, "x")


def output_maze_writer(
        path: str,
        grid: MazeGrid,
        width: int,
        height: int,
        entry: Coordinate,
        exit_: Coordinate,
        solution_path: str
        ) -> None:
    try:
        with open(path, "w", newline="") as file:  # 'newline="" + '\n' = full control over exactly what bytes end up on disk.
            for row in grid:
                row_chars = []
                for cell in row:
                    row_chars.append(to_hex_digit(cell))
                file.write("".join(row_chars) + "\n")

            file.write("\n")
            file.write(f"{entry[0]}, {entry[1]}\n")
            file.write(f"{exit_[0]}, {exit_[1]}\n")
            file.write(f"{solution_path}\n")

    except OSError as e:
        raise OutputWriterError(f"Cannot write output file: {path}, ({e})")

# if __name__ == "__main__":

#     fake_grid = [[8, 4, 8, 10, 2], [1, 15, 5, 13, 8], [4, 5, 10, 11, 4], [4, 12, 3, 0, 2], [3, 5, 10, 8, 10]]
#     output_maze_writer("test_output.txt", fake_grid, width=5, height=5, entry_=(0, 0), exit_=(4, 4), solution_path="ESEES")
