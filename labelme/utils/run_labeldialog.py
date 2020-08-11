# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 11:46:01 2020

@author: MHerzo
"""


from qtpy import QtCore
from qtpy import QtWidgets

from labelme.widgets import LabelDialog

import sys

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()


app = QtWidgets.QApplication(sys.argv)
#win = QtWidgets.QMainWindow()
#win.show()
#win.raise_()
ld = LabelDialog(labels=["a","b","c"], flags={'.*': ['&Not in picture', 'Not in &tissue', '&Rework']})
text, flags, group_id = ld.popUp()
#sys.exit(app.exec_())
#app.exec_()
print(text, flags, group_id )


