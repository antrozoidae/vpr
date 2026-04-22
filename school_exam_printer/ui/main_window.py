"""
Главное окно приложения
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
    QMenuBar, QMenu, QAction, QMessageBox, QFileDialog,
    QApplication, QToolBar, QLabel, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

from ..core.config import AppConfig
from .tabs.classes_tab import ClassesTab
from .tabs.subjects_tab import SubjectsTab
from .tabs.printers_tab import PrintersTab
from .tabs.assignments_tab import AssignmentsTab
from .tabs.print_tab import PrintTab


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        
        self.config = AppConfig.create_empty()
        self.current_file: Optional[str] = None
        
        self._init_ui()
        self._init_menu()
        self._init_statusbar()
        
        # Попытка загрузить последнюю конфигурацию
        self._try_load_last_config()
    
    def _init_ui(self) -> None:
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("SchoolExamPrinter - Автоматизация печати экзаменов")
        self.setMinimumSize(1024, 768)
        
        # Центральный виджет с вкладками
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Создание вкладок
        self.classes_tab = ClassesTab(self.config)
        self.subjects_tab = SubjectsTab(self.config)
        self.printers_tab = PrintersTab(self.config)
        self.assignments_tab = AssignmentsTab(self.config)
        self.print_tab = PrintTab(self.config)
        
        self.tabs.addTab(self.classes_tab, "📚 Классы")
        self.tabs.addTab(self.subjects_tab, "📝 Предметы")
        self.tabs.addTab(self.printers_tab, "🖨️ Принтеры")
        self.tabs.addTab(self.assignments_tab, "📁 Задания")
        self.tabs.addTab(self.print_tab, "⚙️ Расчёт и Печать")
        
        # Сигналы между вкладками
        self._connect_tabs()
    
    def _connect_tabs(self) -> None:
        """Подключить сигналы между вкладками"""
        # При изменении матрицы классов обновляем предметы и задания
        self.classes_tab.data_changed.connect(self._on_classes_changed)
        
        # При изменении предметов обновляем задания
        self.subjects_tab.data_changed.connect(self._on_subjects_changed)
        
        # При изменении принтеров обновляем расчёт
        self.printers_tab.data_changed.connect(self._on_printers_changed)
        
        # При изменении заданий обновляем расчёт
        self.assignments_tab.data_changed.connect(self._on_assignments_changed)
    
    def _init_menu(self) -> None:
        """Инициализация меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        new_action = QAction("📄 Новый", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_config)
        file_menu.addAction(new_action)
        
        open_action = QAction("📂 Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_config)
        file_menu.addAction(open_action)
        
        save_action = QAction("💾 Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_config)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("💾 Сохранить как...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_config_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Настройки
        settings_menu = menubar.addMenu("Настройки")
        
        sumatra_action = QAction("🔧 Путь к SumatraPDF...", self)
        sumatra_action.triggered.connect(self._set_sumatra_path)
        settings_menu.addAction(sumatra_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_statusbar(self) -> None:
        """Инициализация строки состояния"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.status_label = QLabel("Готов")
        self.statusbar.addWidget(self.status_label)
    
    def _update_status(self, message: str) -> None:
        """Обновить статус бар"""
        self.status_label.setText(message)
        self.statusbar.showMessage(message, 5000)
    
    def _try_load_last_config(self) -> None:
        """Попытка загрузить последнюю конфигурацию"""
        import json
        last_config_file = Path.home() / ".school_exam_printer" / "last_config.json"
        
        if last_config_file.exists():
            try:
                with open(last_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_path = data.get("last_config_path")
                    
                    if last_path and Path(last_path).exists():
                        self._load_config_file(last_path)
                        self._update_status(f"Загружено: {last_path}")
            except Exception as e:
                print(f"Ошибка загрузки последней конфигурации: {e}")
    
    def _save_last_config_path(self, path: str) -> None:
        """Сохранить путь к последней конфигурации"""
        try:
            config_dir = Path.home() / ".school_exam_printer"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(config_dir / "last_config.json", 'w', encoding='utf-8') as f:
                json.dump({"last_config_path": path}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения пути: {e}")
    
    def _new_config(self) -> None:
        """Создать новую конфигурацию"""
        reply = QMessageBox.question(
            self,
            "Новая конфигурация",
            "Создать новую конфигурацию? Текущие несохранённые изменения будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config = AppConfig.create_empty()
            self.current_file = None
            
            # Обновить все вкладки
            self.classes_tab.refresh()
            self.subjects_tab.refresh()
            self.printers_tab.refresh()
            self.assignments_tab.refresh()
            self.print_tab.refresh()
            
            self._update_status("Создана новая конфигурация")
    
    def _open_config(self) -> None:
        """Открыть конфигурацию из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть конфигурацию",
            "",
            "JSON файлы (*.json);;Все файлы (*)"
        )
        
        if file_path:
            self._load_config_file(file_path)
    
    def _load_config_file(self, file_path: str) -> None:
        """Загрузить конфигурацию из файла"""
        try:
            self.config = AppConfig.load(file_path)
            self.current_file = file_path
            
            # Обновить все вкладки
            self.classes_tab.refresh()
            self.subjects_tab.refresh()
            self.printers_tab.refresh()
            self.assignments_tab.refresh()
            self.print_tab.refresh()
            
            self._save_last_config_path(file_path)
            self._update_status(f"Загружено: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить конфигурацию:\n{str(e)}"
            )
    
    def _save_config(self) -> None:
        """Сохранить конфигурацию"""
        if self.current_file:
            self._do_save_config(self.current_file)
        else:
            self._save_config_as()
    
    def _save_config_as(self) -> None:
        """Сохранить конфигурацию как..."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить конфигурацию",
            "config.json",
            "JSON файлы (*.json)"
        )
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            self._do_save_config(file_path)
    
    def _do_save_config(self, file_path: str) -> None:
        """Выполнить сохранение конфигурации"""
        try:
            # Сначала обновить данные из всех вкладок
            self.classes_tab.save_data()
            self.subjects_tab.save_data()
            self.printers_tab.save_data()
            self.assignments_tab.save_data()
            
            self.config.save(file_path)
            self.current_file = file_path
            
            self._save_last_config_path(file_path)
            self._update_status(f"Сохранено: {file_path}")
            
            QMessageBox.information(
                self,
                "Сохранение",
                f"Конфигурация успешно сохранена в:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить конфигурацию:\n{str(e)}"
            )
    
    def _set_sumatra_path(self) -> None:
        """Установить путь к SumatraPDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите SumatraPDF.exe",
            "",
            "Executable файлы (*.exe);;Все файлы (*)"
        )
        
        if file_path:
            self.config.sumatra_path = file_path
            self._update_status(f"SumatraPDF: {file_path}")
    
    def _show_about(self) -> None:
        """Показать информацию о программе"""
        QMessageBox.about(
            self,
            "О программе",
            "<h2>SchoolExamPrinter v2.0</h2>"
            "<p>Автоматизация печати экзаменационных материалов</p>"
            "<p>© 2024</p>"
            "<p>Функции:</p>"
            "<ul>"
            "<li>Матрица классов и предметов</li>"
            "<li>Автоматический расчёт тиражей</li>"
            "<li>Распределение по принтерам</li>"
            "<li>Склейка многосоставных PDF</li>"
            "<li>Тихая печать через SumatraPDF</li>"
            "</ul>"
        )
    
    def closeEvent(self, event) -> None:
        """Обработка закрытия окна"""
        # Автосохранение конфигурации
        if self.current_file:
            try:
                self._do_save_config(self.current_file)
            except Exception:
                pass
        
        event.accept()
    
    def _on_classes_changed(self) -> None:
        """Изменена матрица классов"""
        self.subjects_tab.refresh()
        self.assignments_tab.refresh()
        self.print_tab.refresh()
        self._update_status("Матрица классов обновлена")
    
    def _on_subjects_changed(self) -> None:
        """Изменена матрица предметов"""
        self.assignments_tab.refresh()
        self.print_tab.refresh()
        self._update_status("Матрица предметов обновлена")
    
    def _on_printers_changed(self) -> None:
        """Изменён список принтеров"""
        self.print_tab.refresh()
        self._update_status("Список принтеров обновлён")
    
    def _on_assignments_changed(self) -> None:
        """Изменены задания"""
        self.print_tab.refresh()
        self._update_status("Задания обновлены")
