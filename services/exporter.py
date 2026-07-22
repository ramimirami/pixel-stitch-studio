import io


def image_to_png_bytes(image):
    """
    Конвертирует PIL.Image в байты PNG для скачивания через Streamlit.

    image: PIL.Image — готовое изображение (например, схема с сеткой)
    """

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()


from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def build_pdf_report(scheme_image, palette_image, title="Pixel Stitch Studio"):
    """
    Собирает PDF из двух страниц: схема с сеткой и палитра.

    scheme_image: PIL.Image — схема с наложенной сеткой
    palette_image: PIL.Image — изображение палитры
    """

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    margin = 15 * mm
    heading_space = 20 * mm

    def draw_page(image, heading):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, page_height - margin, heading)

        img_w, img_h = image.size
        max_w = page_width - 2 * margin
        max_h = page_height - 2 * margin - heading_space
        scale = min(max_w / img_w, max_h / img_h, 1.0)

        draw_w = img_w * scale
        draw_h = img_h * scale
        x = (page_width - draw_w) / 2
        y = page_height - margin - heading_space - draw_h

        c.drawImage(ImageReader(image), x, y, width=draw_w, height=draw_h)
        c.showPage()

    draw_page(scheme_image, f"{title} — Схема")
    draw_page(palette_image, f"{title} — Палитра")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()