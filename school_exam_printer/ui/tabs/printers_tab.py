"""
Вкладка управления принтерами
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox, QHeaderView, QTableWidget,
    QTableWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...core.config import AppConfig, PrinterConfig


class PrintersTab(QWidget):
    """Вкладка управления принтерами"""
    
    data_changed = pyqtSignal()
    
    DUPLEX_MODES = {
        "none": "Нет",
        "long": "Длинная сторона",
        "short": "Короткая сторона"
    }
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._init_ui()
        self._refresh_printers()
    
    def _init_ui(self) -> None:
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_label = QLabel("🖨️ Принтеры")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Описание
        desc_label = QLabel(
            "Выберите активные принтеры для печати. "
            "Настройте режим дуплекса для каждого принтера."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Таблица принтеров
        self.printers_table = QTableWidget()
        self.printers_table.setColumnCount(4)
        self.printers_table.setHorizontalHeaderLabels([
            "✓", "Принтер", "Статус", "Дуплекс"
        ])
        
        header = self.printers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.printers_table.verticalHeader().setVisible(False)
        self.printers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.printers_table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Обновить список")
        self.refresh_btn.clicked.connect(self._refresh_printers)
        btn_layout.addWidget(self.refresh_btn)
        
        btn_layout.addStretch()
        
        self.select_all_btn = QPushButton("✅ Выбрать все")
        self.select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("❌ Снять выделение")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)
        
        layout.addLayout(btn_layout)
    
    def _refresh_printers(self) -> None:
        """Обновить список принтеров из системы"""
        system_printers = self._get_system_printers()
        
        # Сохранить текущие настройки
        current_printers = {p.name: p for p in self.config.printers}
        
        # Обновить список принтеров в конфигурации
        new_printers = []
        for printer_name in system_printers:
            if printer_name in current_printers:
                new_printers.append(current_printers[printer_name])
            else:
                new_printers.append(PrinterConfig(name=printer_name))
        
        self.config.printers = new_printers
        
        # Перерисовать таблицу
        self._populate_table()
    
    def _get_system_printers(self) -> list:
        """Получить список системных принтеров"""
        try:
            import win32print
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            return [p[2] for p in printers]  # Имя принтера
        except ImportError:
            # Если pywin32 недоступен, вернуть тестовые принтеры
            return ["Microsoft Print to PDF", "OneNote", "Test Printer"]
        except Exception as e:
            print(f"Ошибка получения принтеров: {e}")
            return ["Microsoft Print to PDF", "OneNote"]
    
    def _populate_table(self) -> None:
        """Заполнить таблицу принтерами"""
        self.printers_table.setRowCount(len(self.config.printers))
        
        for row, printer in enumerate(self.config.printers):
            # Чекбокс включения
            enabled_cb = QCheckBox()
            enabled_cb.setChecked(printer.enabled)
            enabled_cb.stateChanged.connect(lambda state, r=row: self._on_enabled_changed(r, state))
            self.printers_table.setCellWidget(row, 0, enabled_cb)
            
            # Имя принтера
            name_item = QTableWidgetItem(printer.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.printers_table.setItem(row, 1, name_item)
            
            # Статус
            status_item = QTableWidgetItem("Готов")
            status_item.setForeground(Qt.GlobalColor.darkGreen)
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.printers_table.setItem(row, 2, status_item)
            
            # Дуплекс
            duplex_combo = QComboBox()
            for mode, label in self.DUPLEX_MODES.items():
                duplex_combo.addItem(label, mode)
            
            duplex_combo.setCurrentText(self.DUPLEX_MODES.get(printer.duplex_mode, "Нет"))
            duplex_combo.currentTextChanged.connect(lambda _, r=row: self._on_duplex_changed(r))
            self.printers_table.setCellWidget(row, 3, duplex_combo)
    
    def _on_enabled_changed(self, row: int, state: int) -> None:
        """Изменён статус включения принтера"""
        if 0 <= row < len(self.config.printers):
            self.config.printers[row].enabled = (state == Qt.CheckState.Checked.value)
            self.data_changed.emit()
    
    def _on_duplex_changed(self, row: int) -> None:
        """Изменён режим дуплекса"""
        if 0 <= row < len(self.config.printers):
            combo = self.printers_table.cellWidget(row, 3)
            if combo:
                mode = combo.currentData()
                self.config.printers[row].duplex_mode = mode
                self.data_changed.emit()
    
    def _select_all(self) -> None:
        """Выбрать все принтеры"""
        for printer in self.config.printers:
            printer.enabled = True
        self._populate_table()
        self.data_changed.emit()
    
    def _deselect_all(self) -> None:
        """Снять выделение со всех принтеров"""
        for printer in self.config.printers:
            printer.enabled = False
        self._populate_table()
        self.data_changed.emit()
    
    def refresh(self) -> None:
        """Обновить отображение"""
        self._refresh_printers()
    
    def save_data(self) -> None:
        """Сохранить данные"""
        pass
