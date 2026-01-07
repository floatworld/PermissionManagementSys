"""
测试窗口图标
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from UIManagement.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    print("窗口已显示，请查看左上角的图标")
    sys.exit(app.exec_())
