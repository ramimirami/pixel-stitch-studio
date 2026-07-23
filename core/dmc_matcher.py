import numpy as np

from core.dmc_palette import get_dmc_palette


def find_nearest_dmc(rgb):
    """
    Находит ближайший цвет мулине DMC для одного RGB-цвета.

    rgb: кортеж (r, g, b) — цвет из палитры схемы.

    Возвращает словарь: {"code", "name", "rgb", "hex"} — ближайший цвет DMC.

    Для сравнения используется формула "redmean" — взвешенное расстояние
    между цветами, которое учитывает особенности восприятия цвета человеческим
    глазом лучше, чем простое сравнение по прямой линии в RGB-кубе.
    """
    palette = get_dmc_palette()
    r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])

    colors = palette["rgb_array"]  # numpy-массив (N, 3): все цвета DMC

    dr = colors[:, 0] - r
    dg = colors[:, 1] - g
    db = colors[:, 2] - b
    rmean = (colors[:, 0] + r) / 2.0

    # "redmean" — взвешенное евклидово расстояние между цветами
    dist_sq = (2 + rmean / 256.0) * dr ** 2 + 4 * dg ** 2 + (2 + (255 - rmean) / 256.0) * db ** 2

    best_index = int(np.argmin(dist_sq))
    entry = palette["entries"][best_index]

    return {
        "code": entry["code"],
        "name": entry["name"],
        "rgb": entry["rgb"],
        "hex": entry["hex"],
    }


def match_dmc_colors(palette_stats):
    """
    Дополняет palette_stats (результат get_palette_stats() + assign_symbols())
    информацией о ближайшем цвете мулине DMC для каждого цвета схемы.

    Добавляет в каждый элемент списка поля:
        "dmc_code" — номер мулине DMC, например "310"
        "dmc_name" — название цвета DMC, например "Black"
        "dmc_rgb"  — RGB ближайшего цвета мулине, кортеж (r, g, b)
        "dmc_hex"  — HEX ближайшего цвета мулине, например "#000000"

    Возвращает тот же список (изменённый на месте), чтобы вызов можно было
    использовать как: palette_stats = match_dmc_colors(palette_stats)
    """
    for color in palette_stats:
        match = find_nearest_dmc(color["rgb"])
        color["dmc_code"] = match["code"]
        color["dmc_name"] = match["name"]
        color["dmc_rgb"] = match["rgb"]
        color["dmc_hex"] = match["hex"]

    return palette_stats