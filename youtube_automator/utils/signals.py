from PyQt5.QtCore import pyqtSignal, QObject

class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    history_update = pyqtSignal(dict)
    session_update = pyqtSignal(dict)