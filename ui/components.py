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

    statuses = {
        "ready": "SYSTEM READY",
        "uploaded": "IMAGE LOADED - PROCESSING",
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

def render_upload_panel():

    uploaded_file = st.file_uploader(
        " ",
        label_visibility="hidden"
    )

    return uploaded_file


# =========================
# STATS PANEL (Размер схемы)
# =========================

def render_stats_panel(color_count, cell_size, grid_width, grid_height):
    """
    Отображает карточки со сводной статистикой обработанной схемы:
    количество цветов, размер клетки, ширина и высота сетки.
    """

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