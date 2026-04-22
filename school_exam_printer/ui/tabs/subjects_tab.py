"""
Вкладка управления матрицей предметов
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QMessageBox, 
    QHeaderView, QCheckBox, QLineEdit, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.config import AppConfig


class SubjectsTab(QWidget):
    """Вкладка управления матрицей предметов"""
    
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
        header_label = QLabel("📝 Предметы")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Разделитель для списка и матрицы
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - список предметов
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        list_header = QLabel("Список предметов:")
        left_layout.addWidget(list_header)
        
        self.subjects_list = QListWidget()
        self.subjects_list.itemClicked.connect(self._on_subject_selected)
        left_layout.addWidget(self.subjects_list)
        
        # Кнопки управления предметами
        btn_layout = QHBoxLayout()
        
        self.add_subject_btn = QPushButton("➕ Добавить")
        self.add_subject_btn.clicked.connect(self._add_subject)
        btn_layout.addWidget(self.add_subject_btn)
        
        self.remove_subject_btn = QPushButton("➖ Удалить")
        self.remove_subject_btn.clicked.connect(self._remove_subject)
        btn_layout.addWidget(self.remove_subject_btn)
        
        left_layout.addLayout(btn_layout)
        splitter.addWidget(left_widget)
        
        # Правая панель - матрица предмета
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.matrix_title = QLabel("Матрица предмета: <выберите предмет>")
        self.matrix_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(self.matrix_title)
        
        desc_label = QLabel(
            "Отметьте классы, которые будут сдавать этот предмет. "
            "Чекбокс '2 части' указывает на необходимость склейки двух PDF файлов."
        )
        desc_label.setWordWrap(True)
        right_layout.addWidget(desc_label)
        
        # Таблица матрицы
        self.matrix_table = QTableWidget()
        self.matrix_table.setColumnCount(len(self.GRADES) * 2 + 1)  # Буквы + 2 части для каждой параллели
        self.matrix_table.setRowCount(len(self.config.letters))
        
        # Настройка заголовков
        self._update_matrix_headers()
        
        # Настройка таблицы
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.matrix_table.verticalHeader().setDefaultSectionSize(35)
        
        right_layout.addWidget(self.matrix_table)
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Заполнение
        self._populate_subjects_list()
        self._populate_matrix()
    
    def _update_matrix_headers(self) -> None:
        """Обновить заголовки матрицы"""
        col = 0
        self.matrix_table.setHorizontalHeaderItem(col, QTableWidgetItem("Класс"))
        col += 1
        
        for grade in self.GRADES:
            for letter in self.config.letters:
                self.matrix_table.setHorizontalHeaderItem(col, QTableWidgetItem(f"{grade}{letter}"))
                col += 1
            
            self.matrix_table.setHorizontalHeaderItem(col, QTableWidgetItem(f"{grade} (2 части)"))
            col += 1
    
    def _populate_subjects_list(self) -> None:
        """Заполнить список предметов"""
        self.subjects_list.clear()
        
        for subject in self.config.subjects:
            item = QListWidgetItem(subject.name)
            self.subjects_list.addItem(item)
        
        if self.config.subjects:
            self.subjects_list.setCurrentRow(0)
    
    def _populate_matrix(self) -> None:
        """Заполнить матрицу предмета"""
        selected_index = self.subjects_list.currentRow()
        
        if selected_index < 0 or not self.config.subjects:
            return
        
        subject = self.config.subjects[selected_index]
        self.matrix_title.setText(f"Матрица предмета: {subject.name}")
        
        self.matrix_table.setRowCount(len(self.config.letters))
        self.matrix_table.setColumnCount(len(self.GRADES) * (len(self.config.letters) + 1) + 1)
        self._update_matrix_headers()
        
        for row, letter in enumerate(self.config.letters):
            # Установка буквы в первый столбец
            letter_item = QTableWidgetItem(letter)
            letter_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            letter_item.setBackground(Qt.GlobalColor.lightGray)
            letter_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont("Arial", 11, QFont.Weight.Bold)
            letter_item.setFont(font)
            self.matrix_table.setItem(row, 0, letter_item)
            
            col = 1
            for grade in self.GRADES:
                # Проверка существования класса
                class_exists = False
                if grade in self.config.classes_matrix:
                    count = self.config.classes_matrix[grade].get(letter, 0)
                    class_exists = count > 0
                
                # Чекбокс выбора класса
                checkbox = QCheckBox()
                checkbox.setEnabled(class_exists)
                
                # Получить текущее состояние из конфигурации
                is_selected = False
                if grade in subject.matrix:
                    selected_letters = subject.matrix[grade].get("selected_letters", [])
                    is_selected = letter in selected_letters
                
                checkbox.setChecked(is_selected and class_exists)
                checkbox.stateChanged.connect(
                    lambda state, r=row, g=grade, l=letter: self._on_checkbox_changed(g, l, state)
                )
                self.matrix_table.setCellWidget(row, col, checkbox)
                col += 1
                
                # Чекбокс "2 части" для параллели (один на строку)
                # Но отображаем только в последней ячейке для этой параллели
                # Для простоты - один чекбокс на параллель в конце
            
            # Чекбокс "2 части" для этой параллели
            two_parts_cb = QCheckBox()
            
            is_two_parts = False
            if self.GRADES[row % len(self.GRADES)] in subject.matrix:
                is_two_parts = subject.matrix[self.GRADES[row % len(self.GRADES)]].get("two_parts", False)
            
            two_parts_cb.setChecked(is_two_parts)
            two_parts_cb.stateChanged.connect(
                lambda state, r=row: self._on_two_parts_changed(r, state)
            )
            
            # Поставим чекбокс 2 части после всех букв для каждой параллели
            # Это будет пересмотрено в упрощённой версии
        
        # Упростим: одна колонка "2 части" справа для каждой параллели
        self._rebuild_matrix_with_two_parts()
    
    def _rebuild_matrix_with_two_parts(self) -> None:
        """Перестроить матрицу с колонками 2 части для каждой параллели"""
        selected_index = self.subjects_list.currentRow()
        
        if selected_index < 0 or not self.config.subjects:
            return
        
        subject = self.config.subjects[selected_index]
        
        # Колонки: Класс + для каждой параллели (буквы + 2 части)
        total_cols = 1 + len(self.GRADES) * (len(self.config.letters) + 1)
        self.matrix_table.setColumnCount(total_cols)
        
        # Заголовки
        self.matrix_table.setHorizontalHeaderItem(0, QTableWidgetItem("Класс"))
        
        col = 1
        for grade in self.GRADES:
            for letter in self.config.letters:
                self.matrix_table.setHorizontalHeaderItem(col, QTableWidgetItem(f"{grade}{letter}"))
                col += 1
            self.matrix_table.setHorizontalHeaderItem(col, QTableWidgetItem(f"{grade}\n2 части"))
            col += 1
        
        # Заполнение
        for row, letter in enumerate(self.config.letters):
            # Буква
            letter_item = QTableWidgetItem(letter)
            letter_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            letter_item.setBackground(Qt.GlobalColor.lightGray)
            letter_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont("Arial", 11, QFont.Weight.Bold)
            letter_item.setFont(font)
            self.matrix_table.setItem(row, 0, letter_item)
            
            col = 1
            for grade_idx, grade in enumerate(self.GRADES):
                # Проверка существования класса
                class_exists = False
                if grade in self.config.classes_matrix:
                    count = self.config.classes_matrix[grade].get(letter, 0)
                    class_exists = count > 0
                
                # Чекбокс выбора класса
                checkbox = QCheckBox()
                checkbox.setEnabled(class_exists)
                
                is_selected = False
                if grade in subject.matrix:
                    selected_letters = subject.matrix[grade].get("selected_letters", [])
                    is_selected = letter in selected_letters
                
                checkbox.setChecked(is_selected and class_exists)
                checkbox.stateChanged.connect(
                    lambda state, g=grade, l=letter: self._on_class_checkbox_changed(g, l, state)
                )
                self.matrix_table.setCellWidget(row, col, checkbox)
                col += 1
                
                # Чекбокс "2 части" - только для первой строки каждой параллели
                if row == 0:
                    two_parts_cb = QCheckBox()
                    
                    is_two_parts = False
                    if grade in subject.matrix:
                        is_two_parts = subject.matrix[grade].get("two_parts", False)
                    
                    two_parts_cb.setChecked(is_two_parts)
                    two_parts_cb.stateChanged.connect(
                        lambda state, g=grade: self._on_two_parts_changed(g, state)
                    )
                    self.matrix_table.setCellWidget(row, col, two_parts_cb)
                else:
                    # Пустая ячейка
                    empty_widget = QWidget()
                    self.matrix_table.setCellWidget(row, col, empty_widget)
                
                col += 1
    
    def _on_class_checkbox_changed(self, grade: str, letter: str, state: int) -> None:
        """Изменён чекбокс выбора класса"""
        if not self.config.subjects:
            return
        
        subject = self.config.subjects[self.subjects_list.currentRow()]
        
        if grade not in subject.matrix:
            subject.matrix[grade] = {"selected_letters": [], "two_parts": False}
        
        selected_letters = subject.matrix[grade].get("selected_letters", [])
        
        if state == Qt.CheckState.Checked.value:
            if letter not in selected_letters:
                selected_letters.append(letter)
        else:
            if letter in selected_letters:
                selected_letters.remove(letter)
        
        subject.matrix[grade]["selected_letters"] = selected_letters
        self.data_changed.emit()
    
    def _on_two_parts_changed(self, grade: str, state: int) -> None:
        """Изменён чекбокс '2 части'"""
        if not self.config.subjects:
            return
        
        subject = self.config.subjects[self.subjects_list.currentRow()]
        
        if grade not in subject.matrix:
            subject.matrix[grade] = {"selected_letters": [], "two_parts": False}
        
        subject.matrix[grade]["two_parts"] = (state == Qt.CheckState.Checked.value)
        self.data_changed.emit()
    
    def _on_subject_selected(self, item: QListWidgetItem) -> None:
        """Выбран предмет в списке"""
        self._rebuild_matrix_with_two_parts()
    
    def _add_subject(self) -> None:
        """Добавить предмет"""
        name, ok = QLineEdit.getText(self, "Новый предмет", "Введите название предмета:")
        
        if ok and name.strip():
            name = name.strip()
            
            # Проверка на дубликат
            for subj in self.config.subjects:
                if subj.name == name:
                    QMessageBox.warning(self, "Ошибка", f"Предмет '{name}' уже существует")
                    return
            
            self.config.add_subject(name)
            self._populate_subjects_list()
            self._rebuild_matrix_with_two_parts()
            self.data_changed.emit()
    
    def _remove_subject(self) -> None:
        """Удалить предмет"""
        selected_index = self.subjects_list.currentRow()
        
        if selected_index < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите предмет для удаления")
            return
        
        subject = self.config.subjects[selected_index]
        
        reply = QMessageBox.question(
            self,
            "Удаление предмета",
            f"Удалить предмет '{subject.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.remove_subject(subject.name)
            self._populate_subjects_list()
            
            if self.config.subjects:
                self.subjects_list.setCurrentRow(0)
                self._rebuild_matrix_with_two_parts()
            else:
                self.matrix_title.setText("Матрица предмета: <нет предметов>")
                self.matrix_table.clear()
            
            self.data_changed.emit()
    
    def refresh(self) -> None:
        """Обновить отображение"""
        self._populate_subjects_list()
        if self.config.subjects:
            self.subjects_list.setCurrentRow(0)
            self._rebuild_matrix_with_two_parts()
    
    def save_data(self) -> None:
        """Сохранить данные"""
        pass
