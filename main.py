import sys
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.settings_manager import SettingsManager


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    Получить абсолютный путь к ресурсу, работает для разработки и для EXE
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    path = os.path.join(base_path, relative_path)

    # Для отладки (можно удалить после проверки)
    if not os.path.exists(path):
        print(f"⚠️ Resource not found: {path}")
        if hasattr(sys, '_MEIPASS'):
            print(f"📁 _MEIPASS contents: {os.listdir(base_path)}")
            resources_path = os.path.join(base_path, "resources")
            if os.path.exists(resources_path):
                print(f"📁 Resources contents: {os.listdir(resources_path)}")

    return path


def main():
    # Инициализация настроек с правильными путями
    settings = SettingsManager()
    # Создание приложения
    app = QApplication(sys.argv)
    # Создание главного окна
    window = MainWindow(settings)
    # Установка иконки окна с правильным путем
    icon_path = resource_path("resources/icons/app_icon.png")
    window.setWindowIcon(QIcon(icon_path))
    # Установка иконки для всего приложения
    app.setWindowIcon(QIcon(icon_path))
    # Показ окна
    window.show()
    # Запуск приложения
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
