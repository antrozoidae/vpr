"""
Вкладка управления принтерами.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt


class PrintersTab(QWidget):
    """Вкладка для управления принтерами."""
    
    def __init__(self, config, printer_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.printer_manager = printer_manager
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс."""
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel("Выберите активные принтеры из списка доступных:")
        layout.addWidget(info_label)
        
        # Кнопка обновления
        self.refresh_btn = QPushButton("Обновить список принтеров")
        self.refresh_btn.clicked.connect(self._refresh_printers)
        layout.addWidget(self.refresh_btn)
        
        # Таблица принтеров
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Имя", "Статус", "Активен", ""])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        layout.addWidget(self.table)
        
        # Обновить таблицу
        self._refresh_printers()
    
    def _get_status_color(self, status: str) -> str:
        """Получить цвет для статуса."""
        colors = {
            "ready": "green",
            "offline": "red",
            "error": "red",
            "paper_jam": "orange",
            "paper_out": "orange",
            "paused": "gray",
            "unknown": "gray"
        }
        return colors.get(status, "gray")
    
    def _refresh_printers(self):
        """Обновить список принтеров."""
        printers = self.printer_manager.get_all_printers()
        
        self.table.setRowCount(0)
        
        for printer_info in printers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Имя
            name_item = QTableWidgetItem(printer_info["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Статус
            status = printer_info["status"]
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.black)
            # Примечание: для цвета нужен delegate или стилизация
            self.table.setItem(row, 1, status_item)
            
            # Чекбокс активности
            enabled_widget = QWidget()
            enabled_layout = QHBoxLayout(enabled_widget)
            enabled_layout.setContentsMargins(5, 0, 5, 0)
            
            enabled_check = QCheckBox()
            # Найти существующий статус в конфиге
            is_enabled = False
            for p in self.config.printers:
                if p["name"] == printer_info["name"]:
                    is_enabled = p["enabled"]
                    break
            
            enabled_check.setChecked(is_enabled)
            enabled_check.stateChanged.connect(
                lambda state, name=printer_info["name"]: 
                self._toggle_printer(name, state == Qt.CheckState.Checked.value)
            )
            enabled_layout.addWidget(enabled_check)
            enabled_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 2, enabled_widget)
        
        # Синхронизировать с конфигом
        self._sync_config_printers(printers)
    
    def _sync_config_printers(self, printers):
        """Синхронизировать конфигурацию с текущими принтерами."""
        current_names = {p["name"] for p in printers}
        
        # Добавить новые принтеры
        for printer_info in printers:
            self.config.add_printer(printer_info["name"], False)
        
        # Удалить несуществующие (опционально)
        # self.config.printers = [p for p in self.config.printers if p["name"] in current_names]
    
    def _toggle_printer(self, name: str, enabled: bool):
        """Переключить статус принтера."""
        self.config.set_printer_enabled(name, enabled)
    
    def get_enabled_printers(self) -> list:
        """Получить список включённых принтеров."""
        return self.config.get_enabled_printers()
