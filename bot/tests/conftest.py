import sys
from pathlib import Path

# Плоская структура bot/: тесты импортируют модули (config, db, ...) по имени.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
