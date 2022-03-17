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
import json
import requests
from pymysql_comme import get_userid_by_qrid
from pymysql_ai import get_page_info_by_id
import time
import numpy as np
import cv2
def generator_pic(page_info,temp_info,id):
    pic=np.zeros((1756,1242),dtype=np.uint8)
    pic.fill(250)
    for key,value in page_info.items():
        index = key.split("_")
        position = temp_info[index[0]]['position'][int(index[1])]
        pt1Start = [position[0]+position[2],position[1]]
        if value["isCorrect"] == "3":
            pt1End = np.array(pt1Start) + np.array([10,10])
            pt2Start = pt1End
            pt2End = np.array(pt2Start) + np.array([20,-20])
        else:
            pt1End = np.array(pt1Start) + np.array([20,20])
            pt2Start = np.array(pt1Start) + np.array([0,20])
            pt2End = np.array(pt1Start) + np.array([20,0])
        cv2.line(pic,pt1Start,pt1End,(0,0,0),4,1)
        cv2.line(pic,pt2Start,pt2End,(0,0,0),4,1)
    cv2.imwrite(os.path.join("./pic",id+".jpg"),pic)
    # cv2.imshow("pic",pic)
    # cv2.waitKey(0)
    return True

def upload_pic_simple(imgpath, current_model):  # 将图片上传到指定位置
    if current_model == "develop":
        url = "http://124.70.17.227/api/media/api/v1/media/addMedia"
    elif current_model == "preprod":
        url = "http://121.36.71.62/api/media/api/v1/media/addMedia"
    elif current_model == "production":
        url = "http://www.necibook.com/api/media/api/v1/media/addMedia"
    else:
        url = "http://112.126.120.231/api/media/api/v1/media/addMedia"
    # url ="http://121.36.71.62/api/media/api/v1/media/download/"
    # try:
    data = {}
    data["file"] = (imgpath, open(imgpath, "rb"),
                    "image/"+imgpath.split(".")[-1])
    res = requests.post(url, files=data).json()
    if res["code"]:
        print(str("图片%s上传失败" % ( imgpath)))

        return None
    else:
        # 将文件夹下的图片清空
        fileId = res["result"]['id']
        return fileId
def uploadPic(srcPath,count):
    #上传图片获得uuid
    fileId = upload_pic_simple(srcPath,"develop")
    url = "http://192.168.0.74:5014/api/ai_cv/pic_message"
    params = json.dumps([{"fileId":fileId,"recognitionFlag":True}])
    res = requests.post(url, data=params).json()
    print(res)
    #根据二维码id 查找userId
    userId = get_userid_by_qrid(res["result"][0]["printQrId"])

    params = json.dumps([{"pic": [{"fileId":res['result'][0]['fileId'], 'presetUserId':userId,'pageNum':1, 'extraList': res['result'][0]["extraList"]}],'isAnonymous':True,'isExam':False, 'subjectId':'2','examId':'ee7e9da250a7465d897772d9d92b17be','printId':"1ec3daafcb384f5eb161e80d1aa8e1fb",'isExtraInfo':True}])
    url = "http://192.168.0.74:5014/api/ai_cv/pic_judge"
    res = requests.post(url, data=params).json()
    #这里查找下判题结果，然后生成图片，供打印
    for r in res["result"]:
        for pic in r['picList']:
            pageInfo ,temp_info = get_page_info_by_id(pic['fileId'],r['printId'])
            while True:
                time.sleep(1)
                if generator_pic(pageInfo,temp_info,r['printId']+r['examId'] +"_"+ str(count)):
                    break

    return True

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
        count = 0
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
                    # uploadHomework(srcimgPath,uuid)
                    # 先上传图片,然后判题
                    uploadPic(srcimgPath,count)
                    count += 1
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
        self.resize(611, 351+200)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 文件监视器 生产者
        self.monitorDir = monitorDir
        self.queue = Queue()
        self.dirMonitor_thread = DirMonitor(
            monitorDir=self.monitorDir, myqueue=self.queue, parent=self)
        # 如果配置异常 会导致 文件监控者线程起不来 就导致后续 检测不到
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
    # import sys
    # app = QApplication(sys.argv)
    # win = QTShowMointorFile(monitorDir="C:/Users/W10/Pictures")
    # win.show()
    # sys.exit(app.exec_())
    # uploadPic("./03632d574d91435e9319de819550a1a5.jpg")
    temp = {"1": {"answer": "ruler", "test_id": "25f63d78bc6e4c3daff6cd1200087a1b", "position": [[89, 329, 158, 33]], "seniorId": "0", "has_blank": [1], "test_form": "2", "other_info_list": []}, "2": {"answer": "ruler", "test_id": "7b8f1aadde16472aa697946e7e66d272", "position": [[89, 379, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "3": {"answer": "ruler", "test_id": "6501d130f7614587b07ec4f9a8680ed7", "position": [[89, 428, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "4": {"answer": "ruler", "test_id": "a45158b278df469fa8ee0ef24676392a", "position": [[89, 479, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "5": {"answer": "ruler", "test_id": "ffb76a24b74444ecb7d44c97d5d23de1", "position": [[89, 529, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "6": {"answer": "ruler", "test_id": "65d4c9eccc134b1591331953151fc7d6", "position": [[89, 579, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "7": {"answer": "ruler", "test_id": "c256eb28d4bb4a68bfcca82567564696", "position": [[89, 630, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "8": {"answer": "ruler", "test_id": "0c54a368b1e446618a9b7c3b1b3fecb7", "position": [[89, 681, 158, 32]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "9": {"answer": "ruler", "test_id": "790b28d1db95483e8106e145c8876496", "position": [[89, 730, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "10": {"answer": "ruler", "test_id": "9f223b5530e04bfcbacf37e68158913b", "position": [[103, 780, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "11": {"answer": "ruler", "test_id": "55cb8d440f8d4facbbe958d3323a9c9b", "position": [[103, 831, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "12": {"answer": "ruler", "test_id": "443ceb1ce89c454fa12cb0ea83634f20", "position": [[103, 880, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "13": {"answer": "ruler", "test_id": "08b516277f7c4ec8a67fbe7fa43c23b9", "position": [[103, 931, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "14": {"answer": "ruler", "test_id": "0ccba0230bd841d0b20e4ca9e3e0d3c6", "position": [[103, 981, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "15": {"answer": "ruler", "test_id": "e4acf72fd928405caa4abe59de056e8e", "position": [[104, 1033, 157, 32]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "16": {"answer": "ruler", "test_id": "2caacce7c398451aa2e0096278dd16ff", "position": [[103, 1082, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "17": {"answer": "ruler", "test_id": "16d40a49c42c456d813d43bc15a1b012", "position": [[103, 1132, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "18": {"answer": "ruler", "test_id": "d86c8cab79da4deaa7dbb3d0b906c4d4", "position": [[103, 1182, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "19": {"answer": "ruler", "test_id": "8f41dfa1154243d2a8018ba5573cc150", "position": [[103, 1232, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "20": {"answer": "ruler", "test_id": "83c9f55f966240b68a38703dd40288ab", "position": [[103, 1283, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "21": {"answer": "ruler", "test_id": "f4fd74b49de24a5f85e3b9cf085249cb", "position": [[103, 1333, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "22": {"answer": "ruler", "test_id": "957165225e514bd4abd00c35e2adb468", "position": [[104, 1384, 157, 32]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "23": {"answer": "", "test_id": "7ff3a362d14641f2b049c8320a1dbb63", "position": [[103, 1433, 158, 34]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "24": {"answer": "", "test_id": "963d13ece12546c09b8c4d31dd263998", "position": [[103, 1484, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "25": {"answer": "", "test_id": "b64f300056b4464eaf61b5f362209797", "position": [[103, 1534, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}, "26": {"answer": "", "test_id": "bcb4c0d078a54e27b9e57624f1e7ee83", "position": [[103, 1584, 158, 33]], "seniorId": "0", "has_blank": [0], "test_form": "2", "other_info_list": []}}
    page = {"1_0": {"page": 1, "fileId": "9d025a737be349ddb60a5451fdd93d82", "formula": "classroom", "myAnswer": "classroom", "regionId": "1", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9996646046638488, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 52, "w": 148, "x": 104, "y": 315}], "standardAnswer": "ruler"}, "2_0": {"page": 1, "fileId": "6962efe113334de3a1a0e69eecf76be1", "formula": "window", "myAnswer": "window", "regionId": "2", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9992947578430176, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 62, "w": 112, "x": 95, "y": 370}], "standardAnswer": "ruler"}, "3_0": {"page": 1, "fileId": "1dc9a8ecdf9246e4aaee5699140366ff", "formula": "world", "myAnswer": "world", "regionId": "3", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9998592138290404, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 59, "w": 97, "x": 95, "y": 408}], "standardAnswer": "ruler"}, "4_0": {"page": 1, "fileId": "cc9bb9d5ff4442299012afd73db3063d", "formula": "back board", "myAnswer": "back board", "regionId": "4", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.998149275779724, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 50, "w": 163, "x": 89, "y": 468}], "standardAnswer": "ruler"}, "5_0": {"page": 1, "fileId": "f596e023a6764c14b2602c1e307e25ea", "formula": "light", "myAnswer": "light", "regionId": "5", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9999969005584716, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 59, "w": 89, "x": 96, "y": 517}], "standardAnswer": "ruler"}, "6_0": {"page": 1, "fileId": "ba31df9efb6e4250940ae8ec6d30ac29", "formula": "picture", "myAnswer": "picture", "regionId": "6", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9996030926704408, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 43, "w": 110, "x": 99, "y": 575}], "standardAnswer": "ruler"}, "7_0": {"page": 1, "fileId": "75291c0dc4a249628ae52604541fbdc0", "formula": "door", "myAnswer": "door", "regionId": "7", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9947221279144288, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 44, "w": 70, "x": 102, "y": 625}], "standardAnswer": "ruler"}, "8_0": {"page": 1, "fileId": "573facc04f0a4fa38b4015d9964adacc", "formula": "teachey's desk", "myAnswer": "teachey's desk", "regionId": "8", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.97823828458786, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 46, "w": 165, "x": 87, "y": 673}], "standardAnswer": "ruler"}, "9_0": {"page": 1, "fileId": "c8fb1efb0bb54c4b8fc822be3c1b512e", "formula": "computer", "myAnswer": "computer", "regionId": "9", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.999411940574646, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 51, "w": 146, "x": 99, "y": 732}], "standardAnswer": "ruler"}, "10_0": {"page": 1, "fileId": "2c8311d86169461f91f9fafcc933f570", "formula": "Fan", "myAnswer": "Fan", "regionId": "10", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.8019269108772278, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 60, "w": 70, "x": 107, "y": 760}], "standardAnswer": "ruler"}, "11_0": {"page": 1, "fileId": "6d8a4cd0df1a4e11b88699b2c39bdf6d", "formula": "wall", "myAnswer": "wall", "regionId": "11", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9999758005142212, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 53, "w": 73, "x": 113, "y": 817}], "standardAnswer": "ruler"}, "12_0": {"page": 1, "fileId": "c271c7742f7f4968a20d2b442ba68e06", "formula": "floor", "myAnswer": "floor", "regionId": "12", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.9984062314033508, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 46, "w": 84, "x": 115, "y": 874}], "standardAnswer": "ruler"}, "13_0": {"page": 1, "fileId": "10fe2e80cc844b2a9cbd5f827f67360c", "formula": "rule,", "myAnswer": "rule,", "regionId": "13", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.508323609828949, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 43, "w": 99, "x": 114, "y": 927}], "standardAnswer": "ruler"}, "14_0": {"page": 1, "fileId": "09baf5ba4c864579b3664772d7873e11", "formula": "ruler", "myAnswer": "ruler", "regionId": "14", "testForm": "2", "isCorrect": "3", "subjectId": "2", "confidence": 0.4582285881042481, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 45, "w": 104, "x": 119, "y": 975}], "standardAnswer": "ruler"}, "15_0": {"page": 1, "fileId": "564f301016f74378b98d38d30e33b5ea", "formula": "ruler", "myAnswer": "ruler", "regionId": "15", "testForm": "2", "isCorrect": "3", "subjectId": "2", "confidence": -0.2299860417842865, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 50, "w": 100, "x": 121, "y": 1021}], "standardAnswer": "ruler"}, "16_0": {"page": 1, "fileId": "30ecd57149b243e39e8db6a374da9d0d", "formula": "ruler", "myAnswer": "ruler", "regionId": "16", "testForm": "2", "isCorrect": "3", "subjectId": "2", "confidence": 0.9420140385627748, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 51, "w": 109, "x": 119, "y": 1075}], "standardAnswer": "ruler"}, "17_0": {"page": 1, "fileId": "d1393f76d8c546ba816d7c673e34ca0c", "formula": "rule", "myAnswer": "rule", "regionId": "17", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.997418999671936, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 49, "w": 110, "x": 121, "y": 1123}], "standardAnswer": "ruler"}, "18_0": {"page": 1, "fileId": "00bd28fa0cad49518dabd2284c9ce3c3", "formula": "ruler", "myAnswer": "ruler", "regionId": "18", "testForm": "2", "isCorrect": "3", "subjectId": "2", "confidence": 0.8282421231269836, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 51, "w": 107, "x": 121, "y": 1171}], "standardAnswer": "ruler"}, "19_0": {"page": 1, "fileId": "1ef870361e12463799a4214475781616", "formula": "ruler", "myAnswer": "ruler", "regionId": "19", "testForm": "2", "isCorrect": "3", "subjectId": "2", "confidence": 0.925237476825714, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 54, "w": 108, "x": 123, "y": 1225}], "standardAnswer": "ruler"}, "20_0": {"page": 1, "fileId": "10b9056c4db3448987cfea91215eb2d0", "formula": "Yuleyl", "myAnswer": "Yuleyl", "regionId": "20", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.2939051389694214, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 50, "w": 109, "x": 122, "y": 1275}], "standardAnswer": "ruler"}, "21_0": {"page": 1, "fileId": "8adb6e3ad19545bd8dcd69874ffff5d0", "formula": "ruler", "myAnswer": "ruler", "regionId": "21", "testForm": "2", "isCorrect": "3", "subjectId": "2", "confidence": 0.9919412732124328, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 53, "w": 108, "x": 115, "y": 1323}], "standardAnswer": "ruler"}, "22_0": {"page": 1, "fileId": "8a4f2a8d94084fa9a24d2c153f5f0736", "formula": "", "myAnswer": "", "regionId": "22", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 1.0, "modelIndex": "3", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 32, "w": 16, "x": 178, "y": 1384}], "standardAnswer": "ruler"}, "23_0": {"page": 1, "fileId": "78c3229290fd48d2ac345966f7ea2521", "formula": "", "myAnswer": "", "regionId": "23", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.0, "modelIndex": "", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 34, "w": 158, "x": 103, "y": 1433}], "standardAnswer": ""}, "24_0": {"page": 1, "fileId": "44ceb49b0862471799ba010ed72c55b9", "formula": "", "myAnswer": "", "regionId": "24", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.0, "modelIndex": "", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 33, "w": 158, "x": 103, "y": 1484}], "standardAnswer": ""}, "25_0": {"page": 1, "fileId": "e4373280555f4989b7f473f74aebc1b6", "formula": "", "myAnswer": "", "regionId": "25", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.0, "modelIndex": "", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 33, "w": 158, "x": 103, "y": 1534}], "standardAnswer": ""}, "26_0": {"page": 1, "fileId": "c6b8c07d0b19402588ffec1829fd730d", "formula": "", "myAnswer": "", "regionId": "26", "testForm": "2", "isCorrect": "1", "subjectId": "2", "confidence": 0.0, "modelIndex": "", "modifyAnswer": "", "modifyStatus": "", "positionList": [{"h": 33, "w": 158, "x": 103, "y": 1584}], "standardAnswer": ""}}
    generator_pic(page,temp,'1')
