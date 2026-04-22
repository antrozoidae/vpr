"""
Вкладка управления заданиями (файлы PDF)
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QFileDialog, QScrollArea, QFrame, QLineEdit,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class AssignmentsTab(QWidget):
    """Вкладка управления файлами заданий"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.file_widgets = {}  # Хранение виджетов для файлов
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_label = QLabel("📁 Задания (PDF файлы)")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Описание
        desc_label = QLabel(
            "Укажите пути к PDF файлам для каждого предмета, параллели и варианта. "
            "Если для параллели включён режим '2 части', укажите оба файла."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Область прокрутки для содержимого
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("✅ Проверить файлы")
        self.validate_btn.clicked.connect(self._validate_files)
        btn_layout.addWidget(self.validate_btn)
        
        btn_layout.addStretch()
        
        self.clear_all_btn = QPushButton("🗑️ Очистить все")
        self.clear_all_btn.clicked.connect(self._clear_all_files)
        btn_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(btn_layout)
        
        # Заполнение
        self._populate_content()
    
    def _populate_content(self) -> None:
        """Заполнить содержимое вкладки"""
        # Очистка текущего содержимого
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.file_widgets = {}
        
        if not self.config.subjects:
            no_subjects_label = QLabel("<i>Нет предметов. Добавьте предметы на вкладке 'Предметы'.</i>")
            self.content_layout.addWidget(no_subjects_label)
            return
        
        for subject in self.config.subjects:
            group = QGroupBox(f"📚 {subject.name}")
            group_layout = QVBoxLayout(group)
            
            grid = QGridLayout()
            row = 0
            
            for grade, grade_data in subject.matrix.items():
                selected_letters = grade_data.get("selected_letters", [])
                two_parts = grade_data.get("two_parts", False)
                
                if not selected_letters:
                    continue
                
                # Заголовок параллели
                parts_text = " (2 части)" if two_parts else ""
                grade_label = QLabel(f"<b>{grade} класс{parts_text}:</b>")
                grid.addWidget(grade_label, row, 0, 1, 3)
                row += 1
                
                # Вариант 1
                v1_label = QLabel("Вариант 1:")
                grid.addWidget(v1_label, row, 0)
                
                if two_parts:
                    # Часть 1
                    file_edit_p1 = self._create_file_edit(subject.name, grade, 1, "part_1")
                    grid.addWidget(file_edit_p1, row, 1)
                    
                    browse_btn_p1 = QPushButton("...")
                    browse_btn_p1.setFixedWidth(40)
                    browse_btn_p1.clicked.connect(
                        lambda checked, s=subject.name, g=grade, v=1, p="part_1": 
                        self._browse_file(s, g, v, p)
                    )
                    grid.addWidget(browse_btn_p1, row, 2)
                    row += 1
                    
                    # Часть 2
                    file_edit_p2 = self._create_file_edit(subject.name, grade, 1, "part_2")
                    grid.addWidget(file_edit_p2, row, 1)
                    
                    browse_btn_p2 = QPushButton("...")
                    browse_btn_p2.setFixedWidth(40)
                    browse_btn_p2.clicked.connect(
                        lambda checked, s=subject.name, g=grade, v=1, p="part_2": 
                        self._browse_file(s, g, v, p)
                    )
                    grid.addWidget(browse_btn_p2, row, 2)
                else:
                    # Один файл
                    file_edit = self._create_file_edit(subject.name, grade, 1, "single")
                    grid.addWidget(file_edit, row, 1)
                    
                    browse_btn = QPushButton("...")
                    browse_btn.setFixedWidth(40)
                    browse_btn.clicked.connect(
                        lambda checked, s=subject.name, g=grade, v=1, p="single": 
                        self._browse_file(s, g, v, p)
                    )
                    grid.addWidget(browse_btn, row, 2)
                
                row += 1
                
                # Вариант 2
                v2_label = QLabel("Вариант 2:")
                grid.addWidget(v2_label, row, 0)
                
                if two_parts:
                    # Часть 1
                    file_edit_p1 = self._create_file_edit(subject.name, grade, 2, "part_1")
                    grid.addWidget(file_edit_p1, row, 1)
                    
                    browse_btn_p1 = QPushButton("...")
                    browse_btn_p1.setFixedWidth(40)
                    browse_btn_p1.clicked.connect(
                        lambda checked, s=subject.name, g=grade, v=2, p="part_1": 
                        self._browse_file(s, g, v, p)
                    )
                    grid.addWidget(browse_btn_p1, row, 2)
                    row += 1
                    
                    # Часть 2
                    file_edit_p2 = self._create_file_edit(subject.name, grade, 2, "part_2")
                    grid.addWidget(file_edit_p2, row, 1)
                    
                    browse_btn_p2 = QPushButton("...")
                    browse_btn_p2.setFixedWidth(40)
                    browse_btn_p2.clicked.connect(
                        lambda checked, s=subject.name, g=grade, v=2, p="part_2": 
                        self._browse_file(s, g, v, p)
                    )
                    grid.addWidget(browse_btn_p2, row, 2)
                else:
                    # Один файл
                    file_edit = self._create_file_edit(subject.name, grade, 2, "single")
                    grid.addWidget(file_edit, row, 1)
                    
                    browse_btn = QPushButton("...")
                    browse_btn.setFixedWidth(40)
                    browse_btn.clicked.connect(
                        lambda checked, s=subject.name, g=grade, v=2, p="single": 
                        self._browse_file(s, g, v, p)
                    )
                    grid.addWidget(browse_btn, row, 2)
                
                row += 1
                
                # Разделитель
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                grid.addWidget(line, row, 0, 1, 3)
                row += 1
            
            grid.setColumnStretch(1, 1)
            group_layout.addLayout(grid)
            self.content_layout.addWidget(group)
        
        self.content_layout.addStretch()
    
    def _create_file_edit(self, subject: str, grade: str, variant: int, part: str) -> QLineEdit:
        """Создать поле редактирования для файла"""
        key = (subject, grade, variant, part)
        
        edit = QLineEdit()
        edit.setPlaceholderText("Выберите файл...")
        edit.setReadOnly(True)
        
        # Загрузить существующий путь
        if subject in self.config.subjects:
            subj_obj = self.config.get_subject(subject)
            if subj_obj and grade in subj_obj.files:
                files_data = subj_obj.files[grade].get(f"variant_{variant}", {})
                file_path = files_data.get(part, "")
                if file_path:
                    edit.setText(file_path)
        
        self.file_widgets[key] = edit
        return edit
    
    def _browse_file(self, subject: str, grade: str, variant: int, part: str) -> None:
        """Открыть диалог выбора файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Выберите PDF файл",
            "",
            "PDF файлы (*.pdf);;Все файлы (*)"
        )
        
        if file_path:
            key = (subject, grade, variant, part)
            if key in self.file_widgets:
                self.file_widgets[key].setText(file_path)
            
            # Сохранить в конфигурацию
            subj_obj = self.config.get_subject(subject)
            if subj_obj:
                if grade not in subj_obj.files:
                    subj_obj.files[grade] = {}
                
                variant_key = f"variant_{variant}"
                if variant_key not in subj_obj.files[grade]:
                    subj_obj.files[grade][variant_key] = {}
                
                subj_obj.files[grade][variant_key][part] = file_path
            
            self.data_changed.emit()
    
    def _validate_files(self) -> None:
        """Проверить существование всех указанных файлов"""
        errors = []
        
        for subject in self.config.subjects:
            for grade, grade_data in subject.matrix.items():
                two_parts = grade_data.get("two_parts", False)
                
                for variant in [1, 2]:
                    variant_key = f"variant_{variant}"
                    files_data = subject.files.get(grade, {}).get(variant_key, {})
                    
                    if two_parts:
                        part_1 = files_data.get("part_1", "")
                        part_2 = files_data.get("part_2", "")
                        
                        if not part_1:
                            errors.append(f"{subject.name}, {grade} класс, Вариант {variant}: не указана Часть 1")
                        elif not Path(part_1).exists():
                            errors.append(f"{subject.name}, {grade} класс, Вариант {variant}: файл Части 1 не найден")
                        
                        if not part_2:
                            errors.append(f"{subject.name}, {grade} класс, Вариант {variant}: не указана Часть 2")
                        elif not Path(part_2).exists():
                            errors.append(f"{subject.name}, {grade} класс, Вариант {variant}: файл Части 2 не найден")
                    else:
                        single = files_data.get("single", "")
                        
                        if not single:
                            errors.append(f"{subject.name}, {grade} класс, Вариант {variant}: не указан файл")
                        elif not Path(single).exists():
                            errors.append(f"{subject.name}, {grade} класс, Вариант {variant}: файл не найден")
        
        if errors:
            error_text = "\n".join(errors[:20])  # Показать первые 20 ошибок
            if len(errors) > 20:
                error_text += f"\n... и ещё {len(errors) - 20} ошибок"
            
            QMessageBox.warning(
                self,
                "Ошибки валидации",
                f"Найдены следующие ошибки:\n\n{error_text}"
            )
        else:
            QMessageBox.information(
                self,
                "Валидация",
                "Все файлы указаны корректно!"
            )
    
    def _clear_all_files(self) -> None:
        """Очистить все пути к файлам"""
        reply = QMessageBox.question(
            self,
            "Очистка файлов",
            "Очистить все пути к файлам?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for subject in self.config.subjects:
                subject.files = {}
            
            self._populate_content()
            self.data_changed.emit()
    
    def refresh(self) -> None:
        """Обновить отображение"""
        self._populate_content()
    
    def save_data(self) -> None:
        """Сохранить данные"""
        pass
