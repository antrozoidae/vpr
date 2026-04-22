"""
Модуль работы с PDF: склейка, валидация.
"""
import os
from pathlib import Path
from typing import List, Optional
from pypdf import PdfReader, PdfWriter


class PDFProcessor:
    """Обработчик PDF файлов."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
    
    def validate_pdf(self, file_path: str) -> bool:
        """Проверить существование и читаемость PDF файла."""
        if not file_path:
            return False
        
        path = Path(file_path)
        if not path.exists():
            return False
        
        if not path.is_file():
            return False
        
        # Проверка расширения
        if path.suffix.lower() != '.pdf':
            return False
        
        # Попытка открыть файл для проверки целостности
        try:
            with open(path, 'rb') as f:
                # Проверка заголовка PDF
                header = f.read(5)
                if not header.startswith(b'%PDF'):
                    return False
            return True
        except (IOError, OSError):
            return False
    
    def merge_pdfs(self, pdf_paths: List[str], output_name: Optional[str] = None) -> Optional[str]:
        """
        Склеить несколько PDF файлов в один.
        Возвращает путь к временному файлу или None при ошибке.
        """
        if not pdf_paths:
            return None
        
        # Валидация всех входных файлов
        valid_paths = []
        for path in pdf_paths:
            if self.validate_pdf(path):
                valid_paths.append(path)
            else:
                return None  # Ошибка валидации
        
        if len(valid_paths) != len(pdf_paths):
            return None
        
        # Создать имя выходного файла
        if output_name is None:
            import hashlib
            import time
            hash_input = "".join(pdf_paths) + str(time.time())
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            output_name = f"merged_{hash_value}.pdf"
        
        output_path = self.temp_dir / output_name
        
        try:
            writer = PdfWriter()
            
            for pdf_path in valid_paths:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return str(output_path)
        except Exception as e:
            print(f"Ошибка склейки PDF: {e}")
            return None
    
    def cleanup_temp_files(self):
        """Очистить временные файлы."""
        try:
            for file in self.temp_dir.glob("*.pdf"):
                file.unlink()
        except Exception as e:
            print(f"Ошибка очистки временных файлов: {e}")
    
    def get_or_create_merged_pdf(self, file_path_marker: str) -> Optional[str]:
        """
        Получить или создать склеенный PDF из маркера пути.
        Маркер имеет формат: "path1.pdf+path2.pdf"
        """
        if '+' not in file_path_marker:
            # Это не маркер склейки, проверяем существование
            if self.validate_pdf(file_path_marker):
                return file_path_marker
            return None
        
        # Разделить маркер на части
        parts = file_path_marker.split('+')
        
        if len(parts) != 2:
            return None
        
        return self.merge_pdfs(parts)
