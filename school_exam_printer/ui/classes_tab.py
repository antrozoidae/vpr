"""
Вкладка управления классами.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt


class ClassesTab(QWidget):
    """Вкладка для управления классами."""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс."""
        layout = QVBoxLayout(self)
        
        # Форма добавления класса
        form_layout = QFormLayout()
        
        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 11)
        self.parallel_spin.setValue(9)
        form_layout.addRow("Параллель:", self.parallel_spin)
        
        self.letter_edit = QLineEdit()
        self.letter_edit.setMaxLength(1)
        self.letter_edit.setPlaceholderText("А")
        form_layout.addRow("Буква:", self.letter_edit)
        
        self.students_spin = QSpinBox()
        self.students_spin.setRange(1, 50)
        self.students_spin.setValue(25)
        form_layout.addRow("Учеников:", self.students_spin)
        
        self.add_btn = QPushButton("Добавить класс")
        self.add_btn.clicked.connect(self._add_class)
        form_layout.addRow("", self.add_btn)
        
        layout.addLayout(form_layout)
        
        # Таблица классов
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Параллель", "Буква", "Учеников", "Действия"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(3, 100)
        layout.addWidget(self.table)
        
        # Обновить таблицу
        self._refresh_table()
    
    def _refresh_table(self):
        """Обновить таблицу классов."""
        self.table.setRowCount(0)
        
        for cls in self.config.classes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(cls["parallel"])))
            self.table.setItem(row, 1, QTableWidgetItem(cls["letter"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(cls["students"])))
            
            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(
                lambda checked, p=cls["parallel"], l=cls["letter"]: 
                self._delete_class(p, l)
            )
            self.table.setCellWidget(row, 3, delete_btn)
    
    def _add_class(self):
        """Добавить класс."""
        parallel = self.parallel_spin.value()
        letter = self.letter_edit.text().strip().upper()
        students = self.students_spin.value()
        
        if not letter:
            QMessageBox.warning(self, "Ошибка", "Введите букву класса")
            return
        
        try:
            self.config.add_class(parallel, letter, students)
            self._refresh_table()
            QMessageBox.information(self, "Успех", f"Класс {parallel}{letter} добавлен")
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _delete_class(self, parallel: int, letter: str):
        """Удалить класс."""
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить класс {parallel}{letter}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.remove_class(parallel, letter)
            self._refresh_table()
    
    def get_data(self):
        """Получить данные о классах."""
        return self.config.classes
