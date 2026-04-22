"""
Модуль конфигурации и работы с JSON.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class Config:
    """Класс для управления конфигурацией приложения."""
    
    DEFAULT_DUPLEX_MODE = "none"
    DEFAULT_SUMATRA_NAME = "SumatraPDF.exe"
    TEMP_DIR_NAME = "SchoolExamPrinter"
    
    def __init__(self):
        self.classes: List[Dict[str, Any]] = []
        self.subjects: List[Dict[str, Any]] = []
        self.printers: List[Dict[str, Any]] = []
        self.settings: Dict[str, Any] = {
            "duplex_mode": self.DEFAULT_DUPLEX_MODE,
            "sumatra_path": "",
            "last_config_path": "",
            "temp_dir": ""
        }
        self.config_path: Optional[str] = None
    
    def get_temp_dir(self) -> Path:
        """Получить директорию для временных файлов."""
        if self.settings.get("temp_dir"):
            return Path(self.settings["temp_dir"])
        
        temp_base = Path(os.environ.get("TEMP", os.environ.get("TMP", "/tmp")))
        temp_dir = temp_base / self.TEMP_DIR_NAME
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir
    
    def set_sumatra_path(self, path: str):
        """Установить путь к SumatraPDF."""
        self.settings["sumatra_path"] = path
    
    def get_sumatra_path(self) -> str:
        """Получить путь к SumatraPDF."""
        return self.settings.get("sumatra_path", "")
    
    def add_class(self, parallel: int, letter: str, students: int):
        """Добавить класс."""
        class_id = f"{parallel}{letter}"
        # Проверка на уникальность
        for cls in self.classes:
            if f"{cls['parallel']}{cls['letter']}" == class_id:
                raise ValueError(f"Класс {class_id} уже существует")
        
        self.classes.append({
            "parallel": parallel,
            "letter": letter,
            "students": students
        })
    
    def remove_class(self, parallel: int, letter: str):
        """Удалить класс."""
        class_id = f"{parallel}{letter}"
        self.classes = [c for c in self.classes 
                       if f"{c['parallel']}{c['letter']}" != class_id]
    
    def update_class(self, parallel: int, letter: str, students: int):
        """Обновить количество учеников в классе."""
        class_id = f"{parallel}{letter}"
        for cls in self.classes:
            if f"{cls['parallel']}{cls['letter']}" == class_id:
                cls["students"] = students
                return
        raise ValueError(f"Класс {class_id} не найден")
    
    def get_class_id(self, parallel: int, letter: str) -> str:
        """Получить идентификатор класса."""
        return f"{parallel}{letter}"
    
    def get_total_students(self, class_ids: List[str]) -> int:
        """Получить общее количество учеников по списку классов."""
        total = 0
        for cls in self.classes:
            class_id = self.get_class_id(cls["parallel"], cls["letter"])
            if class_id in class_ids:
                total += cls["students"]
        return total
    
    def add_subject(self, name: str, target_classes: List[str], has_two_parts: bool = False):
        """Добавить предмет."""
        for subj in self.subjects:
            if subj["name"] == name:
                raise ValueError(f"Предмет '{name}' уже существует")
        
        self.subjects.append({
            "name": name,
            "target_classes": target_classes,
            "has_two_parts": has_two_parts,
            "files": {
                "variant_1": {"part_1": "", "part_2": ""},
                "variant_2": {"part_1": "", "part_2": ""}
            }
        })
    
    def remove_subject(self, name: str):
        """Удалить предмет."""
        self.subjects = [s for s in self.subjects if s["name"] != name]
    
    def get_subject(self, name: str) -> Optional[Dict[str, Any]]:
        """Получить предмет по имени."""
        for subj in self.subjects:
            if subj["name"] == name:
                return subj
        return None
    
    def set_subject_file(self, subject_name: str, variant: str, part: str, file_path: str):
        """Установить путь к файлу для предмета."""
        subject = self.get_subject(subject_name)
        if not subject:
            raise ValueError(f"Предмет '{subject_name}' не найден")
        
        if variant not in subject["files"]:
            subject["files"][variant] = {}
        
        subject["files"][variant][part] = file_path
    
    def add_printer(self, name: str, enabled: bool = False):
        """Добавить принтер."""
        for printer in self.printers:
            if printer["name"] == name:
                return  # Уже существует
        
        self.printers.append({
            "name": name,
            "enabled": enabled
        })
    
    def set_printer_enabled(self, name: str, enabled: bool):
        """Установить статус принтера."""
        for printer in self.printers:
            if printer["name"] == name:
                printer["enabled"] = enabled
                return
    
    def get_enabled_printers(self) -> List[str]:
        """Получить список включённых принтеров."""
        return [p["name"] for p in self.printers if p["enabled"]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать конфигурацию в словарь."""
        return {
            "classes": self.classes,
            "subjects": self.subjects,
            "printers": self.printers,
            "settings": self.settings
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Загрузить конфигурацию из словаря."""
        self.classes = data.get("classes", [])
        self.subjects = data.get("subjects", [])
        self.printers = data.get("printers", [])
        self.settings = data.get("settings", {
            "duplex_mode": self.DEFAULT_DUPLEX_MODE,
            "sumatra_path": "",
            "last_config_path": "",
            "temp_dir": ""
        })
    
    def save(self, path: Optional[str] = None) -> str:
        """Сохранить конфигурацию в файл."""
        if path is None:
            path = self.config_path or "config.json"
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        self.config_path = path
        self.settings["last_config_path"] = path
        return path
    
    def load(self, path: str):
        """Загрузить конфигурацию из файла."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.from_dict(data)
        self.config_path = path
        self.settings["last_config_path"] = path
