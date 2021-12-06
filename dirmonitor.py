# coding:utf8#author:lcamry

import os
import traceback


from queue import Queue
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QMessageBox, QTableView
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from qr_detect.correct_answer import AnswercardCorrect
from api import uploadHomework

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
        # self.observer.stop()
        # print('---------ssssssss')
        # 更换被监控的文件夹后
        self.observer.unschedule_all()
        self.monitorDir = monitorDir
        self.observer.schedule(self.event_handler, self.monitorDir, True)
        # self.observer.start()
        # self.start()  # ----》》》》 会调用 run()

    def __del__(self):
        self.observer.stop()

class DirfileConsumer(QThread):
    res_signal = pyqtSignal(str,str,int) # 文件名称 uuid pageno
    uploadfile_ok_signal = pyqtSignal(bool)
    def __init__(self, myqueue,parent = None) -> None:
        super().__init__(parent=parent)
        self.queue = myqueue
        self.answercardCorrect = AnswercardCorrect()
        self.working = True

        # self.save_dir_name = "qt_correct_img"
        # self.save_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0],self.save_dir_name)
        # if not os.path.exists(self.save_dir):
        #     os.makedirs(self.save_dir)

        # print(os.path.realpath(__file__))
    
    def run(self) -> None:
        '''消费 图片'''
        while self.working:
            # if self.queue.empty():
            #     self.sleep(1)
            #     continue

            srcimgPath = self.queue.get()
            print('-----------')
            self.sleep(1)
            _,qr_dict,page_no = self.answercardCorrect.predict(srcimgPath)
            imgname = os.path.split(srcimgPath)[-1]

            # 保存一下 矫正后的图片
            # save_path = os.path.join(self.save_dir,imgname)

            # if not isinstance(correct_img,str):
            #     cv2.imwrite(save_path,correct_img)
            print(qr_dict,'-----------')

            if len(qr_dict):
                uuid = list(qr_dict.values())[0]
            else:
                uuid = ''
            
            if not isinstance(page_no,int):
                page_no = 0
            self.res_signal.emit(imgname,uuid,page_no)

            # 开始上传文件
            if  uuid:
            
                try:
                    uploadHomework(srcimgPath,uuid)
                except:
                    print(traceback.format_exc())
                    self.uploadfile_ok_signal.emit(False)
                else:
                    self.uploadfile_ok_signal.emit(True)
            else:
                self.uploadfile_ok_signal.emit(False)


    # def __del__(self):
    #     self.working = False
        # self.wait()


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
        if self.checkMonitorDir():
            self.dirMonitor_thread.start()

        # 消费者
        self.dirfileConsumer_thread = DirfileConsumer(self.queue)
        self.dirfileConsumer_thread.start()
        self.dirfileConsumer_thread.res_signal.connect(self.get_pic_info)
        self.dirfileConsumer_thread.uploadfile_ok_signal.connect(self.uploadFileOK)

        # self.checkMonitorDir()
    
    def checkMonitorDir(self):
        if  not (self.monitorDir and os.path.exists(self.monitorDir)):
            QMessageBox.about(self,"警告",f"监视的文件夹路径异常：{self.monitorDir}")
            return False
        else:
            return True

    def get_pic_info(self,imgname,uuid,page_no):
        print(imgname,uuid,page_no)
        self.setRowdata(imgname,uuid,page_no)
    
    def uploadFileOK(self,uploadOK):
        print(self.r_rownum)
        if uploadOK:
            self.setRowdata(status="上传成功",rownum=self.r_rownum)
        else:
            self.setRowdata(status="上传失败",rownum=self.r_rownum)

    def chageMonitorDir(self,newMonitorDir):
        self.monitorDir = newMonitorDir
        if self.checkMonitorDir():
            self.dirMonitor_thread.updataMonitorDir(newMonitorDir)
    
    def destroy(self) -> None:
        self.dirMonitor_thread.observer.stop()
        # return super().destroy(destroyWindow=destroyWindow, destroySubWindows=destroySubWindows

    def setRowdata(self,imgname=None,uuid=None,page_no=None,status=None,rownum=None):
        '''设置数据'''
        if rownum is None:
            rownum = self.model.rowCount()

        self.r_rownum = self.model.rowCount()
        print(rownum)

        if not imgname is None:
            self.model.setItem(rownum,0,QStandardItem(imgname))
        
        if not uuid is None:
            self.model.setItem(rownum,1,QStandardItem(uuid))

        if not page_no is None:
            self.model.setItem(rownum,2,QStandardItem(str(page_no)))

        if not status is None:
            self.model.setItem(rownum,3,QStandardItem(status))
    


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
