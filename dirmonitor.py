# coding:utf8#author:lcamry
from queue import Queue
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QTableView
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, queue):
        FileSystemEventHandler.__init__(self)
        self.queue = queue

    def on_moved(self, event):
        if event.is_directory:
            print("directory moved from {0} to {1}".format(
                event.src_path, event.dest_path))
        else:
            print("file moved from {0} to {1}".format(
                event.src_path, event.dest_path))

    def on_created(self, event):
        if event.is_directory:
            print("directory created:{0}".format(event.src_path))
        else:
            self.queue.put(event.src_path)
            # print(self.queue)
            print("file created:{0}".format(event.src_path))

    def on_deleted(self, event):
        if event.is_directory:
            print("directory deleted:{0}".format(event.src_path))
        else:
            print("file deleted:{0}".format(event.src_path))

    def on_modified(self, event):
        if event.is_directory:
            print("directory modified:{0}".format(event.src_path))
        else:
            print("file modified:{0}".format(event.src_path))


class DirMonitor(QThread):
    '''生产者'''

    def __init__(self, monitorDir, myqueue, parent=None) -> None:
        super().__init__(parent=parent)
        self.monitorDir = monitorDir
        self.queue = myqueue
        self.observer = Observer() 
        self.event_handler = FileEventHandler(self.queue)

    def run(self) -> None:
        '''启动监控文件夹程序'''
        self.observer.schedule(self.event_handler, self.monitorDir, True)
        self.observer.start()

    def updataMonitorDir(self, monitorDir):
        '''更换监控的文件夹'''
        self.observer.stop()
        # 更换被监控的文件夹后
        self.monitorDir = monitorDir
        self.start()  # ----》》》》 会调用 run()

    def __del__(self):
        self.observer.stop()


class QTShowMointorFile(QTableView):

    def __init__(self, monitorDir,parent=None) -> None:
        super().__init__(parent=parent)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["文件名称", "uuid", "pageno", "备注"])
        self.setModel(self.model)
        self.resize(611, 351)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 文件监视器 生产者
        self.monitorDir = monitorDir
        self.queue = Queue()
        self.dirMonitor_thread = DirMonitor(
            monitorDir=self.monitorDir, myqueue=self.queue, parent=self)
        self.dirMonitor_thread.start()


if __name__ == "__main__":
    # from queue import Queue
    # observer = Observer()
    # myqueue = Queue()
    # event_handler = FileEventHandler(myqueue)
    # observer.schedule(event_handler,"C:/Users/W10/Pictures",True)
    # observer.start()
    # try:
    #     while True:
    #         time.sleep(2)
    # except KeyboardInterrupt:
    #     observer.stop()
    # observer.join()
    import sys
    app = QApplication(sys.argv)
    win = QTShowMointorFile(monitorDir="C:/Users/W10/Pictures")
    win.show()
    sys.exit(app.exec_())
