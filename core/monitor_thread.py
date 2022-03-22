import os
from threading import Thread
from time import time
import traceback
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from qr_detect.correct_answer import AnswercardCorrect

'''
    自动上传app class
'''

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


class DirMonitor_Thread(Thread):
    '''生产者'''

    def __init__(self, monitorDir, myqueue) -> None:
        super().__init__()
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

class DirfileConsumer_Thread(Thread):
    def __init__(self, myqueue) -> None:
        super().__init__()
        self.queue = myqueue
        self.answercardCorrect = AnswercardCorrect()
        self.working = True

    def run(self) -> None:
        '''消费 图片'''
        count = 0
        while self.working:
            srcimgPath = self.queue.get()
            print('-----------')
            self.sleep(1)
            _,qr_dict,page_no = self.answercardCorrect.predict(srcimgPath)
            imgname = os.path.split(srcimgPath)[-1]

            if len(qr_dict):
                uuid = list(qr_dict.values())[0]
            else:
                uuid = ''
            
            if not isinstance(page_no,int):
                page_no = 0

            # 开始上传文件
            if  uuid:
                try:
                    # uploadHomework(srcimgPath,uuid)
                    # 先上传图片,然后判题
                    # uploadPic(srcimgPath,count)
                    count += 1
                except:
                    logging.error(traceback.format_exc())
                    logging.error('-------上传图片失败----------')
                else:
                    logging.info(f'-------{imgname},上传图片成功----------')
            else:
                logging.error('-------无uuid 导致上传图片失败----------')


if __name__ == "__main__":
    from queue import Queue
    import time
    myqueue = Queue()
    dirMonitor_thread = DirMonitor_Thread("C:/Users/W10/Pictures",myqueue)
    dirMonitor_thread.start()

    while True:
        time.sleep(1)


