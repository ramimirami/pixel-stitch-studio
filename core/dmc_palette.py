import csv
import os

import numpy as np

# CSV лежит в assets/dmc_colors.csv — рядом с остальными ассетами приложения
_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "dmc_colors.csv")

_cache = None


def get_dmc_palette():
    """
    Загружает и кеширует палитру мулине DMC из assets/dmc_colors.csv.

    Возвращает словарь:
        "entries"   — список словарей {"code", "name", "rgb", "hex"} для каждого цвета DMC
        "rgb_array" — numpy-массив (N, 3) с теми же RGB, для быстрого поиска ближайшего цвета

    Файл читается с диска только один раз за время работы приложения —
    повторные вызовы возвращают уже готовые данные из памяти.
    """
    global _cache
    if _cache is not None:
        return _cache

    entries = []
    with open(_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append({
                "code": row["code"],
                "name": row["name"],
                "rgb": (int(row["r"]), int(row["g"]), int(row["b"])),
                "hex": row["hex"],
            })

    if not entries:
        raise ValueError(f"Файл палитры DMC пуст или не найден: {_CSV_PATH}")

    rgb_array = np.array([e["rgb"] for e in entries], dtype=float)

    _cache = {"entries": entries, "rgb_array": rgb_array}
    return _cache