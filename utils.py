import traceback

from PyQt5.QtCore import QThread, pyqtSignal


class ApiNetUtilThread(QThread):
    res_signal = pyqtSignal(dict)
    def __init__(self,taskfun,  parent=None,**kargs) -> None:
        super().__init__(parent=parent)
        self.taskfun = taskfun
        self.args = kargs

    def run(self) -> None:
        status = 1
        try:
            res = self.taskfun(**self.args)
        except:
            status = 0
            res = {}
            print(traceback.format_exc())
        self.res_signal.emit({"status":status,"result":res})