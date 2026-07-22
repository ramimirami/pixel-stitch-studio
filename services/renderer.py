from PIL import Image, ImageDraw

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