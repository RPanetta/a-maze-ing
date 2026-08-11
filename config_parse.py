from dataclasses import dataclass
from mazegen.mazegen_types import Coordinate

REQUIRED_KEY = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]


class ConfigError(Exception):
    pass


@dataclass
class MazeConfig:
    width: int
    height: int
    entry: Coordinate
    exit_: Coordinate
    output_file: str
    perfect: bool
    seed: int | None = None


def coordinate_parse(raw_config: str) -> Coordinate:
    """
    - Raise ConfigError on wrong coordinates in config.txt
      as ENTRY and/or EXIT
    """
    parts = raw_config.split(",")

    if len(parts) != 2:
        raise ConfigError(f"Coordinate must be x, y: got {raw_config}")
    try:
        return (int(parts[0].strip()), int(parts[1].strip()))
    except ValueError:
        raise ConfigError(f"Coordinate must be integer: got {raw_config}")


def config_parse(filename: str) -> MazeConfig:
    """
    - Parse the config.txt file into a validated MazeConfig object.

    - Raises ConfigError on any missing, malformed, or invalid value
      instead of crashing it
    """
    raw_values = {}

    try:
        with open(filename) as file:
            for line_numb, line in enumerate(file, start=1):  # file object treated and iterated through line by line
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    raise ConfigError(f"malformed line {line_numb}: {line}")

                key, _, value = stripped.partition("=")
                key = key.strip().upper()
                value = value.strip()
                raw_values[key] = value
    except OSError as e:
        raise ConfigError(f"Config file cannot be opened: {filename} ({e})")

    for key in REQUIRED_KEY:
        if key not in raw_values:
            raise ConfigError(f"missing required key: {key}")

    try:
        width = int(raw_values["WIDTH"])
        height = int(raw_values["HEIGHT"])
    except ValueError:
        raise ConfigError("WIDTH/HEIGHT must be integers")

    if width <= 0 or height <= 0:
        raise ConfigError("WIDTH/HEIGHT must be positive")

    """
    - Parse ENTRY and EXIT coordinates(x,y) into entry_ and exit_
    """
    entry = coordinate_parse(raw_values["ENTRY"])
    exit_ = coordinate_parse(raw_values["EXIT"])

    """
    - Iterate through x & y coordinates and check if they are valid
      and they are inside the grid if no = ConfigError
    """
    for (x, y) in [entry, exit_]:
        if not (0 <= x < width and 0 <= y < height):
            raise ConfigError(f"Coordinate out of maze bounds: {x}, {y}")

    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different cells")

    perfect_str = raw_values["PERFECT"].lower()
    if perfect_str not in ["true", "false"]:  # not in checks whether it matches ANY of the values in the collection
        raise ConfigError("PERFECT must be True or False")
    perfect = (perfect_str == "true")

    output_file = raw_values["OUTPUT_FILE"]
    if not output_file:
        raise ConfigError("OUTPUT_FILE must not be empty")

    seed = None
    if "SEED" in raw_values:
        try:
            seed = int(raw_values["SEED"])
        except ValueError:
            raise ConfigError(f"SEED must be an integer: got {raw_values['SEED']}")

    return MazeConfig(
        width, height, entry, exit_, output_file, perfect, seed
        )
