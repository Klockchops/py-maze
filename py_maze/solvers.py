import random

from . import maze_utils
from .maze_utils import DIRECTION


class Solver_Base:
    visible = False
    display = ""

    def __init__(self, maze, watch):
        self.maze = maze
        self.route = []
        self.finished = False
        self._step = None
        self.watch = watch

    def set_up(self):
        if self.maze.maze is None:
            return
        for cell in self.maze.allCells():
            cell.clear_state()
        x1, y1 = self.maze.start
        x0, y0 = maze_utils.take_step(self.maze.start_side, *self.maze.start)
        self.maze[x1, y1].visited = False
        self.maze[x1, y1].checking = True
        self.route = [[x0, y0], [x1, y1]]

    def not_done(self):
        return self._step is not None

    def step(self):
        self.check_finished()
        self._step()
        while not self.watch and self.not_done():
            self.check_finished()
            self._step()

    def mark_route(self):
        while self.route:
            step = self.route.pop(-1)
            if self.maze.out_of_bounds(*step):
                continue
            self.maze.set_current(*step, append=True)
            return
        self._step = None

    def check_finished(self):
        if not self.finished and self.route[-1] == self.maze.end:
            self.maze.clear_current()
            self._step = self.mark_route
            self.finished = True

    def take_step(self, x, y):  # _take_step
        self.maze[x, y].visited = True
        self.maze.set_current(x, y)


class All_Left(Solver_Base):
    visible = True
    display = "All Left"

    def __init__(self, maze, watch):
        super().__init__(maze, watch)
        self._step = self.all_left_step

    def all_left_step(self):
        x1, y1 = self.route[-1]
        x2, y2 = self.route[-2]
        dx, dy = x1 - x2, y1 - y2
        if dx:
            if dx > 0:
                start = 4
            else:
                start = 2
        if dy:
            if dy > 0:
                start = 1
            else:
                start = 3
        dirs = [DIRECTION((start - i) % 4) for i in range(3)]

        # Try to turn left
        left = dirs.pop(0)
        if self.maze[x1, y1].neighbors[left.value] is not None:
            tx, ty = maze_utils.take_step(left, x1, y1)
            self.take_step(tx, ty)
            self.route.append([tx, ty])
            return

        # Try to move forward
        tx, ty = x1 + dx, y1 + dy
        if self.maze[x1, y1].neighbors[(start + 1) % 4] is not None:
            self.take_step(tx, ty)
            self.route.append([tx, ty])
            return

        # Try to pick a new direction and take a step
        for dir in dirs:
            tx, ty = maze_utils.take_step(dir, x1, y1)
            if [tx, ty] == [x2, y2]:
                continue
            if self.maze[x1, y1].neighbors[dir.value] is not None:
                self.take_step(tx, ty)
                self.route.append([tx, ty])
                return

        # Have to turn around
        self.take_step(x2, y2)
        self.route.extend([[x1, y1], [x2, y2]])


class Depth_First(Solver_Base):
    visible = True
    display = "Depth First"

    def __init__(self, maze, watch):
        super().__init__(maze, watch)
        self._step = self._step.depth_first_step

    def depth_first_step(self):
        x1, y1 = self.route[-1]

        # Try to move forward
        try:
            x2, y2 = self.route[-2]
            dx, dy = x1 - x2, y1 - y2
            if dx != 0:
                if dx > 0:
                    direction = DIRECTION.RIGHT
                else:
                    direction = DIRECTION.LEFT
            else:
                if dy > 0:
                    direction = DIRECTION.BOTTOM
                else:
                    direction = DIRECTION.TOP
            tx, ty = x1 + dx, y1 + dy
        # We reached our starting cell
        except IndexError:
            direction = maze_utils.opposite(self.maze.start_side)
            tx, ty = maze_utils.take_step(direction, x1, y1)

        if (
            self.maze[x1, y1].neighbors[direction.value] is not None
            and not self.maze.isVisited(tx, ty)
            and [tx, ty] not in self.route
        ):
            self.take_step(tx, ty)
            self.route.append([tx, ty])
            return

        # Try to pick a new direction
        for dir_int in range(4):
            if dir_int == direction.value:
                continue
            tx, ty = maze_utils.take_step(dir_int, *self.route[-1])
            if (
                self.maze[x1, y1].neighbors[dir_int] is not None
                and not self.maze.isVisited(tx, ty)
                and [tx, ty] not in self.route
            ):
                self.take_step(tx, ty)
                self.route.append([tx, ty])
                return
        # Unroll route
        x0, y0 = self.route.pop(-1)
        self.maze[x0, y0].closed = True
        self.take_step(x0, y0)


class A_Star(Solver_Base):
    visible = True
    display = "A*"

    def __init__(self, maze, watch):
        super().__init__(maze, watch)
        self._step = self.a_step
        self.dist_map = {}
        self.node = None

    def set_up(self):
        super().set_up()
        if self.maze.maze is None:
            return
        x, y = self.maze.start
        newNode = maze_utils.TreeNode(self.maze[x, y], self.maze.start)
        self.dist_map.setdefault(newNode.dist_to(*self.maze.end), list()).append(
            newNode
        )

    def check_finished(self):
        if self.finished:
            return
        minDist = min(self.dist_map.keys())
        node = self.dist_map[minDist][random.randrange(len(self.dist_map[minDist]))]
        if node.pos == self.maze.end:
            self.maze.clear_current()
            self._step = self.mark_route
            self.finished = True
            self.node = node

    def a_step(self):
        minDist = min(self.dist_map.keys())
        node = self.dist_map[minDist].pop(random.randrange(len(self.dist_map[minDist])))

        self.take_step(*node.pos)
        if not self.dist_map[minDist]:
            self.dist_map.pop(minDist)
        for dir, neighbor in enumerate(node.cell.neighbors):
            if neighbor is None or neighbor == -1 or neighbor.visited:
                continue
            tx, ty = maze_utils.take_step(dir, *node.pos)
            newChild = maze_utils.TreeNode(neighbor, [tx, ty])
            node.add_child(newChild)
            self.dist_map.setdefault(newChild.dist_to(*self.maze.end), list()).append(
                newChild
            )

    def mark_route(self):
        while self.node:
            self.maze.set_current(*self.node.pos, append=True)
            self.node = self.node.parent
            return
        self._step = None
