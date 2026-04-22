"""
SchoolExamPrinter - Автоматизация печати экзаменационных материалов.

Приложение для автоматизации расчёта тиражей и печати экзаменационных материалов.
"""

import sys
from pathlib import Path

# Добавляем корень проекта в PATH для корректного импорта
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui.main_window import main

if __name__ == "__main__":
    main()
