import inspect
import random

from Qt.QtCore import QPointF, QRectF, Qt
from Qt.QtGui import QColor, qRgb
from Qt.QtWidgets import QGraphicsItem

from . import generators, solvers
from .maze_utils import DIRECTION, glRand, opposite

GENERATORS = [
    [c.display, c]
    for _, c in inspect.getmembers(generators, inspect.isclass)
    if c.__module__ == generators.__name__ and c.visible
]

SOLVERS = [
    [c.display, c]
    for _, c in inspect.getmembers(solvers, inspect.isclass)
    if c.__module__ == solvers.__name__ and c.visible
]


class Cell(QGraphicsItem):
    mult = 1.0

    def __init__(self, offset):
        super(Cell, self).__init__(None)
        self._neighbors = [None, None, None, None]
        self._visited = False
        self._current = False
        self._checking = False
        self._closed = False
        self._set = -1
        self._inc = 0
        self._rand = offset

    @property
    def visited(self):
        return self._visited

    @visited.setter
    def visited(self, value):
        self._visited = value
        self.update(self.boundingRect())

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        if value and self.current:
            self._inc += 1
        else:
            self._inc = 0
        self._current = value
        self.update(self.boundingRect())

    @property
    def closed(self):
        return self._closed

    @closed.setter
    def closed(self, value):
        self._closed = value
        self.update(self.boundingRect())

    @property
    def set(self):
        return self._set

    @set.setter
    def set(self, value):
        self._set = value
        self.update(self.boundingRect())

    @property
    def neighbors(self):
        return self._neighbors

    def neighbor(self, dir):
        if isinstance(dir, DIRECTION):
            dir = dir.value
        return self._neighbors[dir]

    def __getitem__(self, key):
        # neighbors, visited, current, checking, closed, set
        if key == 3:  # checking
            return self._checking
        elif key == 4:  # closed
            return self._checking
        raise ValueError("Can't access that way")

    def __setitem__(self, key, value):
        # neighbors, visited, current, checking, closed, set
        if key == 3:
            self._checking = value
            self.update(self.boundingRect())
        elif key == 4:
            return self._closed
        raise ValueError("Can't access that way")

    def add_neighbor(self, cell, direction):
        self._neighbors[direction.value] = cell
        self.update(self.boundingRect())
        cell._neighbors[opposite(direction).value] = self
        cell.update(cell.boundingRect())

    def clear_state(self):
        self._visited = False
        self._current = False
        self._checking = False
        self._closed = False
        self._set = -1
        self.update(self.boundingRect())

    @staticmethod
    def boundingRect():
        return QRectF(0, 0, Cell.mult, Cell.mult)

    def paint(self, painter, option, widget):
        painter.fillRect(option.rect, QColor(0, 0, 0))
        rect = option.exposedRect
        if self._current:
            painter.fillRect(rect, Qt.green)
            overlay = QColor(Qt.yellow)
            overlay.setAlpha(200)
            for _ in range(self._inc):
                painter.fillRect(rect, overlay)
        elif self._closed:
            painter.fillRect(rect, Qt.red)
        elif self._visited:
            painter.fillRect(rect, QColor(255, 150, 203))
        elif self._checking:
            painter.fillRect(rect, Qt.white)
        elif self._set != -1:
            random.seed(self._set + self._rand)
            setColor = QColor(
                random.randrange(255), random.randrange(255), random.randrange(255)
            )
            painter.fillRect(rect, setColor)
        elif all(dir is None for dir in self._neighbors):
            painter.fillRect(rect, Qt.gray)
        else:
            painter.fillRect(rect, Qt.white)

        lineW = 0.1 * Cell.mult
        pen = painter.pen()
        pen.setColor(QColor(Qt.black))
        pen.setWidthF(lineW)
        painter.setPen(pen)
        tl = QPointF(0 + lineW * 0.5, 0 + lineW * 0.5)
        tr = QPointF(Cell.mult - lineW * 0.5, 0 + lineW * 0.5)
        br = QPointF(Cell.mult - lineW * 0.5, Cell.mult - lineW * 0.5)
        bl = QPointF(0 + lineW * 0.5, Cell.mult - lineW * 0.5)

        if self._neighbors[0] is None:
            painter.drawLine(tl, tr)
        if self._neighbors[1] is None:
            painter.drawLine(tr, br)
        if self._neighbors[2] is None:
            painter.drawLine(br, bl)
        if self._neighbors[3] is None:
            painter.drawLine(bl, tl)

    def __repr__(self) -> str:
        return "<Cell ({}, {}): {}>".format(
            int(self.pos().x()), int(self.pos().y()), self.set
        )


class Maze:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.maze = None
        self.start = None
        self.end = None
        self.start_side = DIRECTION.TOP
        self.end_side = DIRECTION.BOTTOM
        self.current = []

    @staticmethod
    def _make_maze(x, y):
        maze = []
        offset = glRand.randint(-(2**64), 2**64)
        for i in range(x):
            row = []
            for j in range(y):
                new = Cell(offset)
                new.setPos(i * Cell.mult, j * Cell.mult)
                row.append(new)
            maze.append(row)
        return maze

    def set_bounds(self, x, y):
        self.x = x
        self.y = y
        self.maze = self._make_maze(self.x, self.y)
        self.start = list(self.open_goal(self.start_side))
        self.end = list(self.open_goal(self.end_side))

    def open_goal(self, wall):
        # find the y side opening cell
        if wall.value % 2:
            value = glRand.randint(0, self.y - 1)
        # find the x side opening cell
        else:
            value = glRand.randint(0, self.x - 1)

        if wall == DIRECTION.TOP:
            x = value
            y = 0
        elif wall == DIRECTION.RIGHT:
            x = self.x - 1
            y = value
        elif wall == DIRECTION.BOTTOM:
            x = value
            y = self.y - 1
        elif wall == DIRECTION.LEFT:
            x = 0
            y = value

        self.maze[x][y]._neighbors[wall.value] = -1
        return x, y

    def __getitem__(self, pos):
        if len(pos) == 2:
            return self.maze[pos[0]][pos[1]]

    def out_of_bounds(self, x, y):
        """Checks if indices are out of bounds."""
        return x < 0 or x >= self.x or y < 0 or y >= self.y

    def is_start_or_end(self, x, y):
        return [x, y] in (self.start, self.end)

    def pos_is_unreached(self, x, y):
        return all(n in (None, -1) for n in self.maze[x][y].neighbors)

    def isVisited(self, x, y):
        return self.maze[x][y].visited

    def isWall(self, x, y, direction):
        return self.maze[x][y].neighbors[direction] is None

    def cellsBetween(self, sX, sY, dX, dY):
        if sX < dX:
            minX, maxX = sX + 1, dX + 1
        else:
            minX, maxX = dX, sX
        if sY < dY:
            minY, maxY = sY + 1, dY + 1
        else:
            minY, maxY = dY, sY
        if minX == maxX:
            maxX += 1
        if minY == maxY:
            maxY += 1
        for x in range(minX, maxX):
            for y in range(minY, maxY):
                yield x, y

    def allCells(self):
        if self.maze is None:
            return []
        for x in range(0, self.x):
            for y in range(0, self.y):
                yield self[x, y]

    def set_current(self, x, y, append=False):
        currentCell = self.maze[x][y]
        if append:
            self.current.append(currentCell)
        else:
            self.clear_current()
            self.current = [
                currentCell,
            ]
        currentCell.current = True

    def clear_current(self):
        for cell in self.current:
            cell.current = False
        self.current = []
