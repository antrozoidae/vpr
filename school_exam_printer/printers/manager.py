"""
Модуль работы с принтерами Windows.
"""
import sys
from typing import List, Dict, Any, Optional


class PrinterManager:
    """Менеджер принтеров Windows."""
    
    def __init__(self):
        self.win32print = None
        self._initialize_win32()
    
    def _initialize_win32(self):
        """Инициализировать win32print (только Windows)."""
        if sys.platform == 'win32':
            try:
                import win32print
                self.win32print = win32print
            except ImportError:
                print("Warning: pywin32 не установлен. Функционал принтеров будет ограничен.")
        else:
            print("Info: Не Windows OS. Используем заглушку для принтеров.")
    
    def get_all_printers(self) -> List[Dict[str, Any]]:
        """
        Получить список всех локальных принтеров.
        Возвращает список словарей с именем и статусом.
        """
        if self.win32print is None:
            # Заглушка для не-Windows или при отсутствии pywin32
            return [
                {"name": "Microsoft Print to PDF", "status": "ready"},
                {"name": "HP LaserJet Pro M404", "status": "ready"},
                {"name": "Canon i-SENSYS MF269", "status": "offline"}
            ]
        
        printers = []
        try:
            # EnumPrinters возвращает кортежи (flags, name, port_name, desc)
            printer_list = self.win32print.EnumPrinters(
                self.win32print.PRINTER_ENUM_LOCAL | self.win32print.PRINTER_ENUM_CONNECTIONS
            )
            
            for printer_info in printer_list:
                printer_name = printer_info[1]  # Имя принтера
                status = self._get_printer_status(printer_name)
                printers.append({
                    "name": printer_name,
                    "status": status
                })
        except Exception as e:
            print(f"Ошибка получения списка принтеров: {e}")
        
        return printers
    
    def _get_printer_status(self, printer_name: str) -> str:
        """Получить статус принтера."""
        if self.win32print is None:
            return "ready"
        
        try:
            # Очистка имени для API
            clean_name = printer_name.strip()
            if not clean_name:
                return "unknown"
            
            handle = self.win32print.OpenPrinter(clean_name)
            if handle:
                try:
                    printer_info = self.win32print.GetPrinter(handle, 2)
                    status_code = printer_info.get("Status", 0)
                    
                    # Проверка флагов статуса
                    if status_code & self.win32print.PRINTER_STATUS_OFFLINE:
                        return "offline"
                    elif status_code & self.win32print.PRINTER_STATUS_ERROR:
                        return "error"
                    elif status_code & self.win32print.PRINTER_STATUS_PAPER_JAM:
                        return "paper_jam"
                    elif status_code & self.win32print.PRINTER_STATUS_PAPER_OUT:
                        return "paper_out"
                    elif status_code & self.win32print.PRINTER_STATUS_PAUSED:
                        return "paused"
                    else:
                        return "ready"
                finally:
                    self.win32print.ClosePrinter(handle)
            else:
                return "unknown"
        except Exception as e:
            # Принтер может быть виртуальным, сетевым офлайн или имя не совпадает
            return "unknown"
    
    def is_printer_ready(self, printer_name: str) -> bool:
        """Проверить, готов ли принтер к печати."""
        status = self._get_printer_status(printer_name)
        return status == "ready"
    
    def cancel_print_jobs_by_prefix(self, prefix: str):
        """
        Отменить все задания печати, имя которых начинается с префикса.
        """
        if self.win32print is None:
            print("Info: Отмена заданий печати недоступна (не Windows или нет pywin32)")
            return
        
        printers = self.get_all_printers()
        
        for printer_info in printers:
            printer_name = printer_info["name"]
            try:
                handle = self.win32print.OpenPrinter(printer_name)
                if not handle:
                    continue
                
                try:
                    # Получить список заданий
                    jobs = self.win32print.EnumJobs(handle, 0, -1, 1)
                    
                    for job in jobs:
                        job_id = job["JobId"]
                        job_name = job.get("Document", "")
                        
                        # Проверка префикса
                        if job_name.startswith(prefix):
                            try:
                                self.win32print.SetJob(handle, job_id, 0, None, 
                                                      self.win32print.JOB_CONTROL_DELETE)
                                print(f"Задание {job_id} ({job_name}) удалено из очереди {printer_name}")
                            except Exception as e:
                                print(f"Ошибка удаления задания {job_id}: {e}")
                finally:
                    self.win32print.ClosePrinter(handle)
            except Exception as e:
                print(f"Ошибка обработки принтера {printer_name}: {e}")
