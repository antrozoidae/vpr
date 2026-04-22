"""
Модуль работы с PDF: склейка, валидация, управление временными файлами
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

try:
    from pypdf import PdfReader, PdfWriter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class PDFManager:
    """Управление PDF файлами"""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_pdf(self, file_path: str) -> Tuple[bool, str]:
        """
        Проверить существование и валидность PDF файла
        Возвращает (успех, сообщение)
        """
        if not file_path:
            return False, "Путь к файлу не указан"
        
        if not os.path.exists(file_path):
            return False, f"Файл не найден: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Не является файлом: {file_path}"
        
        if not file_path.lower().endswith('.pdf'):
            return False, f"Не является PDF файлом: {file_path}"
        
        if not PYPDF_AVAILABLE:
            # Если pypdf недоступен, делаем минимальную проверку
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    if not header.startswith(b'%PDF'):
                        return False, "Неверный формат PDF"
                return True, "OK"
            except Exception as e:
                return False, f"Ошибка чтения файла: {str(e)}"
        
        try:
            reader = PdfReader(file_path)
            if len(reader.pages) == 0:
                return False, "PDF файл пустой"
            return True, f"OK ({len(reader.pages)} стр.)"
        except Exception as e:
            return False, f"Ошибка чтения PDF: {str(e)}"
    
    def merge_pdfs(self, files: List[str], output_name: Optional[str] = None) -> Tuple[Optional[Path], str]:
        """
        Склеить несколько PDF файлов в один
        Возвращает путь к результату и сообщение
        """
        if not files:
            return None, "Список файлов пуст"
        
        if not PYPDF_AVAILABLE:
            return None, "Библиотека pypdf недоступна"
        
        # Проверка всех входных файлов
        for file_path in files:
            valid, msg = self.validate_pdf(file_path)
            if not valid:
                return None, f"Ошибка файла {file_path}: {msg}"
        
        try:
            writer = PdfWriter()
            
            for file_path in files:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    writer.add_page(page)
            
            # Генерация имени выходного файла
            if output_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"merged_{timestamp}.pdf"
            
            output_path = self.temp_dir / output_name
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return output_path, f"Успешно создано: {output_path}"
            
        except Exception as e:
            return None, f"Ошибка склейки: {str(e)}"
    
    def merge_two_parts(self, part_1: str, part_2: str, subject: str, grade: str, variant: int) -> Tuple[Optional[Path], str]:
        """
        Склеить две части экзамена в один файл
        """
        output_name = f"{subject}_{grade}_var{variant}_merged.pdf"
        # Очистить имя от недопустимых символов
        output_name = "".join(c for c in output_name if c.isalnum() or c in "._- ")
        return self.merge_pdfs([part_1, part_2], output_name)
    
    def cleanup_temp_dir(self, keep_recent_hours: int = 24) -> int:
        """
        Очистить временную директорию от старых файлов
        Возвращает количество удалённых файлов
        """
        if not self.temp_dir.exists():
            return 0
        
        deleted_count = 0
        now = datetime.now()
        
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    age_hours = (now - mtime).total_seconds() / 3600
                    
                    if age_hours > keep_recent_hours:
                        file_path.unlink()
                        deleted_count += 1
                except Exception:
                    pass
        
        return deleted_count
    
    def remove_file(self, file_path: Path) -> bool:
        """Удалить конкретный файл"""
        try:
            if file_path and file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def get_temp_files(self) -> List[Path]:
        """Получить список временных файлов"""
        if not self.temp_dir.exists():
            return []
        return [f for f in self.temp_dir.iterdir() if f.is_file()]


class PrintLogger:
    """Логирование операций печати"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Записать сообщение в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Ошибка записи в лог: {e}")
    
    def log_print_task(
        self,
        subject: str,
        grade: str,
        variant: int,
        printer: str,
        copies: int,
        status: str,
        return_code: int = 0,
        duplex: str = "none"
    ) -> None:
        """Записать информацию о задаче печати"""
        message = (
            f"Печать | Предмет: {subject} | Параллель: {grade} | "
            f"Вариант: {variant} | Принтер: {printer} | "
            f"Копий: {copies} | Дуплекс: {duplex} | "
            f"Статус: {status} | Код возврата: {return_code}"
        )
        level = "INFO" if status == "OK" else "ERROR"
        self.log(message, level)
    
    def clear(self) -> None:
        """Очистить лог файл"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("")
        except Exception:
            pass
    
    def get_recent_logs(self, lines: int = 100) -> List[str]:
        """Получить последние строки лога"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except Exception:
            return []
