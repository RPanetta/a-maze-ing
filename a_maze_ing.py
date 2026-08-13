import sys
from config_parse import ConfigError, config_parse
from cli_display import cli_display


def run(config_path: str) -> int:
    """Runs the complete workflow: read the configuration, then hand
    off to the interactive menu (generate/re-solve, toggle solution
    display, cycle wall colour, quit-and-save).
    config_path: path to the configuration file
    Returns: int: Exit code (0 on success, 1 on error)"""
    try:
        config = config_parse(config_path)
    except ConfigError as err:
        print(f"Error in configuration: {err}")
        return 1

    return cli_display(config)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    sys.exit(run(sys.argv[1]))
