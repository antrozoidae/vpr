"""
Вкладка управления матрицей классов
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QSpinBox, QMessageBox, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...core.config import AppConfig


class ClassesTab(QWidget):
    """Вкладка управления матрицей классов"""
    
    data_changed = pyqtSignal()
    
    GRADES = ["5", "6", "7", "8", "9", "10", "11"]
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_label = QLabel("📚 Матрица классов")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Описание
        desc_label = QLabel(
            "Укажите количество учеников в каждом классе. "
            "Пустые ячейки или 0 означают, что класс не существует."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.GRADES) + 1)
        self.table.setRowCount(len(self.config.letters) + 1)
        
        # Настройка заголовков
        self._update_table_headers()
        
        # Настройка таблицы
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(35)
        
        layout.addWidget(self.table)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.add_letter_btn = QPushButton("➕ Добавить букву")
        self.add_letter_btn.clicked.connect(self._add_letter)
        btn_layout.addWidget(self.add_letter_btn)
        
        self.remove_letter_btn = QPushButton("➖ Удалить букву")
        self.remove_letter_btn.clicked.connect(self._remove_letter)
        btn_layout.addWidget(self.remove_letter_btn)
        
        btn_layout.addStretch()
        
        self.clear_btn = QPushButton("🗑️ Очистить таблицу")
        self.clear_btn.clicked.connect(self._clear_table)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Заполнение таблицы
        self._populate_table()
    
    def _update_table_headers(self) -> None:
        """Обновить заголовки таблицы"""
        # Первый столбец - буквы
        self.table.setHorizontalHeaderItem(0, QTableWidgetItem("Класс"))
        
        # Остальные столбцы - параллели
        for i, grade in enumerate(self.GRADES):
            self.table.setHorizontalHeaderItem(i + 1, QTableWidgetItem(f"{grade} класс"))
    
    def _populate_table(self) -> None:
        """Заполнить таблицу данными"""
        self.table.setRowCount(len(self.config.letters))
        self.table.setColumnCount(len(self.GRADES) + 1)
        self._update_table_headers()
        
        for row, letter in enumerate(self.config.letters):
            # Установка буквы в первый столбец
            letter_item = QTableWidgetItem(letter)
            letter_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            letter_item.setBackground(Qt.GlobalColor.lightGray)
            letter_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont("Arial", 11, QFont.Weight.Bold)
            letter_item.setFont(font)
            self.table.setItem(row, 0, letter_item)
            
            # Заполнение ячеек количеством учеников
            for col, grade in enumerate(self.GRADES):
                count = 0
                if grade in self.config.classes_matrix:
                    count = self.config.classes_matrix[grade].get(letter, 0)
                
                spinbox = QSpinBox()
                spinbox.setRange(0, 50)
                spinbox.setValue(count)
                spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
                spinbox.valueChanged.connect(
                    lambda value, r=row, c=col: self._on_cell_changed(r, c, value)
                )
                self.table.setCellWidget(row, col + 1, spinbox)
    
    def _on_cell_changed(self, row: int, col: int, value: int) -> None:
        """Изменена ячейка таблицы"""
        letter = self.config.letters[row]
        grade = self.GRADES[col]
        
        if grade not in self.config.classes_matrix:
            self.config.classes_matrix[grade] = {}
        
        if value > 0:
            self.config.classes_matrix[grade][letter] = value
        else:
            self.config.classes_matrix[grade][letter] = 0
        
        self.data_changed.emit()
    
    def _add_letter(self) -> None:
        """Добавить новую букву класса"""
        letters = set(self.config.letters)
        all_letters = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"
        
        # Найти первую свободную букву
        new_letter = None
        for letter in all_letters:
            if letter not in letters:
                new_letter = letter
                break
        
        if new_letter is None:
            QMessageBox.warning(self, "Ошибка", "Все буквы использованы")
            return
        
        self.config.letters.append(new_letter)
        self.config.letters.sort(key=lambda x: all_letters.index(x) if x in all_letters else 999)
        
        self._populate_table()
        self.data_changed.emit()
    
    def _remove_letter(self) -> None:
        """Удалить последнюю букву"""
        if len(self.config.letters) <= 1:
            QMessageBox.warning(self, "Ошибка", "Должна остаться хотя бы одна буква")
            return
        
        reply = QMessageBox.question(
            self,
            "Удаление буквы",
            f"Удалить букву {self.config.letters[-1]}? Все данные для этой буквы будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            removed_letter = self.config.letters.pop()
            
            # Удалить данные из матрицы
            for grade in self.config.classes_matrix:
                if removed_letter in self.config.classes_matrix[grade]:
                    del self.config.classes_matrix[grade][removed_letter]
            
            self._populate_table()
            self.data_changed.emit()
    
    def _clear_table(self) -> None:
        """Очистить таблицу"""
        reply = QMessageBox.question(
            self,
            "Очистка таблицы",
            "Очистить все значения в таблице?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.classes_matrix = {}
            self._populate_table()
            self.data_changed.emit()
    
    def refresh(self) -> None:
        """Обновить отображение"""
        self._populate_table()
    
    def save_data(self) -> None:
        """Сохранить данные (данные сохраняются автоматически при изменении)"""
        pass
