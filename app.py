import streamlit as st
from PIL import Image, UnidentifiedImageError

from ui.components import (
    render_header,
    render_upload_panel,
    render_stats_panel,
    render_status,
)

from core.pixel_core import (
    detect_grid_size,
    optimize_palette,
    get_palette_stats,
)

from services.renderer import render_scheme_with_grid

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

status_placeholder = st.empty()

if uploaded_file is None:
    with status_placeholder:
        render_status("ready")

else:
    with status_placeholder:
        render_status("uploaded")

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

            with status_placeholder:
                render_status("done")

            palette_stats = get_palette_stats(processed_image)

            st.subheader("Обработанная схема")

            scheme_with_grid = render_scheme_with_grid(processed_image)

            st.image(
                scheme_with_grid,
                use_container_width=True
            )
            
            st.subheader("Размер схемы")

            render_stats_panel(
                color_count=color_count,
                cell_size=cell_size,
                grid_width=grid_width,
                grid_height=grid_height,
            )

            st.divider()

            st.subheader("Палитра")
            for row_start in range(0, len(palette_stats), 4):

                columns = st.columns(4)

                for column, color in zip(columns, palette_stats[row_start:row_start + 4]):

                    with column:

                        st.markdown(
                            f"""
                            <div class="palette-color"
                                style="background:{color['hex']};">
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"**{color['hex'].upper()}** · {color['percentage']:.1f}%"
                        )
            
        except UnidentifiedImageError:

            st.error(
                "Не удалось открыть изображение."
            )

        except Exception as e:

            st.error(str(e))