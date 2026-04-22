"""
Вкладка расчёта и печати
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QTextEdit, QMessageBox, QGroupBox, QSplitter, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from core.config import AppConfig
from core.calculator import CalculationEngine, PrintTask
from core.printer_engine import PrintEngine, PrintStatus, PrintResult


class PrintWorker(QThread):
    progress = pyqtSignal(int, int, object)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, engine: PrintEngine, tasks: list):
        super().__init__()
        self.engine = engine
        self.tasks = tasks
    
    def run(self):
        try:
            results = self.engine.execute_all_tasks(
                self.tasks,
                progress_callback=lambda c, t, r: self.progress.emit(c, t, r)
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class PrintTab(QWidget):
    data_changed = pyqtSignal()
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.calculator = CalculationEngine(config)
        self.print_engine = None
        self.current_tasks = []
        self.print_worker = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        header_label = QLabel('Расчёт и Печать')
        header_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        btn_layout = QHBoxLayout()
        self.calc_btn = QPushButton('Рассчитать')
        self.calc_btn.clicked.connect(self._calculate)
        btn_layout.addWidget(self.calc_btn)
        
        self.print_btn = QPushButton('Печать')
        self.print_btn.clicked.connect(self._start_print)
        self.print_btn.setEnabled(False)
        btn_layout.addWidget(self.print_btn)
        
        self.cancel_btn = QPushButton('Отмена')
        self.cancel_btn.clicked.connect(self._cancel_print)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        self.save_btn = QPushButton('Сохранить JSON')
        self.save_btn.clicked.connect(self._save_json)
        btn_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton('Загрузить JSON')
        self.load_btn.clicked.connect(self._load_json)
        btn_layout.addWidget(self.load_btn)
        
        top_layout.addLayout(btn_layout)
        
        self.calc_table = QTableWidget()
        self.calc_table.setColumnCount(7)
        self.calc_table.setHorizontalHeaderLabels([
            'Предмет', 'Параллель', 'Вариант', 'Принтер', 'Копий', 'Дуплекс', 'Файл'
        ])
        header = self.calc_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.calc_table.verticalHeader().setVisible(False)
        self.calc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.calc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        top_layout.addWidget(self.calc_table)
        splitter.addWidget(top_widget)
        
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        progress_group = QGroupBox('Прогресс печати')
        progress_layout = QVBoxLayout(progress_group)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('%p% (%v/%m)')
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel('Готов к печати')
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        bottom_layout.addWidget(progress_group)
        
        log_group = QGroupBox('Лог операций')
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 9))
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton('Очистить лог')
        clear_log_btn.clicked.connect(self._clear_log)
        log_layout.addWidget(clear_log_btn)
        bottom_layout.addWidget(log_group)
        splitter.addWidget(bottom_widget)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
    
    def _calculate(self):
        self.current_tasks = self.calculator.calculate_all_tasks()
        if not self.current_tasks:
            QMessageBox.warning(self, 'Расчёт', 'Нет задач для печати.')
            return
        self._populate_calc_table()
        summary = self.calculator.get_calculation_summary()
        self._log(f'Расчёт выполнен: {summary["total_tasks"]} задач')
        self.print_btn.setEnabled(True)
        self.data_changed.emit()
    
    def _populate_calc_table(self):
        self.calc_table.setRowCount(len(self.current_tasks))
        for row, task in enumerate(self.current_tasks):
            self.calc_table.setItem(row, 0, QTableWidgetItem(task.subject))
            self.calc_table.setItem(row, 1, QTableWidgetItem(f'{task.grade} класс'))
            self.calc_table.setItem(row, 2, QTableWidgetItem(f'Вариант {task.variant}'))
            self.calc_table.setItem(row, 3, QTableWidgetItem(task.printer))
            self.calc_table.setItem(row, 4, QTableWidgetItem(str(task.copies)))
            duplex_map = {'none': 'Нет', 'long': 'Длинная сторона', 'short': 'Короткая сторона'}
            duplex_text = duplex_map.get(task.duplex_mode, 'Нет')
            self.calc_table.setItem(row, 5, QTableWidgetItem(duplex_text))
            if task.is_two_parts:
                file_text = 'Часть 1 + Часть 2'
            else:
                file_text = task.file_path.split('/')[-1] if task.file_path else 'Не указан'
            self.calc_table.setItem(row, 6, QTableWidgetItem(file_text))
    
    def _start_print(self):
        if not self.current_tasks:
            return
        sumatra_path = self.config.sumatra_path or self.config.find_sumatra_pdf()
        if not sumatra_path:
            QMessageBox.critical(self, 'Ошибка', 'SumatraPDF не найден.')
            return
        reply = QMessageBox.question(self, 'Начало печати', f'Начать печать {len(self.current_tasks)} задач?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.print_engine = PrintEngine(self.config)
        self._set_printing_state(True)
        self.print_worker = PrintWorker(self.print_engine, self.current_tasks)
        self.print_worker.progress.connect(self._on_print_progress)
        self.print_worker.finished.connect(self._on_print_finished)
        self.print_worker.error.connect(self._on_print_error)
        self.print_worker.start()
        self._log('Начало печати...')
    
    def _cancel_print(self):
        if self.print_engine:
            self.print_engine.cancel_printing()
            self._log('Отмена печати...')
        self._set_printing_state(False)
    
    def _set_printing_state(self, printing: bool):
        self.calc_btn.setEnabled(not printing)
        self.print_btn.setEnabled(not printing and bool(self.current_tasks))
        self.cancel_btn.setEnabled(printing)
        self.save_btn.setEnabled(not printing)
        self.load_btn.setEnabled(not printing)
    
    def _on_print_progress(self, current: int, total: int, result: PrintResult):
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        status_map = {PrintStatus.COMPLETED: '+', PrintStatus.FAILED: 'x', PrintStatus.CANCELLED: '-'}
        status_text = status_map.get(result.status, '?')
        self.progress_label.setText(f'{status_text} {result.task.subject} | {result.task.grade}')
        self._log(f'[{status_text}] {result.task.subject}: {result.message}')
    
    def _on_print_finished(self, results: list):
        completed = sum(1 for r in results if r.status == PrintStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == PrintStatus.FAILED)
        cancelled = sum(1 for r in results if r.status == PrintStatus.CANCELLED)
        self.progress_bar.setValue(100)
        self.progress_label.setText(f'Завершено: {completed}, Ошибок: {failed}, Отменено: {cancelled}')
        self._log(f'Печать завершена. Успешно: {completed}')
        self._set_printing_state(False)
        if failed == 0 and cancelled == 0:
            QMessageBox.information(self, 'Печать завершена', f'Все {completed} задач выполнены!')
    
    def _on_print_error(self, error: str):
        self._log(f'Ошибка: {error}')
        self._set_printing_state(False)
        QMessageBox.critical(self, 'Ошибка печати', error)
    
    def _log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f'[{timestamp}] {message}')
    
    def _clear_log(self):
        self.log_text.clear()
    
    def _save_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить конфигурацию', 'config.json', 'JSON файлы (*.json)')
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            try:
                self.config.save(file_path)
                self._log(f'Сохранено: {file_path}')
                QMessageBox.information(self, 'Сохранение', f'Конфигурация сохранена в: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', str(e))
    
    def _load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Загрузить конфигурацию', '', 'JSON файлы (*.json)')
        if file_path:
            try:
                self.config = AppConfig.load(file_path)
                self.calculator = CalculationEngine(self.config)
                self.data_changed.emit()
                self._log(f'Загружено: {file_path}')
                QMessageBox.information(self, 'Загрузка', f'Конфигурация загружена из: {file_path}')
                self.current_tasks = []
                self.calc_table.setRowCount(0)
                self.print_btn.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', str(e))
    
    def refresh(self):
        self.calculator = CalculationEngine(self.config)
        self.current_tasks = []
        self.calc_table.setRowCount(0)
        self.print_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText('Готов к печати')
    
    def save_data(self):
        pass
