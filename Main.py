# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\ui\Main.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

import sys
import os
import json
import logging
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from PyQt5.QtWidgets import QFileDialog, QHeaderView, QMainWindow, QApplication, QMessageBox, QAbstractItemView, QWidget

from configListItem import ConfigList
from utils import ApiNetUtilThread
from api import getHomeworkList
from dirmonitor import QTShowMointorFile
from trayicon import TrayIcon


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):

        with open(configJson_filepath, 'r', encoding='utf-8') as f:
            self.init_config = json.load(f)
        

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(640, 480+200)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.clicked.connect(self.pushButton_click)
        self.pushButton.setGeometry(QtCore.QRect(570, 10, 50, 50))
        self.pushButton.setObjectName("pushButton")

        self.refreshButton = QtWidgets.QPushButton(self.centralwidget)
        self.refreshButton.setGeometry(QtCore.QRect(20, 10, 50, 50))
        self.refreshButton.setObjectName("refreshButton")
        self.refreshButton.setEnabled(False)
        self.refreshButton.clicked.connect(self.refreshHomeworkList)

        # self.model = QStandardItemModel()
        # self.model.setHorizontalHeaderLabels(["作业名称", "作答方式", "发布时间", "提交情况"])
        # self.tableView = QtWidgets.QTableView(self.centralwidget)
        # self.tableView.setModel(self.model)

        # self.tableView.horizontalHeader().setStretchLastSection(True)
        # self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tableView.setEditTriggers(
        #     QAbstractItemView.EditTrigger.NoEditTriggers)

        # self.tableView.doubleClicked.connect(self.tableView_doubleClicked)
        # self.tableView.setGeometry(QtCore.QRect(10, 70, 611, 351))
        # self.tableView.setObjectName("tableView")

        self.showMonitorfile = QTShowMointorFile(
            self.init_config['Monitoredfolders'], parent=self)
        self.showMonitorfile.setGeometry(QtCore.QRect(10, 70, 611, 351+200))

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 640, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        # self.getHomeWorkList_worker = ApiNetUtilThread(
        #     taskfun=getHomeworkList, createUserId=self.init_config['createUserId'])
        # self.getHomeWorkList_worker.res_signal.connect(self.setHomeworkList)
        # self.getHomeWorkList_worker.start()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.closeWin = False

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "展示台"))
        self.pushButton.setText(_translate("MainWindow", "配置"))
        self.refreshButton.setText(_translate("MainWindow", "刷新"))

    def tableView_doubleClicked(self, item):
        print('你选择了', item.row(), item.column(), type(item))
        # self.model.setItem(item.row(),item.column(),QStandardItem("改变"))

    def pushButton_click(self, checked):
        print("配置", self.pushButton.text(), checked)
        # self.pushButton.setText("修改配置")
        self.show_config(self.init_config)

    def show_config(self, configdict):
        configList = ConfigList(configdict, self)
        configList.save_config_signal.connect(self.save_config)
        # configList.config_haschaged_signal.connect(self.refreshHomeworkList)
        # configList.monitordir_haschaged_signal.connect(self.refresMonitorDir)
        configList.show()

    def closeEvent(self, event):
        if self.closeWin:
            event.accept()
            self.showMonitorfile.destroy()
        else:
            self.hide()
            event.ignore()
        # result = QMessageBox.question(
        #     self, "注意：", "您真的要关闭窗体吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if result == QMessageBox.Yes:
        #     event.accept()
        #     self.showMonitorfile.destroy()
        # else:
        #     event.ignore()
        #     QMessageBox.information(self, "消息", "谢谢！")

    def save_config(self, new_configdict):
        init_monitorfile = self.init_config['Monitoredfolders']
        new_monitorfile = new_configdict['Monitoredfolders']

        self.init_config = new_configdict
        print("当前配置为", self.init_config)
        with open(configJson_filepath, 'w', encoding='utf-8') as f:
            json.dump(new_configdict, f, ensure_ascii=False)
        QMessageBox.about(self, "更新配置", "配置保存成功")

        # 如果发现监控文件夹被更改 则需要
        if init_monitorfile != new_monitorfile:
            self.refresMonitorDir()

    def setHomeworkList(self, resdict):
        # 清空一下 原有的数据
        rownum = self.model.rowCount()
        print(rownum)
        if rownum:
            for i in range(rownum):
                # for j in range(colnum):
                self.model.removeRow(0)

        if resdict['status']:
            ''''''
            # print(resdict)
            homeworkList = resdict['result']['result']['data']
            # print(homeworkList)
            self.setTableViewUi(homeworkList)
        else:
            QMessageBox.about(self, '获得作业列表失败', "请检查api:getHomeworkList是否正常工作")

    def setTableViewUi(self, homeworkList):
        self.refreshButton.setEnabled(True)

        if len(homeworkList) == 0:
            print('作业列表为空')
            return

        for i in range(len(homeworkList)):
            info = homeworkList[i]
            homeworkName = info['homeworkName']
            studyFromTime = info['studyFromTime']
            studyEndTime = info['studyEndTime']
            answerType = "纸质作答" if info['answerType'] == "2" else "非纸质作答"
            if "studentStatList" in info:
                studentAmount = sum(i['studentAmount']
                                    for i in info['studentStatList'])
                studentSubmitAmount = sum(
                    i['studentSubmitAmount'] for i in info['studentStatList'])
            else:
                studentAmount = sum(i['studentAmount']
                                    for i in info['statList'])
                studentSubmitAmount = sum(
                    i['studentSubmitAmount'] for i in info['statList'])
            self.model.setItem(i, 0, QStandardItem(homeworkName))
            self.model.setItem(i, 1, QStandardItem(answerType))
            self.model.setItem(i, 2, QStandardItem(
                f"{studyFromTime}-{studyEndTime}"))
            self.model.setItem(i, 3, QStandardItem(
                f"{studentSubmitAmount}-{studentAmount}"))

    def refreshHomeworkList(self):
        # 刷新时 要更新一下 createUserId
        self.getHomeWorkList_worker.args["createUserId"] = self.init_config['createUserId']
        self.refreshButton.setEnabled(False)
        self.getHomeWorkList_worker.start()

    def refresMonitorDir(self):
        self.showMonitorfile.chageMonitorDir(
            self.init_config['Monitoredfolders'])


def checkMonitorDir(monitorDir):
    if not (monitorDir and os.path.exists(monitorDir)):
        return False
    else:
        return True


class MainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainForm, self).__init__()
        # 检测一下 监控文件夹是否正常
        # 不正常 需要选择 一个文件夹
        # 并且更新配置
        with open(configJson_filepath, 'r', encoding='utf-8') as f:
            self.init_config = json.load(f)

        if checkMonitorDir(self.init_config['Monitoredfolders']):
            print("被检测的文件夹存在")
        else:
            '''由于您可能初次启动程序，或者被监控的文件夹在您的计算机上已经不存在，需要您及时设置被监控的文件夹'''
            QMessageBox.about(self, '被检测文件夹异常',
                              '由于您可能初次启动程序，或者被监控的文件夹在您的计算机上已经不存在，需要您及时设置被监控的文件夹')
            while True:
                dir = os.path.expanduser('~')
                print(dir)
                directory = QFileDialog.getExistingDirectory(
                    self, "getExistingDirectory", dir)
                print(directory)
                if not directory is None:
                    new_config = self.init_config
                    new_config['Monitoredfolders'] = directory
                    self.save_config_simple(new_config)
                    break
                
        self.setupUi(self)
        

    def save_config_simple(self, new_configdict):
        print("当前配置为", new_configdict)
        with open(configJson_filepath, 'w', encoding='utf-8') as f:
            json.dump(new_configdict, f, ensure_ascii=False)


if __name__ == "__main__":
    print(os.path.abspath(sys.argv[0]))
    logpath = os.path.join(os.path.split(
        os.path.realpath(__file__))[0], "log.log")
    configJson_filepath = os.path.join(os.path.split(
        os.path.realpath(__file__))[0], "config.json")
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=logpath,
                        filemode='w')

    logging.info(logpath)
    logging.info(configJson_filepath)
    app = QApplication(sys.argv)
    win = MainForm()
    trayicon = TrayIcon(win)
    trayicon.show()
    # 确保配置文件中的 被检查的文件夹
    # info_win = QWidget()
    message = QMessageBox()
    message.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
    message.about(win, '消息', f"作业检测终端成功启动")
    # win.show()
    sys.exit(app.exec_())
