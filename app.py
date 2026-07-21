import streamlit as st
from PIL import Image, UnidentifiedImageError

from ui.components import render_header, render_upload_panel

from core.pixel_core import (
    detect_grid_size,
    optimize_palette,
    get_palette_stats,
)

st.set_page_config(
    page_title="Pixel Stitch Studio",
    page_icon="🧵",
    layout="wide"
)


def load_css():
    with open("assets/style.css", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


load_css()

render_header()

uploaded_file = render_upload_panel()


MAX_FILE_SIZE_MB = 10


if uploaded_file is not None:

    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(
            f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE_MB} MB"
        )

    else:

        try:

            image = Image.open(uploaded_file)

            image.verify()

            uploaded_file.seek(0)

            image = Image.open(uploaded_file)

            gray_image = image.convert("L")

            cell_size, grid_width, grid_height = detect_grid_size(gray_image)
            
            processed_image, color_count, mean_error, max_error, elbow_k, initial_mean, initial_max, initial_colors = optimize_palette(
                image,
                grid_width,
                grid_height,
            )

            st.success("Изображение успешно загружено")

            st.subheader("Исходное изображение")

            st.image(
                image,
                use_container_width=True
            )

            st.subheader("Обработанная схема")

            st.image(
                processed_image,
                use_container_width=True
)
            
            st.subheader("Размер схемы")
            st.write(f"Количество цветов: {color_count}")

            st.write(f"Размер клетки: {cell_size:.2f}px")
            st.write(f"Ширина: {grid_width}")
            st.write(f"Высота: {grid_height}")

        except UnidentifiedImageError:

            st.error(
                "Не удалось открыть изображение."
            )

        except Exception as e:

            st.error(str(e))