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