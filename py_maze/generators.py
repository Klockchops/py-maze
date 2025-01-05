from . import maze_utils
from .maze_utils import DIRECTION


class GenBase:
    visible = False
    display = ""

    def __init__(self, maze, break_walls_chance, watch=True) -> None:
        self.maze = maze
        self.break_walls_chance = break_walls_chance
        self._step = None
        self.watch = watch

    def first_step(self):
        raise NotImplementedError

    def step(self):
        self._step()
        while not self.watch and self.not_done():
            self._step()

    def not_done(self):
        return self._step is not None


class RecursiveGenerator(GenBase):
    visible = True
    display = "Recursive Backtracing"

    def __init__(self, maze, break_walls_chance, watch=True) -> None:
        super().__init__(maze, break_walls_chance, watch)
        self.stack = []

    def first_step(self):
        """Creates a maze using the recursive backtracking algorithm."""
        x, y = self.maze.start
        self.stack = []
        for dir in maze_utils.make_direction_list():
            x0, y0 = maze_utils.take_step(dir, x, y)
            if not self.maze.out_of_bounds(x0, y0):
                self.stack = [[dir, x0, y0] for dir in maze_utils.make_direction_list()]
                maze_utils.carve_path(self.maze, x, y, x0, y0, dir)
                break
        self._step = self._take_step

    def _take_step(self):
        while self.stack:
            dir, x, y = self.stack.pop(-1)
            tx, ty = maze_utils.create_walk(
                self.maze, x, y, dir, self.break_walls_chance
            )
            if tx is not None:
                self.stack.extend(
                    [
                        [dir1, tx, ty]
                        for dir1 in maze_utils.make_direction_list()
                        if dir1 is not maze_utils.opposite(dir)
                        or not self.maze.out_of_bounds(tx, ty)
                    ]
                )
                return
        # Connect exit to a valid cell
        if self.maze.pos_is_unreached(*self.maze.end):
            for dir in range(3):
                tx, ty = maze_utils.take_step(dir, *self.maze.end)
                if not self.maze.out_of_bounds(tx, ty):
                    maze_utils.carve_path(
                        self.maze, *self.maze.end, tx, ty, DIRECTION(dir)
                    )
                    break
        self._step = None
        self.maze.clear_current()


class HuntAndKill(GenBase):
    visible = True
    display = "Hunt and Kill"

    def __init__(self, maze, break_walls_chance, watch=True) -> None:
        super().__init__(maze, break_walls_chance, watch)
        self.unfinished_rows = []
        self.unfinished_columns = []

    def first_step(self):
        self.stack = [
            [dir, *self.maze.start]
            for dir in maze_utils.make_direction_list()
            if dir != self.maze.start_side
        ]
        self.unfinished_rows = [y for y in range(0, self.maze.y)]

        self._step = self._hunt_and_kill

    def _hunt_and_kill(self):
        """Randomly walks along a segment until you can go no further. Only considers no further as
        a wall to either out of bounds or an initialized cell and all directions have been exhausted.
        """

        while self.unfinished_rows:
            while self.stack:
                dir, x, y = self.stack.pop(0)
                self.maze[x, y].visited = True
                tx, ty = maze_utils.create_walk(self.maze, x, y, dir)
                if tx is not None:
                    self.stack = [
                        [dir1, tx, ty]
                        for dir1 in maze_utils.make_direction_list()
                        if dir1 != maze_utils.opposite(dir)
                    ]
                    return
            # We have reached the end of our walk, find a new place to start walking from.
            self.unfinished_columns = [
                x
                for x in range(0, self.maze.x)
                if not self.maze[x, self.unfinished_rows[0]].visited
            ]
            self._step = self._hunt
            return
        self._step = self._finalize

    def _hunt(self):
        """Scan the current row for a new cell to start walking from. If the current row has not been exhausted of matches it will start
        walking from cells that have been initialized"""
        while self.unfinished_rows:
            y = self.unfinished_rows[0]
            while self.unfinished_columns:
                x = self.unfinished_columns.pop(0)
                self.maze.set_current(x, y)
                # Try to find a visited cell next to ours to start walking from
                for dir in maze_utils.make_direction_list():
                    tx, ty = maze_utils.take_step(dir, x, y)

                    if (
                        not self.maze.out_of_bounds(tx, ty)
                        and self.maze[tx, ty].visited
                    ):
                        maze_utils.carve_path(self.maze, x, y, tx, ty, dir)
                        self.stack = [
                            [dir1, x, y]
                            for dir1 in maze_utils.make_direction_list()
                            if dir1 != dir
                        ]
                        self._step = self._hunt_and_kill
                        break
                # Could not find a cell to walk from. Add it back to the end of the list
                else:
                    self.unfinished_columns.append(x)
                return
            self.unfinished_rows.pop(0)
            if self.unfinished_rows:
                self.unfinished_columns = [
                    _x
                    for _x in range(0, self.maze.x)
                    if not self.maze[_x, self.unfinished_rows[0]].visited
                ]
            else:
                self._step = self._finalize
            return

    def _finalize(self):
        """Connect exit to a valid cell if not already."""
        if self.maze.pos_is_unreached(*self.maze.end):
            for dir in range(4):
                tx, ty = maze_utils.take_step(dir, *self.maze.end)
                if not self.maze.out_of_bounds(tx, ty):
                    maze_utils.carve_path(
                        self.maze, *self.maze.end, tx, ty, DIRECTION(dir)
                    )
                    break
        self.maze.clear_current()
        self._step = None


class Kruskal(GenBase):
    visible = True
    display = "Kruskal"

    def __init__(self, maze, break_walls_chance, watch=True) -> None:
        super().__init__(maze, break_walls_chance, watch)
        self.stack = []
        self.sets = []

    def first_step(self):
        """Throw all the edges into a "bag" to randomly remove later.
        Edges don't really exist in my maze implementation so we are storing coordinates of
        cells that have a cell to their right or below them. These are the only edges that are
        breakable."""
        bag = []
        for x in range(0, self.maze.x):
            for y in range(0, self.maze.y):
                if x == (self.maze.x - 1) and y == (self.maze.y - 1):
                    continue
                if x == (self.maze.x - 1):
                    bag.append([0, x, y])
                elif y == (self.maze.y - 1):
                    bag.append([1, x, y])
                else:
                    for i in range(2):  # 0 == down; 1 == right
                        bag.append([i, x, y])
        # Randomly sort the bag
        maze_utils.glRand.shuffle(bag)
        self.stack = bag
        self._step = self._kruskal_step

    def _kruskal_step(self):
        """Pull an edge out of the bag. If the edge is between two cells that do not belong to
        the same set, break the wall down and combine the sets."""
        while self.stack:
            dv, x, y = self.stack.pop(0)
            # Edge is to the right
            if dv:
                dx, dy = 1, 0
            # Edge is below
            else:
                dx, dy = 0, 1

            cell1 = self.maze[x, y]
            cell2 = self.maze[x + dx, y + dy]

            # Merge sets if they don't match or both are uninitialized.
            if cell1.set != cell2.set or cell1.set == -1:
                maze_utils.combine_sets(
                    self.sets, cell1, cell2, DIRECTION.RIGHT if dv else DIRECTION.BOTTOM
                )
            # Both cells in the same set already. Break wall chance?
            if cell1.set == cell2.set:
                pass

            return

        self.maze.clear_current()
        self._step = None


class Eller(GenBase):
    visible = True
    display = "Eller's"

    def __init__(self, maze, break_walls_chance, watch=True) -> None:
        super().__init__(maze, break_walls_chance, watch)
        self.sets = []
        self.bridge_sets = set()
        self.row = 0
        self.column = 0

    def first_step(self):
        self._step = self._eller_init_row

    def _eller_init_row(self):
        """Walk along the row and ensure every cell has been initialized(belongs to a valid set.)"""
        if self.column == self.maze.x:
            self._step = self._eller_join
            self.column = 0
            return

        node = self.maze[self.column, self.row]
        if node.set == -1:
            node.set = len(self.sets)
            self.sets.append(
                [
                    node,
                ]
            )
        else:
            self.sets[node.set].append(node)
        self.maze.set_current(self.column, self.row)
        self.column += 1

    def _eller_join(self):
        """Scans a row of the maze and breaks walls based on a user defined random chance. If a wall is broken the cells sets
        are udpated to be the same and sets are combined.
        """
        if self.maze.out_of_bounds(self.column + 1, self.row):
            self.column = 0
            self.bridge_sets.update(
                self.maze[i, self.row].set for i in range(self.maze.x)
            )
            self._step = self._eller_bridge
            return

        self.maze.set_current(self.column, self.row)
        current = self.maze[self.column, self.row]
        adjacent = self.maze[self.column + 1, self.row]
        if current.set == adjacent.set:
            pass
        elif maze_utils.glRand.random() * 100.0 <= self.break_walls_chance:
            maze_utils.combine_sets(
                self.sets, current, adjacent, maze_utils.DIRECTION.RIGHT
            )

        self.column += 1

    def _eller_bridge(self):
        """Walk along the row and randomly remove a wall from the the current cell and the cell below it."""
        # Check if we've reached a wall and can proceed to the next step
        if self.column == self.maze.x - 1:
            self._step = self._eller_reachable
            return

        self.maze.set_current(self.column, self.row)
        if maze_utils.glRand.random() * 100.0 < self.break_walls_chance:
            maze_utils.combine_sets(
                self.sets,
                self.maze[self.column, self.row],
                self.maze[self.column, self.row + 1],
                maze_utils.DIRECTION.BOTTOM,
            )
            _set = self.maze[self.column, self.row].set
            if _set in self.bridge_sets:
                self.bridge_sets.remove(_set)
        self.column += 1

    def _eller_reachable(self):
        """Ensure all the bridge sets have had at least one connection created to the row below it"""
        while self.bridge_sets:
            _set = self.bridge_sets.pop()
            randList = self.sets[_set][:]
            maze_utils.glRand.shuffle(randList)
            for cell1 in randList:
                if int(cell1.pos().y()) == self.row:
                    break
            column = int(cell1.pos().x())
            self.maze.set_current(column, self.row)
            maze_utils.combine_sets(
                self.sets,
                self.maze[column, self.row],
                self.maze[column, self.row + 1],
                maze_utils.DIRECTION.BOTTOM,
            )
            return

        self.row += 1
        self.column = 0

        if self.maze.out_of_bounds(self.column, self.row + 1):
            self._step = self._eller_finalize
        else:
            self._step = self._eller_init_row

    def _eller_finalize(self):
        """Scan the last row to ensure all cells are reachable"""
        if self.maze.out_of_bounds(self.column + 1, self.row):
            self._step = None
            self.maze.clear_current()
            return

        current = self.maze[self.column, self.row]
        adjacent = self.maze[self.column + 1, self.row]
        self.maze.set_current(self.column, self.row)
        if current.set != adjacent.set:
            maze_utils.combine_sets(
                self.sets, current, adjacent, maze_utils.DIRECTION.RIGHT
            )
        self.column += 1


class SideWinder(GenBase):
    visible = False
    display = "Side Winder"

    def __init__(self, maze, break_walls_chance, watch=True) -> None:
        super().__init__(maze, break_walls_chance, watch)

    def first_step(self):
        pass

    def _sidewinder(self):
        """Creates a maze using the sidewinder algorithm."""
        # Create first row
        for y in range(1, self.col_count_with_walls - 1):
            self.maze[1, y] = [255, 255, 255]

        # Create other rows
        for x in range(3, self.row_count_with_walls, 2):
            row_stack = []  # List of cells without vertical link [y, ...]
            for y in range(1, self.col_count_with_walls - 2, 2):
                self.maze[x, y] = [255, 255, 255]  # Mark as visited
                row_stack.append(y)

                if maze_utils.glRand.getrandbits(1):  # Create vertical link
                    idx = maze_utils.glRand.randint(0, len(row_stack) - 1)
                    self.maze[x - 1, row_stack[idx]] = [
                        255,
                        255,
                        255,
                    ]  # Mark as visited
                    row_stack = []  # Reset row stack
                else:  # Create horizontal link
                    self.maze[x, y + 1] = [255, 255, 255]  # Mark as visited

            # Create vertical link if last cell
            y = self.col_count_with_walls - 2
            self.maze[x, y] = [255, 255, 255]  # Mark as visited
            row_stack.append(y)
            idx = maze_utils.glRand.randint(0, len(row_stack) - 1)
            self.maze[x - 1, row_stack[idx]] = [255, 255, 255]  # Mark as visited


class Prim(GenBase):
    visible = False
    display = "Prim's"

    def __init__(self, maze, break_walls_chance, watch=True) -> None:
        super().__init__(maze, break_walls_chance, watch)

    def first_step(self):
        pass

    def _prim(self):
        """Creates a maze using Prim's algorithm."""
        frontier = []  # List of unvisited cells [(x, y),...]

        # Start with random cell
        x = 2 * maze_utils.glRand.randint(0, self.row_count - 1) + 1
        y = 2 * maze_utils.glRand.randint(0, self.col_count - 1) + 1
        self.maze[x, y] = [255, 255, 255]  # Mark as visited

        # Add cells to frontier for random cell
        for direction in self._dir_two:
            tx, ty = direction(x, y)
            if not self._out_of_bounds(tx, ty):
                frontier.append((tx, ty))
                self.maze[tx, ty, 0] = 1  # Mark as part of frontier

        # Add and connect cells until frontier is empty
        while frontier:
            x, y = frontier.pop(maze_utils.glRand.randint(0, len(frontier) - 1))

            # Connect cells
            for idx in self._random:
                tx, ty = self._dir_two[idx](x, y)
                if (
                    not self._out_of_bounds(tx, ty) and self.maze[tx, ty, 0] == 255
                ):  # Check if visited
                    self.maze[x, y] = self.maze[self._dir_one[idx](x, y)] = [
                        255,
                        255,
                        255,
                    ]  # Connect cells
                    break

            # Add cells to frontier
            for direction in self._dir_two:
                tx, ty = direction(x, y)
                if (
                    not self._out_of_bounds(tx, ty) and self.maze[tx, ty, 0] == 0
                ):  # Check if unvisited
                    frontier.append((tx, ty))
                    self.maze[tx, ty, 0] = 1  # Mark as part of frontier
