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
    reduce_palette_colors,
    get_palette_stats,
    assign_symbols,
)
from core.dmc_matcher import match_dmc_colors, group_by_dmc

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

            # Тяжёлую часть (поиск сетки + первичную оптимизацию палитры)
            # считаем только один раз для каждого загруженного файла и
            # сохраняем в session_state, чтобы движение слайдера ниже
            # не запускало этот расчёт заново.
            file_signature = (uploaded_file.name, uploaded_file.size)

            if st.session_state.get("base_signature") != file_signature:

                gray_image = image.convert("L")

                cell_size, grid_width, grid_height = detect_grid_size(gray_image)

                base_processed_image, base_color_count, mean_error, max_error, elbow_k, initial_mean, initial_max, initial_colors = optimize_palette(
                    image,
                    grid_width,
                    grid_height,
                )

                st.session_state.base_signature = file_signature
                st.session_state.base_processed_image = base_processed_image
                st.session_state.base_color_count = base_color_count
                st.session_state.cell_size = cell_size
                st.session_state.grid_width = grid_width
                st.session_state.grid_height = grid_height

            base_processed_image = st.session_state.base_processed_image
            base_color_count = st.session_state.base_color_count
            cell_size = st.session_state.cell_size
            grid_width = st.session_state.grid_width
            grid_height = st.session_state.grid_height

            with status_placeholder:
                render_status("done")

            st.subheader("Количество цветов схемы")

            target_color_count = st.slider(
                "Количество цветов в схеме",
                min_value=2,
                max_value=base_color_count,
                value=base_color_count,
                step=1,
                help="Похожие цвета будут автоматически объединены в один.",
            )

            if target_color_count < base_color_count:
                processed_image = reduce_palette_colors(base_processed_image, target_color_count)
            else:
                processed_image = base_processed_image

            palette_stats = get_palette_stats(processed_image)
            palette_stats = assign_symbols(palette_stats)
            palette_stats = match_dmc_colors(palette_stats)

            # Группируем цвета схемы по итоговой нити мулине DMC — легенда
            # и символы на схеме теперь опираются на цвет нити, а не на
            # исходный HEX. Исходные цвета остаются доступны внутри группы
            # (поле source_colors) — их можно показать рядом / по наведению.
            grouped_stats = group_by_dmc(palette_stats)

            color_count = len(palette_stats)

            symbol_lookup_stats = [
                {"rgb": source["rgb"], "symbol": group["symbol"]}
                for group in grouped_stats
                for source in group["source_colors"]
            ]

            st.subheader("Результат")

            palette_image = render_palette_image(palette_stats)
            legend_image = render_legend_image(grouped_stats)
            dmc_cross_stitch_image = render_dmc_cross_stitch(processed_image, palette_stats)

            view_mode = st.radio(
                "Показать",
                options=["Схема", "Готовая работа"],
                horizontal=True,
                label_visibility="collapsed",
            )

            if view_mode == "Схема":
                show_symbols = st.toggle(
                    "Показывать символы на схеме",
                    value=False,
                )
            else:
                show_symbols = False

            scheme_with_grid = render_scheme_with_grid(
                processed_image,
                show_symbols=show_symbols,
                palette_stats=symbol_lookup_stats,
            )

            compare_col1, compare_col2 = st.columns(2)

            with compare_col1:
                st.caption("ОРИГИНАЛ")
                st.image(image, use_container_width=True)

            with compare_col2:
                if view_mode == "Схема":
                    st.caption("СХЕМА ДЛЯ ВЫШИВКИ")
                    st.image(scheme_with_grid, use_container_width=True)
                else:
                    st.caption("ГОТОВАЯ РАБОТА")
                    st.image(dmc_cross_stitch_image, use_container_width=True)
            
            scheme_png_bytes = image_to_png_bytes(scheme_with_grid)
            palette_png_bytes = image_to_png_bytes(palette_image)
            dmc_cross_stitch_png_bytes = image_to_png_bytes(dmc_cross_stitch_image)
            pdf_bytes = build_pdf_report(scheme_with_grid, palette_image, legend_image)


            st.download_button(
                label="⬇ СКАЧАТЬ ВСЁ ОДНИМ PDF",
                data=pdf_bytes,
                file_name="pixel_stitch_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )

            
            st.divider()


            st.subheader("Легенда схемы")
            st.caption(
                "Легенда сгруппирована по нитям мулине DMC. Наведите курсор "
                "на маленькие квадраты в колонке «Исходные цвета» — во "
                "всплывающей подсказке будет виден их HEX-код."
            )

            legend_col1, legend_col2, legend_col3, legend_col4 = st.columns([1, 1, 2, 3])
            with legend_col1:
                st.markdown("**№**")
            with legend_col2:
                st.markdown("**Цвет DMC**")
            with legend_col3:
                st.markdown("**Исходные цвета**")
            with legend_col4:
                st.markdown("**Мулине DMC / покрытие**")

            for group in grouped_stats:
                row_col1, row_col2, row_col3, row_col4 = st.columns([1, 1, 2, 3])

                with row_col1:
                    st.markdown(f"**{group['symbol']}**")

                with row_col2:
                    st.markdown(
                        f"""
                        <div class="palette-color"
                            style="height:32px; margin-bottom:0;
                                   background:{group['dmc_hex']};">
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with row_col3:
                    chip_style = (
                        "display:inline-block;width:18px;height:18px;"
                        "margin-right:4px;border-radius:3px;"
                        "border:1px solid rgba(255,255,255,0.25);"
                    )
                    chips_html = "".join(
                        f'<span title="Исходный цвет схемы: {source["hex"].upper()} '
                        f'({source["percentage"]:.1f}%)" '
                        f'style="{chip_style}background:{source["hex"]};"></span>'
                        for source in group["source_colors"]
                    )
                    st.markdown(
                        f'<div style="line-height:32px;">{chips_html}</div>',
                        unsafe_allow_html=True,
                    )

                with row_col4:
                    st.markdown(
                        f"**DMC {group['dmc_code']}** · {group['dmc_name']} · "
                        f"{group['percentage']:.1f}%"
                    )



            st.subheader("Размер схемы")

            render_stats_panel(
                color_count=color_count,
                cell_size=cell_size,
                grid_width=grid_width,
                grid_height=grid_height,
            )

            
        except UnidentifiedImageError:

            st.error(
                "Не удалось открыть изображение."
            )

        except Exception as e:

            st.error(str(e))