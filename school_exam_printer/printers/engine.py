"""
Модуль печати через SumatraPDF CLI.
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class PrintResult:
    """Результат печати."""
    success: bool
    return_code: int
    message: str
    job_info: dict


class PrintEngine:
    """Движок печати через SumatraPDF."""
    
    JOB_PREFIX = "ExamPrint_"
    
    def __init__(self, sumatra_path: str, log_file: str = "print_log.txt"):
        self.sumatra_path = sumatra_path
        self.log_file = log_file
        self.cancel_flag = False
        self._setup_logging()
    
    def _setup_logging(self):
        """Настроить логирование."""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
    
    def set_cancel_flag(self, value: bool):
        """Установить флаг отмены."""
        self.cancel_flag = value
    
    def is_cancelled(self) -> bool:
        """Проверить флаг отмены."""
        return self.cancel_flag
    
    def validate_sumatra(self) -> bool:
        """Проверить доступность SumatraPDF."""
        if not self.sumatra_path:
            return False
        
        path = Path(self.sumatra_path)
        if not path.exists():
            # Попробовать найти в PATH
            try:
                result = subprocess.run(
                    ["SumatraPDF.exe", "-?"],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
            except Exception:
                return False
        
        return path.is_file()
    
    def _build_command(
        self,
        file_path: str,
        printer_name: str,
        duplex_mode: str
    ) -> list:
        """Построить команду для SumatraPDF CLI."""
        # Маппинг режима дуплекса
        duplex_map = {
            "none": "none",
            "long": "longside",
            "short": "shortside"
        }
        duplex_value = duplex_map.get(duplex_mode, "none")
        
        cmd = [
            self.sumatra_path,
            "-print-to", printer_name,
            "-print-settings", f"duplex={duplex_value}",
            "-silent",
            file_path
        ]
        
        return cmd
    
    def print_file(
        self,
        file_path: str,
        printer_name: str,
        duplex_mode: str,
        copies: int,
        subject: str,
        variant: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> PrintResult:
        """
        Отправить файл на печать.
        
        Args:
            file_path: Путь к PDF файлу
            printer_name: Имя принтера
            duplex_mode: Режим дуплекса
            copies: Количество копий
            subject: Название предмета (для логов)
            variant: Номер варианта (для логов)
            progress_callback: Callback для обновления прогресса
        
        Returns:
            PrintResult с результатом операции
        """
        if self.is_cancelled():
            return PrintResult(
                success=False,
                return_code=-1,
                message="Печать отменена пользователем",
                job_info={"subject": subject, "variant": variant, "printer": printer_name}
            )
        
        # Валидация SumatraPDF
        if not self.validate_sumatra():
            msg = "SumatraPDF не найден"
            self.logger.error(msg)
            return PrintResult(
                success=False,
                return_code=-2,
                message=msg,
                job_info={"subject": subject, "variant": variant, "printer": printer_name}
            )
        
        # Построение команды
        cmd = self._build_command(file_path, printer_name, duplex_mode)
        
        job_info = {
            "subject": subject,
            "variant": variant,
            "printer": printer_name,
            "copies": copies,
            "duplex_mode": duplex_mode,
            "file": file_path
        }
        
        self.logger.info(f"Начало печати: {job_info}")
        
        try:
            # Печать каждой копии
            for i in range(copies):
                if self.is_cancelled():
                    msg = f"Печать отменена после {i} из {copies} копий"
                    self.logger.warning(msg)
                    return PrintResult(
                        success=False,
                        return_code=-1,
                        message=msg,
                        job_info=job_info
                    )
                
                if progress_callback:
                    progress_callback(i, copies, f"{subject} Вариант {variant} ({printer_name})")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60  # Таймаут на одну копию
                )
                
                if result.returncode != 0:
                    msg = f"Ошибка печати: код возврата {result.returncode}"
                    if result.stderr:
                        msg += f" - {result.stderr}"
                    
                    self.logger.error(f"{msg}: {job_info}")
                    return PrintResult(
                        success=False,
                        return_code=result.returncode,
                        message=msg,
                        job_info=job_info
                    )
            
            self.logger.info(f"Печать завершена успешно: {job_info}")
            
            if progress_callback:
                progress_callback(copies, copies, f"{subject} Вариант {variant} ({printer_name})")
            
            return PrintResult(
                success=True,
                return_code=0,
                message="Печать завершена успешно",
                job_info=job_info
            )
            
        except subprocess.TimeoutExpired:
            msg = "Таймаут при печати"
            self.logger.error(f"{msg}: {job_info}")
            return PrintResult(
                success=False,
                return_code=-3,
                message=msg,
                job_info=job_info
            )
        except Exception as e:
            msg = f"Исключение при печати: {str(e)}"
            self.logger.error(f"{msg}: {job_info}")
            return PrintResult(
                success=False,
                return_code=-4,
                message=msg,
                job_info=job_info
            )
