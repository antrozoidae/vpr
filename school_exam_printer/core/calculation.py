"""
Модуль расчёта тиражей и распределения по принтерам.
"""
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class PrintJob:
    """Задание на печать."""
    subject: str
    variant: int
    printer: str
    copies: int
    duplex_mode: str
    file_path: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "variant": self.variant,
            "printer": self.printer,
            "copies": self.copies,
            "duplex_mode": self.duplex_mode,
            "file_path": self.file_path
        }


class CalculationEngine:
    """Движок расчёта тиражей."""
    
    def __init__(self, config):
        self.config = config
    
    def calculate_variants(self, total_students: int) -> Tuple[int, int]:
        """
        Рассчитать количество учеников для каждого варианта.
        При нечётном числе: Вариант 1 = ceil(N/2), Вариант 2 = floor(N/2)
        """
        variant1 = math.ceil(total_students / 2)
        variant2 = total_students // 2
        return variant1, variant2
    
    def distribute_copies(self, copies: int, printers: List[str]) -> List[Tuple[str, int]]:
        """
        Распределить копии между принтерами равномерно.
        Остаток распределяется последовательно на первые N принтеров.
        """
        if not printers:
            return []
        
        base_copies = copies // len(printers)
        remainder = copies % len(printers)
        
        distribution = []
        for i, printer in enumerate(printers):
            printer_copies = base_copies + (1 if i < remainder else 0)
            if printer_copies > 0:
                distribution.append((printer, printer_copies))
        
        return distribution
    
    def calculate_print_jobs(
        self,
        subject_name: str,
        enabled_printers: List[str],
        duplex_mode: str
    ) -> List[PrintJob]:
        """
        Рассчитать все задания на печать для предмета.
        """
        jobs = []
        subject = self.config.get_subject(subject_name)
        
        if not subject:
            return jobs
        
        # Получить общее количество учеников для целевых классов
        total_students = self.config.get_total_students(subject["target_classes"])
        
        if total_students == 0 or not enabled_printers:
            return jobs
        
        # Рассчитать варианты
        variant1_copies, variant2_copies = self.calculate_variants(total_students)
        
        variants_data = [
            (1, variant1_copies, "variant_1"),
            (2, variant2_copies, "variant_2")
        ]
        
        for variant_num, copies, variant_key in variants_data:
            if copies <= 0:
                continue
            
            # Получить путь к файлу
            file_path = self._get_file_path(subject, variant_key)
            
            if not file_path:
                continue
            
            # Распределить копии по принтерам
            distribution = self.distribute_copies(copies, enabled_printers)
            
            for printer, printer_copies in distribution:
                jobs.append(PrintJob(
                    subject=subject_name,
                    variant=variant_num,
                    printer=printer,
                    copies=printer_copies,
                    duplex_mode=duplex_mode,
                    file_path=file_path
                ))
        
        return jobs
    
    def _get_file_path(self, subject: Dict[str, Any], variant_key: str) -> str:
        """Получить путь к файлу для варианта."""
        files = subject.get("files", {})
        variant_data = files.get(variant_key, {})
        
        if subject.get("has_two_parts", False):
            # Если две части, нужна склейка - возвращаем пустую строку
            # Фактический путь будет определён после склейки
            part1 = variant_data.get("part_1", "")
            part2 = variant_data.get("part_2", "")
            if part1 and part2:
                return f"{part1}+{part2}"  # Маркер для склейки
            return ""
        else:
            # Если одна часть, используем part_1
            return variant_data.get("part_1", "")
    
    def calculate_all_jobs(
        self,
        enabled_printers: List[str],
        duplex_mode: str
    ) -> List[PrintJob]:
        """Рассчитать все задания для всех предметов."""
        all_jobs = []
        
        for subject in self.config.subjects:
            jobs = self.calculate_print_jobs(
                subject["name"],
                enabled_printers,
                duplex_mode
            )
            all_jobs.extend(jobs)
        
        return all_jobs
    
    def get_calculation_summary(self) -> List[Dict[str, Any]]:
        """Получить сводку расчёта для отображения в UI."""
        enabled_printers = self.config.get_enabled_printers()
        duplex_mode = self.config.settings.get("duplex_mode", "none")
        
        if not enabled_printers:
            return []
        
        jobs = self.calculate_all_jobs(enabled_printers, duplex_mode)
        return [job.to_dict() for job in jobs]
