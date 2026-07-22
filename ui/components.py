import streamlit as st


# =========================
# HEADER
# =========================

def render_header():

    st.markdown(
        """
        <div class="pixel-logo">
            PIXEL STITCH STUDIO
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="pixel-version">
            SYSTEM ONLINE // MVP v0.1
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# STATUS INDICATOR
# =========================

def render_status(status):
    """
    status:
      - "ready"    -> простая строка "SYSTEM READY"
      - "uploaded" -> карточка с прогресс-баром и этапами обработки
      - "done"     -> простая строка "PROCESS COMPLETE"
    """

    if status == "uploaded":
        st.markdown(
            """
            <div class="processing-card">
                <div class="processing-title">
                    ОБРАБОТКА ИЗОБРАЖЕНИЯ<span class="dots"><span>.</span><span>.</span><span>.</span></span>
                </div>
                <div class="step-list">
                    <div class="step-item">
                        <span class="step-icon">◆</span>
                        <span>СКАНИРОВАНИЕ СЕТКИ</span>
                    </div>
                    <div class="step-item">
                        <span class="step-icon">◆</span>
                        <span>ОПТИМИЗАЦИЯ ПАЛИТРЫ</span>
                    </div>
                    <div class="step-item">
                        <span class="step-icon">◆</span>
                        <span>ПОСТРОЕНИЕ СХЕМЫ</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    statuses = {
        "ready": "SYSTEM READY",
        "done": "PROCESS COMPLETE",
    }

    text = statuses.get(status, "SYSTEM UNKNOWN")

    st.markdown(
        f"""
        <div class="status-line">
            <span class="status-dot"></span>
            <span class="status-text">
                {text}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# UPLOAD PANEL
# =========================

def render_upload_panel(key):

    uploaded_file = st.file_uploader(
        " ",
        label_visibility="hidden",
        key=key,
    )

    return uploaded_file


def render_file_bar(filename):

    st.markdown(
        f"""
        <div class="file-bar">
            <span class="file-bar-icon">🖼</span>
            <span class="file-bar-name">{filename}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    reset_clicked = st.button(
        "✕ Сбросить файл",
        key="reset_file_btn",
        help="Сбросить файл",
    )

    return reset_clicked


# =========================
# STATS PANEL (Размер схемы)
# =========================

def render_stats_panel(color_count, cell_size, grid_width, grid_height):

    stats = [
        {
            "icon": "🎨",
            "label": "ЦВЕТА",
            "value": f"{color_count}",
            "unit": "",
        },
        {
            "icon": "▦",
            "label": "КЛЕТКА",
            "value": f"{cell_size:.2f}",
            "unit": "px",
        },
        {
            "icon": "↔",
            "label": "ШИРИНА",
            "value": f"{grid_width}",
            "unit": "клеток",
        },
        {
            "icon": "↕",
            "label": "ВЫСОТА",
            "value": f"{grid_height}",
            "unit": "клеток",
        },
    ]

    cards_html = "".join(
        f"""
        <div class="stat-card">
            <div class="stat-icon">{item['icon']}</div>
            <div class="stat-label">{item['label']}</div>
            <div class="stat-value">{item['value']}<span class="stat-unit">{item['unit']}</span></div>
        </div>
        """
        for item in stats
    )

    st.markdown(
        f"""
        <div class="stats-grid">
            {cards_html}
        </div>
        """,
        unsafe_allow_html=True
    )