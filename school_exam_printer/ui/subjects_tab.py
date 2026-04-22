"""
Вкладка управления предметами.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QCheckBox, QListWidget, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SubjectsTab(QWidget):
    """Вкладка для управления предметами."""
    
    # Сигнал об изменении данных предметов
    subjects_changed = pyqtSignal()
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс."""
        layout = QVBoxLayout(self)
        
        # Форма добавления предмета
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("История")
        form_layout.addRow("Название:", self.name_edit)
        
        # Список классов для выбора
        self.classes_list = QListWidget()
        self.classes_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        form_layout.addRow("Классы:", self.classes_list)
        
        # Флаг "2 части"
        self.two_parts_check = QCheckBox("Задание состоит из двух частей (для выбранных классов)")
        self.two_parts_check.stateChanged.connect(self._on_two_parts_changed)
        form_layout.addRow("", self.two_parts_check)
        
        # Список классов для выбора тех, у кого 2 части
        self.two_parts_classes_label = QLabel("Классы с двумя частями:")
        self.two_parts_classes_list = QListWidget()
        self.two_parts_classes_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.two_parts_classes_list.setVisible(False)
        self.two_parts_classes_label.setVisible(False)
        form_layout.addRow(self.two_parts_classes_label, self.two_parts_classes_list)
        
        self.add_btn = QPushButton("Добавить предмет")
        self.add_btn.clicked.connect(self._add_subject)
        form_layout.addRow("", self.add_btn)
        
        layout.addLayout(form_layout)
        
        # Таблица предметов
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Название", "Классы", "2 части", "Действия"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)
        layout.addWidget(self.table)
        
        # Обновить таблицу и список классов
        self._refresh_table()
        self._refresh_classes_list()
    
    def _refresh_classes_list(self):
        """Обновить список классов."""
        # Сохранить текущие выбранные элементы
        current_main_selection = [item.text() for item in self.classes_list.selectedItems()]
        current_two_parts_selection = [item.text() for item in self.two_parts_classes_list.selectedItems()]
        
        self.classes_list.clear()
        self.two_parts_classes_list.clear()
        
        for cls in self.config.classes:
            class_id = f"{cls['parallel']}{cls['letter']}"
            self.classes_list.addItem(class_id)
            self.two_parts_classes_list.addItem(class_id)
        
        # Восстановить выделение если возможно
        for i in range(self.classes_list.count()):
            if self.classes_list.item(i).text() in current_main_selection:
                self.classes_list.item(i).setSelected(True)
        
        for i in range(self.two_parts_classes_list.count()):
            if self.two_parts_classes_list.item(i).text() in current_two_parts_selection:
                self.two_parts_classes_list.item(i).setSelected(True)
    
    def _on_two_parts_changed(self, state):
        """Показать/скрыть выбор классов для двух частей."""
        is_checked = (state == Qt.CheckState.Checked)
        self.two_parts_classes_label.setVisible(is_checked)
        self.two_parts_classes_list.setVisible(is_checked)
    
    def _refresh_table(self):
        """Обновить таблицу предметов."""
        self.table.setRowCount(0)
        
        for subject in self.config.subjects:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(subject["name"]))
            
            classes_str = ", ".join(subject["target_classes"])
            self.table.setItem(row, 1, QTableWidgetItem(classes_str))
            
            # Отобразить информацию о двух частях
            if subject.get("has_two_parts"):
                two_parts_classes = subject.get("two_parts_classes", [])
                if two_parts_classes:
                    two_parts_str = f"Да ({', '.join(two_parts_classes)})"
                else:
                    two_parts_str = "Да"
            else:
                two_parts_str = "Нет"
            self.table.setItem(row, 2, QTableWidgetItem(two_parts_str))
            
            # Кнопка удаления
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(
                lambda checked, n=subject["name"]: 
                self._delete_subject(n)
            )
            self.table.setCellWidget(row, 3, delete_btn)
    
    def _add_subject(self):
        """Добавить предмет."""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название предмета")
            return
        
        # Получить выбранные классы
        selected_items = self.classes_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один класс")
            return
        
        target_classes = [item.text() for item in selected_items]
        has_two_parts = self.two_parts_check.isChecked()
        
        # Получить классы с двумя частями (если флаг активен)
        two_parts_classes = []
        if has_two_parts:
            two_parts_items = self.two_parts_classes_list.selectedItems()
            if not two_parts_items:
                QMessageBox.warning(
                    self, "Ошибка",
                    "Выберите хотя бы один класс с двумя частями"
                )
                return
            two_parts_classes = [item.text() for item in two_parts_items]
        
        try:
            self.config.add_subject(name, target_classes, has_two_parts, two_parts_classes)
            self._refresh_table()
            self.subjects_changed.emit()  # Уведомить об изменении
            self.name_edit.clear()
            self.two_parts_check.setChecked(False)
            self.two_parts_classes_list.clearSelection()
            QMessageBox.information(self, "Успех", f"Предмет '{name}' добавлен")
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _delete_subject(self, name: str):
        """Удалить предмет."""
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить предмет '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.remove_subject(name)
            self._refresh_table()
            self.subjects_changed.emit()  # Уведомить об изменении
    
    def refresh_all(self):
        """Обновить все данные."""
        self._refresh_table()
        self._refresh_classes_list()
