import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.settings_manager import SettingsManager

def main():
    settings = SettingsManager()
    app = QApplication(sys.argv)
    window = MainWindow(settings)
    window.setWindowIcon(QIcon("resources/icons/app_icon.png"))
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()