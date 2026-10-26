import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication


class QtTestCase(unittest.TestCase):
    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.app = QApplication.instance() or QApplication([])
