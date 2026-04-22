"""
Вкладка управления предметами.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QCheckBox, QListWidget, QComboBox,
    QDialog, QDialogButtonBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal


class TwoPartsDialog(QDialog):
    """Диалог выбора классов, для которых включены 2 части"""
    def __init__(self, available_classes: list, selected_two_parts: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Классы с двумя частями задания")
        self.setMinimumWidth(350)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(
            "Отметьте классы, для которых задание состоит из 2-х частей:\n"
            "(Остальные классы будут печататься как 1 часть)"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.list_widget)
        
        # Заполняем список чекбоксами
        for class_name in sorted(available_classes):
            item = QListWidgetItem(class_name)
            is_checked = class_name in selected_two_parts
            item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_classes(self) -> list:
        result = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                result.append(item.text())
        return result


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
        
        # Кнопка настройки двух частей
        self.btn_two_parts = QPushButton("⚙ Настроить 2 части...")
        self.btn_two_parts.setToolTip("Выберите классы, для которых задание состоит из 2 частей")
        self.btn_two_parts.clicked.connect(self._open_two_parts_dialog)
        self.btn_two_parts.setEnabled(False)
        form_layout.addRow(self.btn_two_parts)
        
        self.lbl_two_parts_info = QLabel("Все классы: 1 часть")
        self.lbl_two_parts_info.setStyleSheet("color: gray; font-style: italic;")
        form_layout.addRow(self.lbl_two_parts_info)
        
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
        
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        layout.addWidget(self.table)
        
        # Обновить таблицу и список классов
        self._refresh_table()
        self._refresh_classes_list()
    
    def _refresh_classes_list(self):
        """Обновить список классов."""
        current_selection = [item.text() for item in self.classes_list.selectedItems()]
        
        self.classes_list.clear()
        
        for cls in self.config.classes:
            class_id = f"{cls['parallel']}{cls['letter']}"
            self.classes_list.addItem(class_id)
        
        # Восстановить выделение если возможно
        for i in range(self.classes_list.count()):
            if self.classes_list.item(i).text() in current_selection:
                self.classes_list.item(i).setSelected(True)
        
        # Обновить состояние кнопки настройки 2 частей
        self._update_two_parts_button_state()
    
    def _update_two_parts_button_state(self):
        """Обновить состояние кнопки настройки 2 частей."""
        has_selected = len(self.classes_list.selectedItems()) > 0
        self.btn_two_parts.setEnabled(has_selected)
    
    def _connect_class_selection(self):
        """Подключить сигнал изменения выделения классов."""
        self.classes_list.itemSelectionChanged.connect(self._update_two_parts_button_state)
    
    def _open_two_parts_dialog(self):
        """Открыть диалог выбора параллелей для 2 частей."""
        subject_name = self.subject_combo.currentText()
        if not subject_name:
            QMessageBox.warning(
                self, "Внимание",
                "Сначала выберите предмет"
            )
            return
        
        subject_data = self.data_manager.get_subject(subject_name)
        if not subject_data:
            return
        
        # Получить выбранные классы предмета
        target_classes = subject_data.get('target_classes', [])
        if not target_classes:
            QMessageBox.information(
                self, "Инфо",
                "Для этого предмета не выбрано ни одного класса."
            )
            return
        
        # Получить уникальные параллели из выбранных классов
        available_parallels = set()
        for cls in self.data_manager.get_classes():
            class_id = f"{cls['parallel']}{cls['letter']}"
            if class_id in target_classes:
                available_parallels.add(cls['parallel'])
        
        if not available_parallels:
            QMessageBox.information(
                self, "Инфо",
                "Не удалось определить параллели для выбранных классов."
            )
            return
        
        sorted_parallels = sorted(list(available_parallels))
        
        # Текущий выбор параллелей с 2 частями
        current_two_parts = subject_data.get('two_parts_parallels', [])
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Настройка 2-х частей для '{subject_name}'")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "Выберите параллели, для которых задание состоит из 2-х частей:"
        ))
        
        checkboxes = {}
        for p in sorted_parallels:
            cb = QCheckBox(f"{p} классы")
            cb.setChecked(p in current_two_parts)
            checkboxes[p] = cb
            layout.addWidget(cb)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_selection = [p for p, cb in checkboxes.items() if cb.isChecked()]
            self.data_manager.update_subject_two_parts_parallels(subject_name, new_selection)
            self._update_two_parts_label(new_selection)
            self.data_changed.emit()
    
    def _update_two_parts_label(self, two_parts_parallels: list):
        """Обновить метку с информацией о 2 частях."""
        if not two_parts_parallels:
            self.lbl_two_parts_info.setText("Все классы: 1 часть")
            self.lbl_two_parts_info.setStyleSheet("color: gray; font-style: italic;")
        else:
            parallels_str = ", ".join(map(str, sorted(two_parts_parallels)))
            self.lbl_two_parts_info.setText(f"2 части для {parallels_str} классов")
            self.lbl_two_parts_info.setStyleSheet("color: blue; font-weight: bold;")
    
    def _refresh_table(self):
        """Обновить таблицу предметов."""
        self.table.setRowCount(0)
        
        for subject in self.config.subjects:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(subject["name"]))
            
            classes_str = ", ".join(subject["target_classes"])
            self.table.setItem(row, 1, QTableWidgetItem(classes_str))
            
            # Отобразить информацию о двух частях (параллели)
            two_parts_parallels = subject.get("two_parts_parallels", [])
            if two_parts_parallels:
                parallels_str = ", ".join(map(str, sorted(two_parts_parallels)))
                two_parts_str = f"Да ({parallels_str} кл.)"
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
        
        # Получить классы с двумя частями (если были выбраны через диалог)
        two_parts_classes = getattr(self, '_pending_two_parts', [])
        
        #has_two_parts = len(two_parts_classes) > 0
        # Флаг has_two_parts теперь определяется наличием two_parts_classes
        has_two_parts = True if two_parts_classes else False
        
        try:
            self.config.add_subject(name, target_classes, has_two_parts, two_parts_classes)
            self._refresh_table()
            self.subjects_changed.emit()  # Уведомить об изменении
            self.name_edit.clear()
            self.classes_list.clearSelection()
            self._pending_two_parts = []
            self.lbl_two_parts_info.setText("Все классы: 1 часть")
            self.lbl_two_parts_info.setStyleSheet("color: gray; font-style: italic;")
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
