import sys

import PyQt5.QtCore as qc
import PyQt5.QtGui as qg
import PyQt5.QtWidgets as qw

# - Globals - #
gDIALOG = None


class PicoSlicer(qw.QDialog):
    def __init__(self):
        super(PicoSlicer, self).__init__()
        self.setWindowTitle('Pico Slicer 0.1')

    def __call__(self, *args, **kwargs):
        self.show()


class PicoTrack(qw.QWidget):
    def __init__(self):
        super(PicoTrack, self).__init__()


def run():
    """
    Main execution
    """
    app = qw.QApplication(sys.argv)
    # app.setStyleSheet(qdarkstyle.load_stylesheet(pyside=False))
    slicer = PicoSlicer()
    slicer()

    sys.exit(app.exec_())

run()