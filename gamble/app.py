"""Starts the game."""
import sys
import traceback

from PyQt6.QtWidgets import QApplication

from .window import MainWindow


def main():
    sys.excepthook = lambda *a: traceback.print_exception(*a)
    app = QApplication(sys.argv)
    w = MainWindow()          # applies the saved theme and text size itself
    w.show_window()
    sys.exit(app.exec())
