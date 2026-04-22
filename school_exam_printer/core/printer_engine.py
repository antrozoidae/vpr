"""
Модуль печати через SumatraPDF CLI и управления очередью принтеров
"""

import subprocess
import time
import threading
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .config import AppConfig, PrinterConfig
from .calculator import PrintTask
from .pdf_manager import PDFManager, PrintLogger


class PrintStatus(Enum):
    """Статусы печати"""
    PENDING = "Ожидание"
    MERGING = "Склейка PDF"
    PRINTING = "Печать"
    COMPLETED = "Завершено"
    FAILED = "Ошибка"
    CANCELLED = "Отменено"


@dataclass
class PrintResult:
    """Результат печати"""
    task: PrintTask
    status: PrintStatus
    message: str
    temp_file: Optional[Path] = None
    return_code: int = 0


class PrintEngine:
    """Движок печати через SumatraPDF CLI"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.pdf_manager = PDFManager(config.get_temp_dir())
        self.logger = PrintLogger(config.get_log_file())
        self.cancel_flag = threading.Event()
        self.current_processes: List[subprocess.Popen] = []
        self.max_concurrent = 3  # Максимум одновременных процессов на принтер
    
    def set_cancel_flag(self, cancel: bool) -> None:
        """Установить флаг отмены"""
        if cancel:
            self.cancel_flag.set()
        else:
            self.cancel_flag.clear()
    
    def is_cancelled(self) -> bool:
        """Проверить флаг отмены"""
        return self.cancel_flag.is_set()
    
    def get_duplex_setting(self, mode: str) -> str:
        """Преобразовать режим дуплекса в параметр SumatraPDF"""
        duplex_map = {
            "none": "duplex=none",
            "long": "duplex=long",
            "short": "duplex=short"
        }
        return duplex_map.get(mode, "duplex=none")
    
    def prepare_print_file(self, task: PrintTask) -> tuple[Optional[Path], str]:
        """
        Подготовить файл для печати (склеить части если нужно)
        Возвращает путь к файлу и сообщение
        """
        if task.is_two_parts:
            if not task.part_1_file or not task.part_2_file:
                return None, "Не указаны файлы частей"
            
            valid1, msg1 = self.pdf_manager.validate_pdf(task.part_1_file)
            if not valid1:
                return None, f"Часть 1: {msg1}"
            
            valid2, msg2 = self.pdf_manager.validate_pdf(task.part_2_file)
            if not valid2:
                return None, f"Часть 2: {msg2}"
            
            merged_path, merge_msg = self.pdf_manager.merge_two_parts(
                task.part_1_file,
                task.part_2_file,
                task.subject,
                task.grade,
                task.variant
            )
            
            if merged_path is None:
                return None, merge_msg
            
            return merged_path, "Части склеены"
        else:
            if not task.file_path:
                return None, "Не указан файл задания"
            
            valid, msg = self.pdf_manager.validate_pdf(task.file_path)
            if not valid:
                return None, msg
            
            return Path(task.file_path), "Файл готов"
    
    def print_file(
        self, 
        file_path: Path, 
        printer_name: str, 
        copies: int,
        duplex_mode: str
    ) -> tuple[int, str]:
        """
        Отправить файл на печать через SumatraPDF
        Возвращает код возврата и сообщение
        """
        sumatra_path = self.config.sumatra_path
        
        if not sumatra_path or not Path(sumatra_path).exists():
            return -1, "SumatraPDF не найден"
        
        if not file_path.exists():
            return -1, f"Файл не найден: {file_path}"
        
        duplex_setting = self.get_duplex_setting(duplex_mode)
        
        # Формирование команды
        cmd = [
            sumatra_path,
            "-print-to", printer_name,
            "-print-settings", duplex_setting,
            "-silent",
            str(file_path)
        ]
        
        # Для нескольких копий нужно запустить несколько раз или использовать N-up
        # SumatraPDF не поддерживает параметр copies напрямую в CLI
        # Поэтому запускаем команду copies раз
        
        try:
            for i in range(copies):
                if self.is_cancelled():
                    return -2, "Печать отменена"
                
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.current_processes.append(proc)
                
                # Ждём завершения процесса с таймаутом
                try:
                    stdout, stderr = proc.communicate(timeout=60)
                    if proc.returncode != 0:
                        error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Неизвестная ошибка"
                        return proc.returncode, f"Ошибка печати: {error_msg}"
                except subprocess.TimeoutExpired:
                    proc.kill()
                    return -1, "Таймаут печати"
            
            return 0, "OK"
            
        except Exception as e:
            return -1, f"Ошибка: {str(e)}"
        finally:
            # Очистка списка процессов
            self.current_processes = [p for p in self.current_processes if p.poll() is None]
    
    def execute_task(self, task: PrintTask, progress_callback: Optional[Callable] = None) -> PrintResult:
        """
        Выполнить задачу печати
        """
        if self.is_cancelled():
            return PrintResult(
                task=task,
                status=PrintStatus.CANCELLED,
                message="Задача отменена перед началом"
            )
        
        temp_file = None
        
        try:
            # Подготовка файла
            file_path, prep_msg = self.prepare_print_file(task)
            if file_path is None:
                return PrintResult(
                    task=task,
                    status=PrintStatus.FAILED,
                    message=f"Ошибка подготовки: {prep_msg}"
                )
            
            temp_file = file_path
            
            if progress_callback:
                progress_callback(task, PrintStatus.PRINTING, prep_msg)
            
            # Печать
            return_code, print_msg = self.print_file(
                file_path,
                task.printer,
                task.copies,
                task.duplex_mode
            )
            
            if return_code == -2:
                status = PrintStatus.CANCELLED
            elif return_code == 0:
                status = PrintStatus.COMPLETED
            else:
                status = PrintStatus.FAILED
            
            # Логирование
            self.logger.log_print_task(
                subject=task.subject,
                grade=task.grade,
                variant=task.variant,
                printer=task.printer,
                copies=task.copies,
                status="OK" if status == PrintStatus.COMPLETED else print_msg,
                return_code=return_code,
                duplex=task.duplex_mode
            )
            
            return PrintResult(
                task=task,
                status=status,
                message=print_msg,
                temp_file=temp_file,
                return_code=return_code
            )
            
        except Exception as e:
            error_msg = str(e)
            self.logger.log_print_task(
                subject=task.subject,
                grade=task.grade,
                variant=task.variant,
                printer=task.printer,
                copies=task.copies,
                status=f"Ошибка: {error_msg}",
                return_code=-1,
                duplex=task.duplex_mode
            )
            
            return PrintResult(
                task=task,
                status=PrintStatus.FAILED,
                message=error_msg,
                temp_file=temp_file,
                return_code=-1
            )
    
    def execute_all_tasks(
        self,
        tasks: List[PrintTask],
        progress_callback: Optional[Callable[[int, int, PrintResult], None]] = None
    ) -> List[PrintResult]:
        """
        Выполнить все задачи печати
        progress_callback: функция(current, total, result)
        """
        results = []
        total = len(tasks)
        
        self.logger.log(f"Начало печати {total} задач")
        
        for i, task in enumerate(tasks):
            if self.is_cancelled():
                self.logger.log("Печать отменена пользователем", "WARNING")
                break
            
            result = self.execute_task(task)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total, result)
        
        # Очистка временных файлов после печати
        self.cleanup_temp_files()
        
        completed = sum(1 for r in results if r.status == PrintStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == PrintStatus.FAILED)
        cancelled = sum(1 for r in results if r.status == PrintStatus.CANCELLED)
        
        self.logger.log(
            f"Завершено: {completed}, Ошибок: {failed}, Отменено: {cancelled}"
        )
        
        return results
    
    def cleanup_temp_files(self) -> None:
        """Очистить временные файлы"""
        try:
            for file in self.pdf_manager.get_temp_files():
                try:
                    file.unlink()
                except Exception:
                    pass
        except Exception:
            pass
    
    def cancel_printing(self) -> None:
        """Отменить текущую печать"""
        self.set_cancel_flag(True)
        
        # Остановка текущих процессов
        for proc in self.current_processes:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass
        
        # Очистка очереди принтера (только Windows)
        self.clear_spooler_queue()
    
    def clear_spooler_queue(self) -> None:
        """
        Очистить очередь спулера для заданий с префиксом ExamPrint_
        Только для Windows с использованием pywin32
        """
        try:
            import win32print
            import win32api
            
            # Получаем принтер по умолчанию или пытаемся найти наши задания
            try:
                printer_name = win32print.GetDefaultPrinter()
                handle = win32print.OpenPrinter(printer_name)
                
                jobs = win32print.EnumJobs(handle, 0, -1, 1)
                
                for job in jobs:
                    job_id = job['JobId']
                    document_name = job.get('pDocument', '')
                    
                    # Проверка на наше задание по имени документа
                    if 'ExamPrint' in document_name or 'merged_' in document_name:
                        try:
                            win32print.SetJob(handle, job_id, 0, None, win32print.JOB_CONTROL_DELETE)
                            self.logger.log(f"Удалено задание из очереди: {job_id}")
                        except Exception as e:
                            self.logger.log(f"Не удалось удалить задание {job_id}: {e}", "WARNING")
                
                win32print.ClosePrinter(handle)
                
            except Exception as e:
                self.logger.log(f"Ошибка доступа к спулеру: {e}", "WARNING")
                
        except ImportError:
            # pywin32 недоступен (не Windows или не установлен)
            self.logger.log("pywin32 недоступен, очистка очереди пропущена", "INFO")
        except Exception as e:
            self.logger.log(f"Ошибка очистки очереди: {e}", "WARNING")
