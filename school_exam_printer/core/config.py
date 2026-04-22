"""
Модель данных и конфигурации приложения
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class PrinterConfig:
    """Конфигурация принтера"""
    name: str
    enabled: bool = False
    duplex_mode: str = "none"  # none, long, short


@dataclass
class SubjectFileConfig:
    """Конфигурация файлов для варианта"""
    part_1: str = ""
    part_2: str = ""
    single: str = ""


@dataclass
class SubjectConfig:
    """Конфигурация предмета"""
    name: str
    matrix: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    files: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "matrix": self.matrix,
            "files": self.files
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SubjectConfig':
        return cls(
            name=data.get("name", ""),
            matrix=data.get("matrix", {}),
            files=data.get("files", {})
        )


@dataclass
class AppConfig:
    """Основная конфигурация приложения"""
    letters: List[str] = field(default_factory=lambda: ["А", "Б", "В", "Г"])
    classes_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)
    subjects: List[SubjectConfig] = field(default_factory=list)
    printers: List[PrinterConfig] = field(default_factory=list)
    sumatra_path: str = ""
    last_config_path: str = ""
    
    # Настройки по умолчанию
    DEFAULT_SUMATRA_PATHS = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
    ]
    
    def get_temp_dir(self) -> Path:
        """Получить директорию для временных файлов"""
        import tempfile
        base_temp = Path(tempfile.gettempdir())
        temp_dir = base_temp / "SchoolExamPrinter"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir
    
    def get_log_file(self) -> Path:
        """Получить путь к файлу логов"""
        return self.get_temp_dir() / "print_log.txt"
    
    def save(self, path: str) -> None:
        """Сохранить конфигурацию в JSON файл"""
        data = {
            "letters": self.letters,
            "classes_matrix": self.classes_matrix,
            "subjects": [s.to_dict() for s in self.subjects],
            "printers": [
                {"name": p.name, "enabled": p.enabled, "duplex_mode": p.duplex_mode}
                for p in self.printers
            ],
            "settings": {
                "sumatra_path": self.sumatra_path,
                "last_config_path": path,
                "duplex_mode": "long",
                "temp_dir": str(self.get_temp_dir())
            }
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.last_config_path = path
    
    @classmethod
    def load(cls, path: str) -> 'AppConfig':
        """Загрузить конфигурацию из JSON файла"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = cls()
        config.letters = data.get("letters", ["А", "Б", "В", "Г"])
        config.classes_matrix = data.get("classes_matrix", {})
        config.subjects = [SubjectConfig.from_dict(s) for s in data.get("subjects", [])]
        
        printers_data = data.get("printers", [])
        config.printers = [
            PrinterConfig(
                name=p.get("name", ""),
                enabled=p.get("enabled", False),
                duplex_mode=p.get("duplex_mode", "none")
            )
            for p in printers_data
        ]
        
        settings = data.get("settings", {})
        config.sumatra_path = settings.get("sumatra_path", "")
        config.last_config_path = path
        
        return config
    
    @classmethod
    def create_empty(cls) -> 'AppConfig':
        """Создать пустую конфигурацию"""
        return cls()
    
    def find_sumatra_pdf(self) -> Optional[str]:
        """Найти установленный SumatraPDF"""
        # Проверка сохранённого пути
        if self.sumatra_path and os.path.exists(self.sumatra_path):
            return self.sumatra_path
        
        # Поиск по стандартным путям
        for path in self.DEFAULT_SUMATRA_PATHS:
            if os.path.exists(path):
                self.sumatra_path = path
                return path
        
        return None
    
    def add_subject(self, name: str) -> SubjectConfig:
        """Добавить новый предмет"""
        subject = SubjectConfig(name=name)
        self.subjects.append(subject)
        return subject
    
    def remove_subject(self, name: str) -> bool:
        """Удалить предмет по имени"""
        for i, subj in enumerate(self.subjects):
            if subj.name == name:
                self.subjects.pop(i)
                return True
        return False
    
    def get_subject(self, name: str) -> Optional[SubjectConfig]:
        """Получить предмет по имени"""
        for subj in self.subjects:
            if subj.name == name:
                return subj
        return None
    
    def get_enabled_printers(self) -> List[PrinterConfig]:
        """Получить список включённых принтеров"""
        return [p for p in self.printers if p.enabled]
    
    def get_active_classes_for_grade(self, grade: str) -> List[str]:
        """Получить список активных классов для параллели"""
        if grade not in self.classes_matrix:
            return []
        
        active = []
        for letter in self.letters:
            count = self.classes_matrix[grade].get(letter, 0)
            if count > 0:
                active.append(letter)
        return active
    
    def get_total_students(self, grade: str, letters: List[str]) -> int:
        """Получить общее количество учеников"""
        total = 0
        if grade in self.classes_matrix:
            for letter in letters:
                total += self.classes_matrix[grade].get(letter, 0)
        return total
