from Qt import QtCore, QtWidgets

from .maze_obj import GENERATORS, SOLVERS, Cell, Maze


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__(None)
        self.setup_ui()
        self.resize(800, 900)
        self.setup_signals()
        self.timer = QtCore.QTimer()
        self.gen = None
        self.solver = None
        self.maze = Maze()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout2 = QtWidgets.QHBoxLayout()
        self.g_scene = QtWidgets.QGraphicsScene(self)
        self.g_scene.setBackgroundBrush(QtCore.Qt.white)
        self.g_view = QtWidgets.QGraphicsView(self)
        self.g_view.setHorizontalScrollBarPolicy(1)
        self.g_view.setVerticalScrollBarPolicy(1)
        layout.addLayout(layout2)
        layout2.addWidget(self.g_view)
        self.g_view.setScene(self.g_scene)
        layout2 = QtWidgets.QHBoxLayout()
        self.watch = QtWidgets.QCheckBox("Watch")
        self.watch.setChecked(True)
        layout2.addWidget(self.watch)
        label = QtWidgets.QLabel("Ms between steps:")
        layout2.addWidget(label)
        self.step_time = QtWidgets.QLineEdit("3", self)
        layout2.addWidget(self.step_time)
        layout.addLayout(layout2)
        layout2 = QtWidgets.QHBoxLayout()
        self.gen_algo = QtWidgets.QComboBox(self)
        self.gen_algo.addItems([gen[0] for gen in GENERATORS])
        layout2.addWidget(self.gen_algo)
        label = QtWidgets.QLabel("X:")
        layout2.addWidget(label)
        self.x_size = QtWidgets.QLineEdit("15", self)
        layout2.addWidget(self.x_size)
        label = QtWidgets.QLabel("Y:")
        layout2.addWidget(label)
        self.y_size = QtWidgets.QLineEdit("15", self)
        layout2.addWidget(self.y_size)
        label = QtWidgets.QLabel("Break Walls %:")
        layout2.addWidget(label)
        self.break_walls = QtWidgets.QLineEdit("50", self)
        layout2.addWidget(self.break_walls)
        self.make_maze_button = QtWidgets.QPushButton("Generate", self)
        layout2.addWidget(self.make_maze_button)
        layout.addLayout(layout2)
        layout2 = QtWidgets.QHBoxLayout()
        self.solve_algo = QtWidgets.QComboBox(self)
        self.solve_algo.addItems([sol[0] for sol in SOLVERS])
        layout2.addWidget(self.solve_algo)
        self.solve_maze_button = QtWidgets.QPushButton("Solve", self)
        layout2.addWidget(self.solve_maze_button)
        layout.addLayout(layout2)

    def setup_signals(self):
        self.make_maze_button.pressed.connect(self.generate_maze)
        self.solve_maze_button.pressed.connect(self.solve_maze)
        self.watch.stateChanged.connect(self.watch_toggled)

    def watch_toggled(self, state):
        self.step_time.setEnabled(state)

    def generate_maze(self):
        x = int(self.x_size.text())
        y = int(self.y_size.text())
        for cell in self.g_scene.items():
            self.g_scene.removeItem(cell)
        self.maze.set_bounds(x, y)
        for cell in self.maze.allCells():
            self.g_scene.addItem(cell)
        self.g_view.fitInView(
            QtCore.QRectF(0, 0, (x + 1) * Cell.mult, (y + 1) * Cell.mult)
        )
        self.gen = GENERATORS[self.gen_algo.currentIndex()][1](
            self.maze, int(self.break_walls.text()), self.watch.isChecked()
        )
        self.gen.first_step()
        self.timer.singleShot(1, self.cont_maker)

    def solve_maze(self):
        if self.maze.maze is None:
            return
        self.solver = SOLVERS[self.solve_algo.currentIndex()][1](
            self.maze, self.watch.isChecked()
        )
        self.solver.set_up()
        self.timer.singleShot(1, self.cont_solver)

    def cont_maker(self):
        if self.gen.not_done():
            self.gen.step()
            timer = self.step_time.text() or 0
            self.timer.singleShot(int(timer), self.cont_maker)

    def cont_solver(self):
        if self.solver.not_done() and not self.gen.not_done():
            self.solver.step()
            timer = self.step_time.text() or 0
            self.timer.singleShot(int(timer), self.cont_solver)

    def resizeEvent(self, event):
        x = int(self.x_size.text())
        y = int(self.y_size.text())
        self.g_view.fitInView(
            QtCore.QRectF(0, 0, (x + 1) * Cell.mult, (y + 1) * Cell.mult)
        )
