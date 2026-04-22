"""
Вкладка привязки PDF файлов к заданиям.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt


class AssignmentsTab(QWidget):
    """Вкладка для привязки PDF файлов."""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс."""
        layout = QVBoxLayout(self)
        
        # Выбор предмета
        form_layout = QFormLayout()
        
        self.subject_combo = QComboBox()
        self.subject_combo.currentTextChanged.connect(self._on_subject_changed)
        form_layout.addRow("Предмет:", self.subject_combo)
        
        layout.addLayout(form_layout)
        
        # Группа для файлов варианта 1
        variant1_group = QGroupBox("Вариант 1")
        variant1_layout = QFormLayout()
        
        self.v1_part1_edit = QLineEdit()
        self.v1_part1_btn = QPushButton("Выбрать файл...")
        self.v1_part1_btn.clicked.connect(
            lambda: self._select_file(self.v1_part1_edit, "variant_1", "part_1")
        )
        
        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(self.v1_part1_edit)
        hlayout1.addWidget(self.v1_part1_btn)
        variant1_layout.addRow("Часть 1:", hlayout1)
        
        self.v1_part2_edit = QLineEdit()
        self.v1_part2_btn = QPushButton("Выбрать файл...")
        self.v1_part2_btn.clicked.connect(
            lambda: self._select_file(self.v1_part2_edit, "variant_1", "part_2")
        )
        
        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(self.v1_part2_edit)
        hlayout2.addWidget(self.v1_part2_btn)
        variant1_layout.addRow("Часть 2:", hlayout2)
        
        variant1_group.setLayout(variant1_layout)
        layout.addWidget(variant1_group)
        
        # Группа для файлов варианта 2
        variant2_group = QGroupBox("Вариант 2")
        variant2_layout = QFormLayout()
        
        self.v2_part1_edit = QLineEdit()
        self.v2_part1_btn = QPushButton("Выбрать файл...")
        self.v2_part1_btn.clicked.connect(
            lambda: self._select_file(self.v2_part1_edit, "variant_2", "part_1")
        )
        
        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(self.v2_part1_edit)
        hlayout3.addWidget(self.v2_part1_btn)
        variant2_layout.addRow("Часть 1:", hlayout3)
        
        self.v2_part2_edit = QLineEdit()
        self.v2_part2_btn = QPushButton("Выбрать файл...")
        self.v2_part2_btn.clicked.connect(
            lambda: self._select_file(self.v2_part2_edit, "variant_2", "part_2")
        )
        
        hlayout4 = QHBoxLayout()
        hlayout4.addWidget(self.v2_part2_edit)
        hlayout4.addWidget(self.v2_part2_btn)
        variant2_layout.addRow("Часть 2:", hlayout4)
        
        variant2_group.setLayout(variant2_layout)
        layout.addWidget(variant2_group)
        
        # Индикатор валидности
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Обновить список предметов
        self._refresh_subjects()
    
    def _refresh_subjects(self):
        """Обновить список предметов."""
        current = self.subject_combo.currentText()
        self.subject_combo.clear()
        
        for subject in self.config.subjects:
            self.subject_combo.addItem(subject["name"])
        
        if current:
            index = self.subject_combo.findText(current)
            if index >= 0:
                self.subject_combo.setCurrentIndex(index)
    
    def _on_subject_changed(self, name: str):
        """При изменении выбранного предмета."""
        if not name:
            return
        
        subject = self.config.get_subject(name)
        if not subject:
            return
        
        # Заполнить поля файлами
        files = subject.get("files", {})
        
        v1_files = files.get("variant_1", {})
        self.v1_part1_edit.setText(v1_files.get("part_1", ""))
        self.v1_part2_edit.setText(v1_files.get("part_2", ""))
        
        v2_files = files.get("variant_2", {})
        self.v2_part1_edit.setText(v2_files.get("part_1", ""))
        self.v2_part2_edit.setText(v2_files.get("part_2", ""))
        
        # Показать/скрыть поля для части 2
        # Теперь показываем всегда если has_two_parts=True, независимо от конкретных классов
        has_two_parts = subject.get("has_two_parts", False)
        self.v1_part2_edit.setVisible(has_two_parts)
        self.v1_part2_btn.setVisible(has_two_parts)
        self.v2_part2_edit.setVisible(has_two_parts)
        self.v2_part2_btn.setVisible(has_two_parts)
        
        self._validate_files()
    
    def _select_file(self, line_edit: QLineEdit, variant: str, part: str):
        """Выбрать файл через диалог."""
        subject_name = self.subject_combo.currentText()
        if not subject_name:
            QMessageBox.warning(self, "Ошибка", "Выберите предмет")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите PDF файл",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            line_edit.setText(file_path)
            self.config.set_subject_file(subject_name, variant, part, file_path)
            self._validate_files()
    
    def _validate_files(self):
        """Проверить валидность файлов."""
        subject_name = self.subject_combo.currentText()
        if not subject_name:
            self.status_label.setText("")
            return
        
        subject = self.config.get_subject(subject_name)
        if not subject:
            return
        
        has_two_parts = subject.get("has_two_parts", False)
        
        v1_part1 = self.v1_part1_edit.text().strip()
        v1_part2 = self.v1_part2_edit.text().strip()
        v2_part1 = self.v2_part1_edit.text().strip()
        v2_part2 = self.v2_part2_edit.text().strip()
        
        errors = []
        
        if not v1_part1:
            errors.append("Вариант 1: не выбрана Часть 1")
        if has_two_parts and not v1_part2:
            errors.append("Вариант 1: не выбрана Часть 2")
        if not v2_part1:
            errors.append("Вариант 2: не выбрана Часть 1")
        if has_two_parts and not v2_part2:
            errors.append("Вариант 2: не выбрана Часть 2")
        
        if errors:
            self.status_label.setText("❌ Ошибки:\n" + "\n".join(errors))
            self.status_label.setStyleSheet("color: red;")
        else:
            self.status_label.setText("✓ Все файлы указаны")
            self.status_label.setStyleSheet("color: green;")
    
    def refresh_all(self):
        """Обновить все данные."""
        self._refresh_subjects()
        self._on_subject_changed(self.subject_combo.currentText())
    
    def is_valid(self) -> bool:
        """Проверить валидность всех файлов."""
        for subject in self.config.subjects:
            files = subject.get("files", {})
            
            for variant_key in ["variant_1", "variant_2"]:
                variant_data = files.get(variant_key, {})
                
                if not variant_data.get("part_1"):
                    return False
                
                if subject.get("has_two_parts") and not variant_data.get("part_2"):
                    return False
        
        return True
