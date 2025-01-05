import random
from enum import Enum
from time import time

glRand = random.Random()


class DIRECTION(Enum):
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3


def carve_path(maze, x0, y0, x1, y1, dir):  # _carve_path
    maze.clear_current()
    maze.set_current(x1, y1)
    maze[x0, y0].add_neighbor(maze[x1, y1], dir)
    maze[x0, y0].visited = True


def create_walk(maze, x, y, dir, break_walls_chance=0, do_carve=True):  # _create_walk
    tx, ty = take_step(dir, x, y)

    if maze.is_start_or_end(tx, ty):
        if do_carve:
            carve_path(maze, x, y, tx, ty, dir)
        return None, None

    if not maze.out_of_bounds(tx, ty):
        if maze.pos_is_unreached(tx, ty):
            if do_carve:
                carve_path(maze, x, y, tx, ty, dir)
            return tx, ty
        else:
            if (glRand.random() * 100.0) < break_walls_chance:
                carve_path(maze, x, y, tx, ty, dir)
    return None, None


def take_step(dir, x, y, opposite=False):  # _dir
    step = 1
    if isinstance(dir, int):
        dir = DIRECTION(dir)
    if opposite:
        dir = opposite(dir)
    if dir == DIRECTION.TOP:
        return x, y - step
    elif dir == DIRECTION.RIGHT:
        return x + step, y
    elif dir == DIRECTION.BOTTOM:
        return x, y + step
    elif dir == DIRECTION.LEFT:
        return x - step, y
    return x, y


def make_direction_list():  # _random
    # random.seed(time())
    dirs = [0, 1, 2, 3]
    glRand.shuffle(dirs)
    return [DIRECTION(dir) for dir in dirs]


def opposite(dir):
    if isinstance(dir, DIRECTION):
        dir = dir.value
    return DIRECTION((dir + 2) % 4)


def combine_sets(sets, cell1, cell2, dir):
    # Both cells have no sets
    if cell1.set == -1 and cell2.set == -1:
        cell1.set = cell2.set = len(sets)
        sets.append([cell1, cell2])
    elif cell1.set == -1:
        sets[cell2.set].append(cell1)
        cell1.set = cell2.set
        setNum = cell2.set
    elif cell2.set == -1:
        sets[cell1.set].append(cell2)
        cell2.set = cell1.set
        setNum = cell1.set
    else:
        loserSet = max(cell1.set, cell2.set)
        setNum = min(cell1.set, cell2.set)
        for cell in sets[loserSet]:
            cell.set = setNum
        sets[setNum].extend(sets[loserSet])
        sets[loserSet] = []
    cell1.add_neighbor(cell2, dir)


class TreeNode:
    def __init__(self, cell, pos) -> None:
        self.parent = None
        self.child = None
        self.cell = cell
        self.pos = pos

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, type(self)):
            return self.pos == __value.pos
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.pos)

    def is_leaf(self):
        return self.child is None

    def add_child(self, childNode):
        self.child = childNode
        childNode.parent = self

    def dist_to(self, x, y):
        x1, y1 = self.pos
        if x >= x1:
            dx = x - x1
        else:
            dx = x1 - x
        if y >= y1:
            dy = y - y1
        else:
            dy = y1 - y

        return dx * dx + dy * dy
