from PIL import Image, ImageDraw, ImageFont

# Цвета взяты из дизайн-концепции (ui/theme.py)
GRID_LINE_COLOR = (42, 42, 52)     # тонкая сетка между клетками
MAJOR_LINE_COLOR = (0, 245, 212)   # Mint Glow — выделение блоков 10x10

GRID_LINE_WIDTH = 1
MAJOR_LINE_WIDTH = 2

DEFAULT_CELL_SIZE_PX = 24
DEFAULT_MAJOR_STEP = 10


def render_scheme_with_grid(
    processed_image,
    cell_size_px=DEFAULT_CELL_SIZE_PX,
    major_step=DEFAULT_MAJOR_STEP,
):
    """
    Превращает "маленькую" обработанную схему (1 пиксель = 1 клетка)
    в увеличенное изображение с наложенной сеткой.

    processed_image: PIL.Image, размер = grid_width x grid_height
    cell_size_px: размер одной клетки в итоговом изображении (в пикселях)
    major_step: через сколько клеток рисовать жирную линию (блоки 10x10)
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

    return scheme_image

    from PIL import ImageFont


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