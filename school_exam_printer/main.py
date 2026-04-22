"""
SchoolExamPrinter - Автоматизация печати экзаменационных материалов
Точка входа приложения
"""

import sys
import os

# Добавить путь к модулю
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """Точка входа приложения"""
    
    # Настройка высоко DPI
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        pass  # Старая версия PyQt
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("SchoolExamPrinter")
    app.setOrganizationName("SchoolExamPrinter")
    
    # Настройка шрифта
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Создание и показ главного окна
    window = MainWindow()
    window.show()
    
    # Запуск цикла событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
