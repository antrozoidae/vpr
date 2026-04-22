"""
Вкладка расчёта и печати.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QTextEdit, QMessageBox,
    QFileDialog, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path

from core.calculation import CalculationEngine, PrintJob
from pdf.processor import PDFProcessor
from printers.engine import PrintEngine


class PrintWorker(QThread):
    """Рабочий поток для печати."""
    
    progress = pyqtSignal(int, int, str)  # current, total, message
    log_message = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, jobs, sumatra_path, duplex_mode, temp_dir, log_file):
        super().__init__()
        self.jobs = jobs
        self.sumatra_path = sumatra_path
        self.duplex_mode = duplex_mode
        self.temp_dir = temp_dir
        self.log_file = log_file
        self.cancel_flag = False
    
    def run(self):
        """Выполнить печать."""
        pdf_processor = PDFProcessor(Path(self.temp_dir))
        print_engine = PrintEngine(self.sumatra_path, self.log_file)
        
        total_jobs = len(self.jobs)
        
        for i, job in enumerate(self.jobs):
            if self.cancel_flag:
                self.finished.emit(False, "Печать отменена пользователем")
                return
            
            self.log_message.emit(f"Обработка: {job.subject} Вариант {job.variant} ({job.printer})")
            
            # Обработать файл (склейка если нужно)
            file_path = pdf_processor.get_or_create_merged_pdf(job.file_path)
            
            if not file_path:
                self.log_message.emit(f"Ошибка: файл не найден или невалиден - {job.file_path}")
                continue
            
            # Печать
            result = print_engine.print_file(
                file_path=file_path,
                printer_name=job.printer,
                duplex_mode=job.duplex_mode,
                copies=job.copies,
                subject=job.subject,
                variant=job.variant,
                progress_callback=lambda c, t, m: self.progress.emit(i * 100 + (c // max(t, 1) * 100), total_jobs * 100, m)
            )
            
            if result.success:
                self.log_message.emit(f"✓ Успешно: {job.subject} Вариант {job.variant} - {job.copies} копий")
            else:
                self.log_message.emit(f"✗ Ошибка: {result.message}")
        
        self.finished.emit(True, "Печать завершена")
    
    def cancel(self):
        """Отменить печать."""
        self.cancel_flag = True


class PrintCalcTab(QWidget):
    """Вкладка расчёта и печати."""
    
    def __init__(self, config, printer_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.printer_manager = printer_manager
        self.calc_engine = CalculationEngine(config)
        self.print_worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс."""
        layout = QVBoxLayout(self)
        
        # Настройки печати
        settings_group = QHBoxLayout()
        
        # Дуплекс
        settings_group.addWidget(QLabel("Дуплекс:"))
        self.duplex_combo = QComboBox()
        self.duplex_combo.addItem("Нет", "none")
        self.duplex_combo.addItem("Длинная сторона", "long")
        self.duplex_combo.addItem("Короткая сторона", "short")
        self.duplex_combo.setCurrentIndex(0)
        settings_group.addWidget(self.duplex_combo)
        
        # SumatraPDF путь
        settings_group.addWidget(QLabel("SumatraPDF:"))
        self.sumatra_edit = QLineEdit()
        self.sumatra_edit.setPlaceholderText("Путь к SumatraPDF.exe")
        settings_group.addWidget(self.sumatra_edit)
        
        self.sumatra_btn = QPushButton("...")
        self.sumatra_btn.clicked.connect(self._select_sumatra)
        settings_group.addWidget(self.sumatra_btn)
        
        layout.addLayout(settings_group)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.calc_btn = QPushButton("Рассчитать")
        self.calc_btn.clicked.connect(self._calculate)
        btn_layout.addWidget(self.calc_btn)
        
        self.print_btn = QPushButton("Печать")
        self.print_btn.clicked.connect(self._start_print)
        self.print_btn.setEnabled(False)
        btn_layout.addWidget(self.print_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self._cancel_print)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Таблица расчёта
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Предмет", "Вариант", "Принтер", "Копий", "Дуплекс"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 120)
        layout.addWidget(self.table)
        
        # Прогресс-бар
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Лог
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # Загрузить сохранённый путь
        saved_path = self.config.settings.get("sumatra_path", "")
        if saved_path:
            self.sumatra_edit.setText(saved_path)
    
    def _select_sumatra(self):
        """Выбрать путь к SumatraPDF."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите SumatraPDF.exe",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            self.sumatra_edit.setText(file_path)
            self.config.set_sumatra_path(file_path)
    
    def _calculate(self):
        """Выполнить расчёт."""
        enabled_printers = self.config.get_enabled_printers()
        
        if not enabled_printers:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один активный принтер")
            return
        
        if not self.config.subjects:
            QMessageBox.warning(self, "Ошибка", "Нет предметов для печати")
            return
        
        # Проверка файлов
        for subject in self.config.subjects:
            files = subject.get("files", {})
            for variant_key in ["variant_1", "variant_2"]:
                variant_data = files.get(variant_key, {})
                if not variant_data.get("part_1"):
                    QMessageBox.warning(
                        self, "Ошибка",
                        f"Не указан файл для предмета '{subject['name']}' {variant_key}"
                    )
                    return
                if subject.get("has_two_parts") and not variant_data.get("part_2"):
                    QMessageBox.warning(
                        self, "Ошибка",
                        f"Не указана часть 2 для предмета '{subject['name']}' {variant_key}"
                    )
                    return
        
        # Получить режим дуплекса
        duplex_mode = self.duplex_combo.currentData()
        
        # Расчёт
        jobs = self.calc_engine.calculate_all_jobs(enabled_printers, duplex_mode)
        
        # Отобразить в таблице
        self.table.setRowCount(0)
        for job in jobs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(job.subject))
            self.table.setItem(row, 1, QTableWidgetItem(str(job.variant)))
            self.table.setItem(row, 2, QTableWidgetItem(job.printer))
            self.table.setItem(row, 3, QTableWidgetItem(str(job.copies)))
            self.table.setItem(row, 4, QTableWidgetItem(duplex_mode))
        
        if jobs:
            self.print_btn.setEnabled(True)
            self.log_message(f"Рассчитано {len(jobs)} заданий на печать")
        else:
            self.print_btn.setEnabled(False)
            self.log_message("Нет заданий для печати (проверьте файлы и классы)")
    
    def _start_print(self):
        """Начать печать."""
        sumatra_path = self.sumatra_edit.text().strip()
        if not sumatra_path:
            QMessageBox.warning(self, "Ошибка", "Укажите путь к SumatraPDF")
            return
        
        if not os.path.exists(sumatra_path):
            QMessageBox.warning(self, "Ошибка", "SumatraPDF не найден по указанному пути")
            return
        
        # Сохранить путь
        self.config.set_sumatra_path(sumatra_path)
        
        # Блокировка UI
        self._set_printing_state(True)
        
        # Получить задания из таблицы
        jobs = []
        for row in range(self.table.rowCount()):
            subject = self.table.item(row, 0).text()
            variant = int(self.table.item(row, 1).text())
            printer = self.table.item(row, 2).text()
            copies = int(self.table.item(row, 3).text())
            duplex = self.table.item(row, 4).text()
            
            # Найти исходное задание для получения file_path
            orig_jobs = self.calc_engine.calculate_all_jobs([printer], duplex)
            for oj in orig_jobs:
                if oj.subject == subject and oj.variant == variant and oj.printer == printer:
                    jobs.append(PrintJob(subject, variant, printer, copies, duplex, oj.file_path))
                    break
        
        # Создать и запустить worker
        self.print_worker = PrintWorker(
            jobs=jobs,
            sumatra_path=sumatra_path,
            duplex_mode=duplex,
            temp_dir=str(self.config.get_temp_dir()),
            log_file="print_log.txt"
        )
        
        self.print_worker.progress.connect(self._on_progress)
        self.print_worker.log_message.connect(self.log_message)
        self.print_worker.finished.connect(self._on_finished)
        
        self.print_worker.start()
    
    def _cancel_print(self):
        """Отменить печать."""
        if self.print_worker:
            self.print_worker.cancel()
            
            # Очистка очереди спулера
            from printers.manager import PrinterManager
            pm = PrinterManager()
            pm.cancel_print_jobs_by_prefix(PrintEngine.JOB_PREFIX)
            
            self.log_message("Печать отменена пользователем")
    
    def _on_progress(self, current: int, total: int, message: str):
        """Обновление прогресса."""
        if total > 0:
            self.progress.setMaximum(total)
            self.progress.setValue(current)
        self.log_message(message)
    
    def _on_finished(self, success: bool, message: str):
        """Завершение печати."""
        self._set_printing_state(False)
        
        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.warning(self, "Предупреждение", message)
        
        # Автоочистка временных файлов
        pdf_processor = PDFProcessor(self.config.get_temp_dir())
        pdf_processor.cleanup_temp_files()
    
    def _set_printing_state(self, is_printing: bool):
        """Установить состояние печати."""
        self.calc_btn.setEnabled(not is_printing)
        self.print_btn.setEnabled(not is_printing)
        self.cancel_btn.setEnabled(is_printing)
        self.duplex_combo.setEnabled(not is_printing)
        self.progress.setVisible(is_printing)
        
        if is_printing:
            self.progress.setValue(0)
    
    def log_message(self, msg: str):
        """Добавить сообщение в лог."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")
