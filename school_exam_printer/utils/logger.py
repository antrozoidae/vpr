"""
Модуль логирования.
"""
import logging
from pathlib import Path
from datetime import datetime


class Logger:
    """Класс для логирования событий приложения."""
    
    def __init__(self, log_file: str = "print_log.txt"):
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self):
        """Настроить логирование."""
        # Создаем logger
        self.logger = logging.getLogger("SchoolExamPrinter")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Формат
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Добавить handler
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
    
    def log_print_job(
        self,
        subject: str,
        variant: int,
        printer: str,
        copies: int,
        status: str,
        return_code: int = 0
    ):
        """Записать информацию о задании печати."""
        message = (
            f"Печать | Предмет: {subject} | Вариант: {variant} | "
            f"Принтер: {printer} | Копий: {copies} | Статус: {status} | "
            f"Код возврата: {return_code}"
        )
        
        if status == "SUCCESS":
            self.logger.info(message)
        elif status == "ERROR":
            self.logger.error(message)
        else:
            self.logger.warning(message)
    
    def log_event(self, level: str, event: str, details: str = ""):
        """Записать событие."""
        message = f"{event}"
        if details:
            message += f" | {details}"
        
        if level == "INFO":
            self.logger.info(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "DEBUG":
            self.logger.debug(message)
    
    def log_startup(self):
        """Записать запуск приложения."""
        self.logger.info("=" * 50)
        self.logger.info("Приложение запущено")
    
    def log_shutdown(self):
        """Записать завершение работы приложения."""
        self.logger.info("Приложение завершено")
        self.logger.info("=" * 50)
