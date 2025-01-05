import sys

from Qt import QtWidgets

from py_maze.maze import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
