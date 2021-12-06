import os
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    def __init__(self,MainWindow, parent=None):
        super(TrayIcon, self).__init__(parent)
        
        self.ui = MainWindow
        self.setUi()

    def setUi(self):
        self.menu = QMenu()
        self.showAction1 = QAction("显示主界面", self, triggered=self.show_window)
        self.quitAction = QAction("退出", self, triggered=self.quit)

        self.menu.addAction(self.showAction1)
        self.menu.addAction(self.quitAction)
        self.setContextMenu(self.menu)

        # 设置图标
        iconPath = os.path.join(os.path.split(os.path.realpath(__file__))[0],'icon','icon_l.png' )
        self.setIcon(QtGui.QIcon(iconPath))
        self.icon = self.MessageIcon()

        # 把鼠标点击图标的信号和槽连接
        self.activated.connect(self.onIconClicked)

    def show_window(self):
        # print('先正常显示窗口，再变为活动窗口')
        # 若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
        self.ui.showNormal()
        self.ui.activateWindow()

    def quit(self):
        self.ui.closeWin = True
        self.ui.close()
        QtWidgets.qApp.quit()

    def onIconClicked(self, reason):
        if reason == 2 or reason == 3:
            self.show_window()
            # print("左键单机 或者双击了 托盘图标")
            # self.showMessage("Message", "skr at here", self.icon)
            # if self.ui.isMinimized() or not self.ui.isVisible():
            #     #若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
            #     self.ui.showNormal()
            #     self.ui.activateWindow()
            #     self.ui.setWindowFlags(QtCore.Qt.Window)
            #     self.ui.show()
            # else:
            #     #若不是最小化，则最小化
            #     self.ui.showMinimized()
            #     self.ui.setWindowFlags(QtCore.Qt.SplashScreen)
            #     self.ui.show()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = TrayIcon()
    win.show()
    sys.exit(app.exec_())
