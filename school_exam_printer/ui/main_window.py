"""
Главное окно приложения.
"""
import sys
import os
from pathlib import Path

# Добавляем корень проекта в путь если нужно
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QApplication
)
from PyQt6.QtCore import Qt

from ui.classes_tab import ClassesTab
from ui.subjects_tab import SubjectsTab
from ui.printers_tab import PrintersTab
from ui.assignments_tab import AssignmentsTab
from ui.print_calc_tab import PrintCalcTab

from core.config import Config
from printers.manager import PrinterManager
from utils.logger import Logger


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    CONFIG_FILE = "config.json"
    
    def __init__(self):
        super().__init__()
        
        self.config = Config()
        self.printer_manager = PrinterManager()
        self.logger = Logger()
        
        self._setup_ui()
        self._load_config()
        self.logger.log_startup()
    
    def _setup_ui(self):
        """Настроить интерфейс."""
        self.setWindowTitle("SchoolExamPrinter - Автоматизация печати экзаменационных материалов")
        self.setMinimumSize(900, 700)
        
        # Центральное виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Вкладки
        self.tabs = QTabWidget()
        
        self.classes_tab = ClassesTab(self.config)
        self.subjects_tab = SubjectsTab(self.config)
        self.printers_tab = PrintersTab(self.config, self.printer_manager)
        self.assignments_tab = AssignmentsTab(self.config)
        self.print_calc_tab = PrintCalcTab(self.config, self.printer_manager)
        
        self.tabs.addTab(self.classes_tab, "Классы")
        self.tabs.addTab(self.subjects_tab, "Предметы")
        self.tabs.addTab(self.printers_tab, "Принтеры")
        self.tabs.addTab(self.assignments_tab, "Задания")
        self.tabs.addTab(self.print_calc_tab, "Расчёт и Печать")
        
        layout.addWidget(self.tabs)
        
        # Подключить сигналы для автообновления вкладок
        self.classes_tab.classes_changed.connect(self._on_classes_changed)
        self.subjects_tab.subjects_changed.connect(self._on_subjects_changed)
        
        # Меню
        self._create_menu()
    
    def _on_classes_changed(self):
        """Обработчик изменения классов - обновить зависимые вкладки."""
        self.subjects_tab.refresh_all()
        self.assignments_tab.refresh_all()
        self.print_calc_tab.refresh_data()
        # Обновить subjects_tab после refresh_all для корректного отображения двух частей
        self.subjects_tab._refresh_table()
    
    def _on_subjects_changed(self):
        """Обработчик изменения предметов - обновить зависимые вкладки."""
        self.assignments_tab.refresh_all()
        self.print_calc_tab.refresh_data()
    
    def _create_menu(self):
        """Создать меню."""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu("Файл")
        
        save_action = file_menu.addAction("Сохранить конфигурацию")
        save_action.triggered.connect(self._save_config)
        save_action.setShortcut("Ctrl+S")
        
        load_action = file_menu.addAction("Загрузить конфигурацию...")
        load_action.triggered.connect(self._load_config_dialog)
        load_action.setShortcut("Ctrl+O")
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        
        # Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self._show_about)
    
    def _load_config(self):
        """Загрузить последнюю конфигурацию."""
        last_config = self.config.settings.get("last_config_path", "")
        
        if last_config and os.path.exists(last_config):
            try:
                self.config.load(last_config)
                self._refresh_all_tabs()
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
    
    def _load_config_dialog(self):
        """Диалог загрузки конфигурации."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить конфигурацию",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.config.load(file_path)
                self._refresh_all_tabs()
                QMessageBox.information(self, "Успех", "Конфигурация загружена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {e}")
    
    def _save_config(self):
        """Сохранить конфигурацию."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить конфигурацию",
            self.CONFIG_FILE,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.config.save(file_path)
                QMessageBox.information(self, "Успех", "Конфигурация сохранена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")
    
    def _refresh_all_tabs(self):
        """Обновить все вкладки."""
        self.classes_tab._refresh_table()
        self.subjects_tab.refresh_all()
        self.printers_tab._refresh_printers()
        self.assignments_tab.refresh_all()
    
    def closeEvent(self, event):
        """Обработка закрытия окна."""
        # Автосохранение
        try:
            self.config.save()
        except Exception as e:
            print(f"Ошибка автосохранения: {e}")
        
        # Очистка временных файлов
        from pdf.processor import PDFProcessor
        pdf_processor = PDFProcessor(self.config.get_temp_dir())
        pdf_processor.cleanup_temp_files()
        
        self.logger.log_shutdown()
        event.accept()
    
    def _show_about(self):
        """Показать информацию о программе."""
        QMessageBox.about(
            self,
            "О программе",
            "SchoolExamPrinter v1.0\n\n"
            "Автоматизация печати экзаменационных материалов.\n\n"
            "Позволяет:\n"
            "- Управлять классами и предметами\n"
            "- Настраивать принтеры\n"
            "- Привязывать PDF файлы к заданиям\n"
            "- Автоматически рассчитывать тиражи\n"
            "- Выполнять тихую печать через SumatraPDF"
        )


def main():
    """Точка входа приложения."""
    app = QApplication(sys.argv)
    
    # Стиль
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
