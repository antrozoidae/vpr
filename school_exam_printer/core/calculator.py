"""
Модуль расчёта тиражей и распределения по принтерам
"""

import math
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

from .config import AppConfig, SubjectConfig, PrinterConfig


@dataclass
class PrintTask:
    """Задача на печать"""
    subject: str
    grade: str
    variant: int  # 1 или 2
    printer: str
    copies: int
    duplex_mode: str
    file_path: str
    is_two_parts: bool = False
    part_1_file: str = ""
    part_2_file: str = ""


class CalculationEngine:
    """Движок расчёта тиражей и распределения"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def calculate_variants(self, total_students: int) -> Tuple[int, int]:
        """
        Рассчитать количество вариантов 1 и 2
        Вариант 1 = ceil(N/2), Вариант 2 = floor(N/2)
        """
        variant_1 = math.ceil(total_students / 2)
        variant_2 = total_students // 2
        return variant_1, variant_2
    
    def distribute_copies(self, copies: int, printers: List[PrinterConfig]) -> List[Tuple[str, int]]:
        """
        Равномерно распределить копии между принтерами
        Остаток распределяется последовательно на первые N принтеров
        """
        if not printers:
            return []
        
        num_printers = len(printers)
        base_copies = copies // num_printers
        remainder = copies % num_printers
        
        distribution = []
        for i, printer in enumerate(printers):
            printer_copies = base_copies + (1 if i < remainder else 0)
            if printer_copies > 0:
                distribution.append((printer.name, printer_copies))
        
        return distribution
    
    def calculate_subject_tasks(
        self, 
        subject: SubjectConfig, 
        printers: List[PrinterConfig]
    ) -> List[PrintTask]:
        """Рассчитать задачи печати для предмета"""
        tasks = []
        
        for grade, grade_data in subject.matrix.items():
            selected_letters = grade_data.get("selected_letters", [])
            two_parts = grade_data.get("two_parts", False)
            
            if not selected_letters:
                continue
            
            # Получить количество учеников для выбранных классов
            total_students = self.config.get_total_students(grade, selected_letters)
            
            if total_students == 0:
                continue
            
            # Рассчитать варианты
            v1_copies, v2_copies = self.calculate_variants(total_students)
            
            # Распределить по принтерам для варианта 1
            v1_distribution = self.distribute_copies(v1_copies, printers)
            for printer_name, copies in v1_distribution:
                printer = next((p for p in printers if p.name == printer_name), None)
                duplex = printer.duplex_mode if printer else "none"
                
                task = PrintTask(
                    subject=subject.name,
                    grade=grade,
                    variant=1,
                    printer=printer_name,
                    copies=copies,
                    duplex_mode=duplex,
                    file_path="",
                    is_two_parts=two_parts
                )
                
                # Добавить информацию о файлах
                files_data = subject.files.get(grade, {}).get("variant_1", {})
                if two_parts:
                    task.part_1_file = files_data.get("part_1", "")
                    task.part_2_file = files_data.get("part_2", "")
                else:
                    task.file_path = files_data.get("single", "")
                
                tasks.append(task)
            
            # Распределить по принтерам для варианта 2
            v2_distribution = self.distribute_copies(v2_copies, printers)
            for printer_name, copies in v2_distribution:
                printer = next((p for p in printers if p.name == printer_name), None)
                duplex = printer.duplex_mode if printer else "none"
                
                task = PrintTask(
                    subject=subject.name,
                    grade=grade,
                    variant=2,
                    printer=printer_name,
                    copies=copies,
                    duplex_mode=duplex,
                    file_path="",
                    is_two_parts=two_parts
                )
                
                # Добавить информацию о файлах
                files_data = subject.files.get(grade, {}).get("variant_2", {})
                if two_parts:
                    task.part_1_file = files_data.get("part_1", "")
                    task.part_2_file = files_data.get("part_2", "")
                else:
                    task.file_path = files_data.get("single", "")
                
                tasks.append(task)
        
        return tasks
    
    def calculate_all_tasks(self) -> List[PrintTask]:
        """Рассчитать все задачи печати для всех предметов"""
        all_tasks = []
        printers = self.config.get_enabled_printers()
        
        if not printers:
            return all_tasks
        
        for subject in self.config.subjects:
            tasks = self.calculate_subject_tasks(subject, printers)
            all_tasks.extend(tasks)
        
        return all_tasks
    
    def get_calculation_summary(self) -> Dict[str, Any]:
        """Получить сводку расчёта"""
        tasks = self.calculate_all_tasks()
        
        summary = {
            "total_tasks": len(tasks),
            "total_copies": sum(t.copies for t in tasks),
            "by_subject": {},
            "by_printer": {},
            "by_grade": {}
        }
        
        for task in tasks:
            # По предметам
            if task.subject not in summary["by_subject"]:
                summary["by_subject"][task.subject] = {"tasks": 0, "copies": 0}
            summary["by_subject"][task.subject]["tasks"] += 1
            summary["by_subject"][task.subject]["copies"] += task.copies
            
            # По принтерам
            if task.printer not in summary["by_printer"]:
                summary["by_printer"][task.printer] = {"tasks": 0, "copies": 0}
            summary["by_printer"][task.printer]["tasks"] += 1
            summary["by_printer"][task.printer]["copies"] += task.copies
            
            # По параллелям
            if task.grade not in summary["by_grade"]:
                summary["by_grade"][task.grade] = {"tasks": 0, "copies": 0}
            summary["by_grade"][task.grade]["tasks"] += 1
            summary["by_grade"][task.grade]["copies"] += task.copies
        
        return summary
