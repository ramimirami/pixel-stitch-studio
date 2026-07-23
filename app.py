import streamlit as st
from PIL import Image, UnidentifiedImageError

from ui.components import (
    render_header,
    render_upload_panel,
    render_file_bar,
    render_stats_panel,
    render_status,
)

from core.pixel_core import (
    detect_grid_size,
    optimize_palette,
    get_palette_stats,
    assign_symbols,
)
from core.dmc_matcher import match_dmc_colors

from services.renderer import (
    render_scheme_with_grid,
    render_palette_image,
    render_legend_image,
    render_dmc_cross_stitch,
)
from services.exporter import image_to_png_bytes, build_pdf_report

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

if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0

if "current_file" not in st.session_state:
    st.session_state.current_file = None

if st.session_state.current_file is None:
    new_file = render_upload_panel(key=f"file_uploader_{st.session_state.uploader_version}")
    if new_file is not None:
        st.session_state.current_file = new_file
        st.rerun()
else:
    reset_clicked = render_file_bar(st.session_state.current_file.name)
    if reset_clicked:
        st.session_state.current_file = None
        st.session_state.uploader_version += 1
        st.rerun()

uploaded_file = st.session_state.current_file

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

            image = image.convert("RGB")
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
            palette_stats = assign_symbols(palette_stats)
            palette_stats = match_dmc_colors(palette_stats)

            st.subheader("Обработанная схема")

            show_symbols = st.toggle(
                "Показывать символы на схеме",
                value=False,
            )

            scheme_with_grid = render_scheme_with_grid(
                processed_image,
                show_symbols=show_symbols,
                palette_stats=palette_stats,
            )

            st.image(
                scheme_with_grid,
                use_container_width=True
            )

            palette_image = render_palette_image(palette_stats)
            legend_image = render_legend_image(palette_stats)
            dmc_cross_stitch_image = render_dmc_cross_stitch(processed_image, palette_stats)

            scheme_png_bytes = image_to_png_bytes(scheme_with_grid)
            palette_png_bytes = image_to_png_bytes(palette_image)
            dmc_cross_stitch_png_bytes = image_to_png_bytes(dmc_cross_stitch_image)
            pdf_bytes = build_pdf_report(scheme_with_grid, palette_image, legend_image)

            download_col1, download_col2 = st.columns(2)

            with download_col1:
                st.download_button(
                    label="⬇ СХЕМА (PNG)",
                    data=scheme_png_bytes,
                    file_name="pixel_stitch_scheme.png",
                    mime="image/png",
                    use_container_width=True,
                )

            with download_col2:
                st.download_button(
                    label="⬇ ПАЛИТРА (PNG)",
                    data=palette_png_bytes,
                    file_name="pixel_stitch_palette.png",
                    mime="image/png",
                    use_container_width=True,
                )

            st.download_button(
                label="⬇ СКАЧАТЬ ВСЁ ОДНИМ PDF",
                data=pdf_bytes,
                file_name="pixel_stitch_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
            
            st.subheader("Размер схемы")

            render_stats_panel(
                color_count=color_count,
                cell_size=cell_size,
                grid_width=grid_width,
                grid_height=grid_height,
            )

            st.divider()

            st.subheader("Готовая работа мулине DMC")
            st.caption(
                "Так будет выглядеть готовая вышивка: крестики вместо пикселей, "
                "цвета — ближайшие мулине DMC."
            )

            st.image(
                dmc_cross_stitch_image,
                use_container_width=True
            )

            st.download_button(
                label="⬇ СХЕМА КРЕСТИКАМИ DMC (PNG)",
                data=dmc_cross_stitch_png_bytes,
                file_name="pixel_stitch_dmc_cross_stitch.png",
                mime="image/png",
                use_container_width=True,
            )

            
            st.divider()

            st.subheader("Легенда схемы")
            st.caption("Номер мулине DMC подобран автоматически по ближайшему цвету.")

            legend_col1, legend_col2, legend_col3, legend_col4 = st.columns([1, 1, 1, 3])
            with legend_col1:
                st.markdown("**№**")
            with legend_col2:
                st.markdown("**Цвет схемы**")
            with legend_col3:
                st.markdown("**Цвет DMC**")
            with legend_col4:
                st.markdown("**Мулине DMC / покрытие**")

            for color in palette_stats:
                row_col1, row_col2, row_col3, row_col4 = st.columns([1, 1, 1, 3])

                with row_col1:
                    st.markdown(f"**{color['symbol']}**")

                with row_col2:
                    st.markdown(
                        f"""
                        <div class="palette-color"
                            style="height:32px; margin-bottom:0;
                                   background:{color['hex']};">
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with row_col3:
                    st.markdown(
                        f"""
                        <div class="palette-color"
                            style="height:32px; margin-bottom:0;
                                   background:{color['dmc_hex']};">
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with row_col4:
                    st.markdown(
                        f"**DMC {color['dmc_code']}** · {color['dmc_name']} · "
                        f"{color['percentage']:.1f}%"
                    )
            
        except UnidentifiedImageError:

            st.error(
                "Не удалось открыть изображение."
            )

        except Exception as e:

            st.error(str(e))