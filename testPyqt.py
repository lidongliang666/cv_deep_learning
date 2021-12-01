import sys

from PyQt5 import QtWidgets,QtCore

app= QtWidgets.QApplication(sys.argv)

widgets = QtWidgets.QWidget()
widgets.resize(360,360)
widgets.setWindowTitle('hello, pyqt5')
widgets.show()

sys.exit(app.exec_())