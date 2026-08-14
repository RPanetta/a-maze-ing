	*This project has been created as part of the 42 curriculum by rpanetta, nnagy.*

# A-Maze-ing

## Description

**A-Maze-ing** is a Python command-line tool that generates, solves, and lets you interactively explore mazes.

Given a small text configuration file (size, entry/exit points, and a couple of options), the program:

1. **Generates** a maze on a grid, either as a *perfect* maze (exactly one path between any two cells, no loops) or as a *playable* maze (loops added, dead-ends trimmed, so it works as a Pac-Man-style board with several possible routes).
2. **Solves** it, computing the shortest path from the entry to the exit with a breadth-first search.
3. **Displays** it in the terminal through a small interactive menu: re-generate, show/hide the solution, cycle the wall colour, or quit (which writes the current maze to a file).

The goal of the project is to practice algorithmic thinking (graph traversal, randomised generation, BFS), clean modular design in Python, and file/CLI I/O, while producing something genuinely fun to play with.

## Instructions

**Requirements:** Python 3.10+

```bash
# Run with the default config.txt
make run

# Or run directly, pointing at any config file
python3 a_maze_ing.py config.txt

# Step through the program with the debugger
make debug

# Remove caches and the generated maze.txt
make clean
```

Development-only targets (require `flake8` and `mypy`, installed via `make install`):

```bash
make install      # installs build/setuptools + the project's dev tools
make lint          # flake8 + mypy (relaxed)
make lint-strict   # flake8 + mypy --strict
```

Once running, the interactive menu looks like this:

```
┌─ A-Maze-ing ──────────────────────┐
│  1. Re-generate a new maze        │
│  2. Show / Hide the shortest path │
│  3. Rotate the wall colours       │
│  4. Quit                          │
└───────────────────────────────────┘
```

- **1. Re-generate** builds a brand-new maze (new random layout, unless `SEED` is set in the config) and re-solves it, so the shown solution is never stale.
- **2. Show / Hide** toggles a bright-green overlay tracing the shortest path from entry to exit.
- **3. Rotate colours** cycles the wall colour through 6 ANSI options; the entry/exit markers, the "42" pattern (bright yellow) and the solution path (bright green) always keep their own fixed colours so they stay legible no matter what.
- **4. Quit** writes the current maze and solution to `OUTPUT_FILE` and exits.

## Configuration file

The config file is a simple `KEY=VALUE` text file, one entry per line. Lines that are blank or start with `#` are ignored. Keys are case-insensitive, and if a key is repeated, the last occurrence wins.

| Key           | Type              | Description                                                        |
|---------------|-------------------|----------------------------------------------------------------------|
| `WIDTH`       | positive integer  | Number of columns in the maze.                                     |
| `HEIGHT`      | positive integer  | Number of rows in the maze.                                        |
| `ENTRY`       | `x,y`             | Entry cell coordinates. Must be inside the grid.                   |
| `EXIT`        | `x,y`             | Exit cell coordinates. Must be inside the grid and differ from `ENTRY`. |
| `OUTPUT_FILE` | string            | Path the maze is written to on quit.                                |
| `PERFECT`     | `True` / `False`  | `True` for a single-path perfect maze, `False` for a looped, playable maze (case-insensitive). |
| `SEED`        | integer, optional | If set, makes generation reproducible; omit for a random maze each run. |

Example (`config.txt`):

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
```

### Output file format

The written maze.txt parts:

1. **Grid** — one line per row, one hexadecimal digit (`0`-`f`) per cell. Each digit is a 4-bit mask of the cell's *closed* walls: bit `1`=North, `2`=East, `4`=South, `8`=West (so `d` = `1101` = North+South+West closed, East open).
2. The **entry coordinate** (`x,y`), the **exit coordinate** (`x,y`), and the shortest **solution path** as a string of `N`/`E`/`S`/`W` letters.

Example:

```
d53d1393915579511557
95696eac6a953abae953
ad38556956abc6ac3aba
c386953c39685383c46a
96ad43c3c056d46c7952
abc53afafafff95556ba
a8552afef857fa955386
ae93c6fffafffaad3c6b
c56c553bfafd52c54552
955393aafefffa95393a
c3bc6aac13d156c3c6c6
96c396c56c56917c3917
a93c693939556c53ae83
aaa93ac6c6953d3ac3ea
c6c6c455556d456c5456

0,0
19,14
EESWWSSESWSSSSEENESEEESSSEENESEENEENNNNNEEEENEESSWSWNWWWSSEEEEESSWNWSWNWWSESESSESEE
```

## Maze generation algorithm

The maze is generated with **recursive backtracking (randomised depth-first search)**: starting from the entry cell, the algorithm repeatedly moves to a random unvisited neighbour, carving (opening) the wall between the two cells, and backtracks along a stack whenever it hits a cell with no unvisited neighbours left, until every cell has been visited.

We chose recursive backtracking because:

- It always produces a **perfect maze** in one pass — a spanning tree over the grid with exactly one path between any two cells — which is exactly what `PERFECT=True` requires, with no separate cleanup step needed.
- It tends to produce long, winding corridors with comparatively few short dead-ends, which reads well visually.

For `PERFECT=False` boards, the same perfect maze is used as a base and then adapted in two further passes, so the result has loops and alternative routes instead of just one fixed path between any two cells:

- **`add_loops`** removes a bounded number of extra internal walls (never on the pattern cells, and never if doing so would open up a fully-walled 3×3 block, which would look like an empty room) to introduce alternative routes.
- **`remove_dead_end`** finds any remaining dead-end cells (3 closed walls) and opens one wall on each, down to a small tolerated number, so the board doesn't trap a chased player. This directly satisfies the school's Pac-Man-readiness check in `maze_analyzer.py` (`--max-dead-ends`).

## Reusable code

The `mazegen/` package is written as a **self-contained, project-agnostic maze library** with no dependency on the CLI, the config format, or the output file format:

- `mazegen.MazeGenerator` — builds a maze grid for any `width`/`height` (and optional `seed`), perfect or playable.
- `mazegen.solve_bfs` — solves any `MazeGrid` from any entry to any exit.
- `mazegen.mazegen_types` — the shared vocabulary (`Wall`, `Coordinate`, `MazeGrid`, `decode_bitmask`/`encode_walls`, and the `WALL_*` lookup tables) that both generation and solving are built on.

Anything that only needs "give me a maze grid and/or its solution" can `import mazegen` and use it directly — a different frontend (a GUI, a web service, another CLI with a different config format) could be built on top of it without touching a single line inside the package.

What's *not* reusable, by design, stays outside `mazegen/`: `config_parse.py` (this project's specific `KEY=VALUE` format), `output_maze_writer.py` (this project's specific output file layout), and `cli_display.py` (this project's specific terminal menu) are all project-specific glue around the reusable core.

## Team and project management

| Member | Role |
|---|---|
| intra: rpanetta (Rocío) | **Algorithm**: `MazeGenerator` (generation, loop-adding, dead-end removal, "42" pattern), `BFS solver`, and the `Makefile`. |
| intra: nnagy (Norbert) | **Visualization**: `config parsing`, `output file writing`, `CLI/terminal display` |
*Shared responsabilities* on `mazegen_types.py`

Since the project defense requires each of us to be able to explain the whole codebase, we split the work along a clear interface (the `mazegen` package vs. everything around it) but stayed in sync on shared conventions — naming, the wall bitmask, the grid indexing order — so either of us can read and defend both halves.

**Planning:** we started by agreeing on the data model together (the `Wall` bitmask, `grid[y][x]` indexing, the config format) before splitting off to our respective sides, so neither side had to guess at the other's interface. Norbi's side (config → CLI → output) was largely straightforward and finished early. Roci's generator needed more iteration than planned: an early version of the backtracker could carve into the sealed "42" pattern cells, and the first loop-adding pass removed walls at random instead of specifically targeting dead-ends — both were caught during cross-review and fixed with a targeted candidate filter and dedicated `find`/`remove` dead-end helpers.

**What worked well:** Agreeing on shared types and naming conventions up front, kept each other constantly updated about changes and supporting each other during coding hardships.

**What could be improved:** Code efficiency could be optimized further

### Rebuilding and testing the package

```bash
# Step 1 — create a virtualenv and build the package
python3 -m venv build_env
source build_env/bin/activate
pip install build
python3 -m build
deactivate
# output: dist/mazegen-1.0.0-py3-none-any.whl

# Step 2 — in a fresh virtualenv, install and test it
python3 -m venv test_env
source test_env/bin/activate
pip install dist/mazegen-1.0.0-py3-none-any.whl
python3 a_maze_ing.py config.txt
deactivate
```

If the program runs correctly without import errors, the package is working.

---

## Resources

Classic references we used to design and implement the generator and solver:

- Jamis Buck, *Mazes for Programmers* — the standard reference on maze-generation algorithms (recursive backtracking, Prim's, Kruskal's, etc.) and their trade-offs.
- Wikipedia, [Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm) — overview and pseudo-code for recursive backtracking and other approaches.
- Wikipedia, [Breadth-first search](https://en.wikipedia.org/wiki/Breadth-first_search) — used for the shortest-path solver.
- Python documentation on [`enum.IntFlag`](https://docs.python.org/3/library/enum.html#enum.IntFlag) and [`collections.deque`](https://docs.python.org/3/library/collections.html#collections.deque), used respectively for the wall bitmask and the BFS queue.

**AI usage:** for better understanding the concept, the main principles and as a learning aid for explanations and debugging hints without asking for direct answers.

Concept Clarification: AI was used to understand graph theory, backtracker algorithm, bitwise operations and BFS optimality.

Architecture & Design: AI assisted in identifying separation of concerns between generation and visualization layers, design patterns, and package structure.

Documentation & Explanation: AI helped translate algorithmic concepts into clear explanations, generate docstrings, and structure this README.
