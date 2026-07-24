from PIL import Image, ImageDraw, ImageFont

# Цвета взяты из дизайн-концепции (ui/theme.py)
GRID_LINE_COLOR = (42, 42, 52)     # тонкая сетка между клетками
MAJOR_LINE_COLOR = (0, 245, 212)   # Mint Glow — выделение блоков 10x10

GRID_LINE_WIDTH = 1
MAJOR_LINE_WIDTH = 2

DEFAULT_CELL_SIZE_PX = 24
DEFAULT_MAJOR_STEP = 10

SYMBOL_LIGHT_COLOR = (255, 255, 255)
SYMBOL_DARK_COLOR = (18, 18, 20)
MIN_CELL_SIZE_FOR_SYMBOLS = 14  # ниже этого размера символы рисовать не будем — нечитаемо


def _contrast_text_color(rgb):
    """Выбирает тёмный или светлый цвет текста в зависимости от яркости фона."""
    r, g, b = rgb
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return SYMBOL_DARK_COLOR if brightness > 140 else SYMBOL_LIGHT_COLOR

def render_scheme_with_grid(
    processed_image,
    cell_size_px=DEFAULT_CELL_SIZE_PX,
    major_step=DEFAULT_MAJOR_STEP,
    show_symbols=False,
    palette_stats=None,
):
    """
    Превращает "маленькую" обработанную схему (1 пиксель = 1 клетка)
    в увеличенное изображение с наложенной сеткой.

    processed_image: PIL.Image, размер = grid_width x grid_height
    cell_size_px: размер одной клетки в итоговом изображении (в пикселях)
    major_step: через сколько клеток рисовать жирную линию (блоки 10x10)
    show_symbols: рисовать ли числовые символы внутри клеток
    palette_stats: список из get_palette_stats() + assign_symbols(),
                   нужен только если show_symbols=True
    """

    grid_width, grid_height = processed_image.size

    output_width = grid_width * cell_size_px
    output_height = grid_height * cell_size_px

    # NEAREST — чтобы клетки остались четкими квадратами, без размытия
    scheme_image = processed_image.resize(
        (output_width, output_height),
        Image.Resampling.NEAREST,
    ).convert("RGB")

    draw = ImageDraw.Draw(scheme_image)

    # Тонкие вертикальные и горизонтальные линии между клетками
    for x in range(0, grid_width + 1):
        line_x = x * cell_size_px
        draw.line([(line_x, 0), (line_x, output_height)],
                   fill=GRID_LINE_COLOR, width=GRID_LINE_WIDTH)

    for y in range(0, grid_height + 1):
        line_y = y * cell_size_px
        draw.line([(0, line_y), (output_width, line_y)],
                   fill=GRID_LINE_COLOR, width=GRID_LINE_WIDTH)

    # Жирные линии — выделение блоков 10x10
    for x in range(0, grid_width + 1, major_step):
        line_x = x * cell_size_px
        draw.line([(line_x, 0), (line_x, output_height)],
                   fill=MAJOR_LINE_COLOR, width=MAJOR_LINE_WIDTH)

    for y in range(0, grid_height + 1, major_step):
        line_y = y * cell_size_px
        draw.line([(0, line_y), (output_width, line_y)],
                   fill=MAJOR_LINE_COLOR, width=MAJOR_LINE_WIDTH)

    # Числовые символы внутри клеток
    if show_symbols and palette_stats and cell_size_px >= MIN_CELL_SIZE_FOR_SYMBOLS:
        rgb_to_symbol = {tuple(color["rgb"]): color["symbol"] for color in palette_stats}

        font_size = max(8, int(cell_size_px * 0.55))
        try:
            symbol_font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except IOError:
            symbol_font = ImageFont.load_default()

        pixels = processed_image.convert("RGB").load()

        for gy in range(grid_height):
            for gx in range(grid_width):
                cell_rgb = pixels[gx, gy]
                symbol = rgb_to_symbol.get(cell_rgb)
                if symbol is None:
                    continue

                text = str(symbol)
                text_color = _contrast_text_color(cell_rgb)

                cell_x0 = gx * cell_size_px
                cell_y0 = gy * cell_size_px

                bbox = draw.textbbox((0, 0), text, font=symbol_font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]

                text_x = cell_x0 + (cell_size_px - text_w) / 2 - bbox[0]
                text_y = cell_y0 + (cell_size_px - text_h) / 2 - bbox[1]

                draw.text((text_x, text_y), text, fill=text_color, font=symbol_font)

    return scheme_image


PALETTE_BG_COLOR = (18, 18, 20)
PALETTE_CARD_COLOR = (30, 30, 36)
PALETTE_BORDER_COLOR = (42, 42, 52)
PALETTE_TEXT_COLOR = (255, 255, 255)
PALETTE_ACCENT_COLOR = (0, 245, 212)


def render_palette_image(palette_stats, columns=4, card_size=220, padding=18):
    """
    Рисует изображение палитры: карточки с цветом, hex-кодом и процентом покрытия.

    palette_stats: список словарей из get_palette_stats()
    """

    rows = (len(palette_stats) + columns - 1) // columns
    card_w = card_size
    card_h = int(card_size * 1.15)

    total_w = columns * card_w + (columns + 1) * padding
    total_h = rows * card_h + (rows + 1) * padding

    image = Image.new("RGB", (total_w, total_h), PALETTE_BG_COLOR)
    draw = ImageDraw.Draw(image)

    try:
        font_label = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 15)
    except IOError:
        # Если системного шрифта нет — используем встроенный (работает везде)
        font_label = ImageFont.load_default()
        font_small = ImageFont.load_default()

    for i, color in enumerate(palette_stats):
        col = i % columns
        row = i // columns

        x0 = padding + col * (card_w + padding)
        y0 = padding + row * (card_h + padding)
        x1 = x0 + card_w
        y1 = y0 + card_h

        draw.rectangle(
            [x0, y0, x1, y1],
            fill=PALETTE_CARD_COLOR,
            outline=PALETTE_BORDER_COLOR,
            width=2,
        )

        swatch_margin = 14
        swatch_h = int(card_h * 0.55)
        draw.rectangle(
            [x0 + swatch_margin, y0 + swatch_margin,
             x1 - swatch_margin, y0 + swatch_margin + swatch_h],
            fill=color["rgb"],
        )

        text_y = y0 + swatch_margin + swatch_h + 14
        draw.text(
            (x0 + swatch_margin, text_y),
            color["hex"].upper(),
            fill=PALETTE_TEXT_COLOR,
            font=font_label,
        )
        draw.text(
            (x0 + swatch_margin, text_y + 26),
            f"{color['percentage']:.1f}%",
            fill=PALETTE_ACCENT_COLOR,
            font=font_small,
        )

    return image

LEGEND_ROW_HEIGHT = 56
LEGEND_SWATCH_SIZE = 40
LEGEND_PADDING = 20
LEGEND_BG_COLOR = (18, 18, 20)
LEGEND_ROW_BORDER_COLOR = (42, 42, 52)
LEGEND_TEXT_COLOR = (255, 255, 255)
LEGEND_ACCENT_COLOR = (0, 245, 212)


LEGEND_CHIP_SIZE = 14
LEGEND_CHIP_GAP = 4
LEGEND_MAX_CHIPS = 6


def render_legend_image(grouped_stats, width=680):
    """
    Рисует таблицу-легенду по нитям мулине DMC: символ / цвет нити DMC /
    маленькие превью исходных цветов схемы, объединённых в эту нить /
    номер и название DMC / суммарный процент покрытия.

    grouped_stats: список из group_by_dmc().
    """

    rows = len(grouped_stats)
    total_h = LEGEND_PADDING * 2 + rows * LEGEND_ROW_HEIGHT

    image = Image.new("RGB", (width, total_h), LEGEND_BG_COLOR)
    draw = ImageDraw.Draw(image)

    try:
        font_symbol = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        font_label = ImageFont.truetype("DejaVuSans-Bold.ttf", 15)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 13)
    except IOError:
        font_symbol = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_small = ImageFont.load_default()

    symbol_col_x = LEGEND_PADDING
    dmc_swatch_x = LEGEND_PADDING + 60
    chips_col_x = dmc_swatch_x + LEGEND_SWATCH_SIZE + 16
    text_col_x = chips_col_x + LEGEND_MAX_CHIPS * (LEGEND_CHIP_SIZE + LEGEND_CHIP_GAP) + 14

    for i, group in enumerate(grouped_stats):
        row_y0 = LEGEND_PADDING + i * LEGEND_ROW_HEIGHT
        row_y1 = row_y0 + LEGEND_ROW_HEIGHT

        if i > 0:
            draw.line(
                [(LEGEND_PADDING, row_y0), (width - LEGEND_PADDING, row_y0)],
                fill=LEGEND_ROW_BORDER_COLOR,
                width=1,
            )

        row_center_y = (row_y0 + row_y1) / 2

        symbol_text = str(group["symbol"])
        bbox = draw.textbbox((0, 0), symbol_text, font=font_symbol)
        text_h = bbox[3] - bbox[1]
        draw.text(
            (symbol_col_x, row_center_y - text_h / 2 - bbox[1]),
            symbol_text,
            fill=LEGEND_ACCENT_COLOR,
            font=font_symbol,
        )

        swatch_y0 = row_center_y - LEGEND_SWATCH_SIZE / 2
        swatch_y1 = row_center_y + LEGEND_SWATCH_SIZE / 2
        draw.rectangle(
            [dmc_swatch_x, swatch_y0, dmc_swatch_x + LEGEND_SWATCH_SIZE, swatch_y1],
            fill=group["dmc_rgb"],
            outline=(255, 255, 255, 60),
            width=1,
        )

        chips = group["source_colors"][:LEGEND_MAX_CHIPS]
        chip_y0 = row_center_y - LEGEND_CHIP_SIZE / 2
        chip_y1 = row_center_y + LEGEND_CHIP_SIZE / 2
        for j, source in enumerate(chips):
            chip_x0 = chips_col_x + j * (LEGEND_CHIP_SIZE + LEGEND_CHIP_GAP)
            chip_x1 = chip_x0 + LEGEND_CHIP_SIZE
            draw.rectangle(
                [chip_x0, chip_y0, chip_x1, chip_y1],
                fill=source["rgb"],
                outline=(255, 255, 255, 60),
                width=1,
            )

        title_line = f"DMC {group['dmc_code']} · {group['dmc_name']}"
        draw.text(
            (text_col_x, row_y0 + 10),
            title_line,
            fill=LEGEND_TEXT_COLOR,
            font=font_label,
        )
        draw.text(
            (text_col_x, row_y0 + 30),
            f"{group['percentage']:.1f}%",
            fill=(160, 160, 171),
            font=font_small,
        )

    return image


# =========================================================================
# Финальная визуализация "крестиками" цветами мулине DMC
# =========================================================================

# Цвет фона имитирует небелёную канву Aida
FABRIC_BG_COLOR = (247, 246, 242)
FABRIC_WEAVE_COLOR = (221, 219, 211)   # мелкие "дырочки" переплетения канвы

STITCH_SEAM_BLEND = 0.22        # затемнение тонкого шва между соседними стежками
STITCH_TOP_BLEND = 0.32         # осветление верхней грани "стежка-подушечки"
STITCH_LEFT_BLEND = 0.12        # лёгкое осветление левой грани
STITCH_RIGHT_BLEND = 0.16       # лёгкое затемнение правой грани
STITCH_BOTTOM_BLEND = 0.34      # затемнение нижней грани — создаёт объём нити


def _blend_color(rgb, target, factor):
    """Смешивает rgb с target в пропорции factor (0..1) — для светотени стежка."""
    return tuple(
        max(0, min(255, int(round(c + (t - c) * factor))))
        for c, t in zip(rgb, target)
    )


def _draw_fabric_texture(draw, grid_width, grid_height, cell_size_px):
    """Рисует лёгкую фактуру канвы — мелкие крестики переплетения в узлах сетки."""
    dot_half = max(1, int(round(cell_size_px * 0.07)))

    for gy in range(grid_height + 1):
        for gx in range(grid_width + 1):
            cx = gx * cell_size_px
            cy = gy * cell_size_px
            draw.line(
                [(cx - dot_half, cy), (cx + dot_half, cy)],
                fill=FABRIC_WEAVE_COLOR, width=1,
            )
            draw.line(
                [(cx, cy - dot_half), (cx, cy + dot_half)],
                fill=FABRIC_WEAVE_COLOR, width=1,
            )


def _draw_stitch(draw, x0, y0, x1, y1, rgb):
    """
    Рисует один "объёмный" крестик-подушечку: клетка заливается основным
    цветом мулине и делится по диагоналям на 4 треугольника со смещённой
    яркостью (светлее сверху-слева, темнее снизу-справа). Это имитирует
    характерный рельеф нити в реальной вышивке крестом.
    """
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0

    top = _blend_color(rgb, (255, 255, 255), STITCH_TOP_BLEND)
    left = _blend_color(rgb, (255, 255, 255), STITCH_LEFT_BLEND)
    right = _blend_color(rgb, (0, 0, 0), STITCH_RIGHT_BLEND)
    bottom = _blend_color(rgb, (0, 0, 0), STITCH_BOTTOM_BLEND)

    draw.polygon([(x0, y0), (x1, y0), (cx, cy)], fill=top)
    draw.polygon([(x0, y0), (x0, y1), (cx, cy)], fill=left)
    draw.polygon([(x1, y0), (x1, y1), (cx, cy)], fill=right)
    draw.polygon([(x0, y1), (x1, y1), (cx, cy)], fill=bottom)

    # тонкий шов по краю клетки — отделяет соседние стежки друг от друга
    seam = _blend_color(rgb, (0, 0, 0), STITCH_SEAM_BLEND)
    draw.rectangle([x0, y0, x1, y1], outline=seam, width=1)


def render_dmc_cross_stitch(
    processed_image,
    palette_stats,
    cell_size_px=DEFAULT_CELL_SIZE_PX,
):
    """
    Рисует финальную визуализацию готовой работы: объёмные крестики-подушечки
    нитками мулине DMC на фоне канвы с лёгкой фактурой переплетения — без
    разметочной сетки и блоков.

    processed_image: PIL.Image — маленькая обработанная схема (1px = 1 клетка)
    palette_stats: список из get_palette_stats() + assign_symbols() +
                   match_dmc_colors() — у каждого цвета должно быть поле "dmc_rgb"
    """

    grid_width, grid_height = processed_image.size
    output_width = grid_width * cell_size_px
    output_height = grid_height * cell_size_px

    canvas = Image.new("RGB", (output_width, output_height), FABRIC_BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    _draw_fabric_texture(draw, grid_width, grid_height, cell_size_px)

    # Сопоставляем исходный цвет клетки схемы -> цвет мулине DMC
    rgb_to_dmc_rgb = {tuple(c["rgb"]): tuple(c["dmc_rgb"]) for c in palette_stats}

    pixels = processed_image.convert("RGB").load()

    for gy in range(grid_height):
        for gx in range(grid_width):
            cell_rgb = pixels[gx, gy]
            dmc_rgb = rgb_to_dmc_rgb.get(cell_rgb, cell_rgb)

            x0 = gx * cell_size_px
            y0 = gy * cell_size_px
            x1 = (gx + 1) * cell_size_px
            y1 = (gy + 1) * cell_size_px

            _draw_stitch(draw, x0, y0, x1, y1, dmc_rgb)

    return canvas