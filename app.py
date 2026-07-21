import streamlit as st
from PIL import Image
from PIL import UnidentifiedImageError

from ui.components import render_header, render_upload_panel


# =========================
# PAGE SETTINGS
# =========================

st.set_page_config(
    page_title="Pixel Stitch Studio",
    page_icon="🧵",
    layout="wide"
)


# =========================
# LOAD CSS
# =========================

def load_css():

    with open(
        "assets/style.css",
        "r",
        encoding="utf-8"
    ) as f:

        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


load_css()


# =========================
# UI
# =========================

render_header()


uploaded_file = render_upload_panel()


# =========================
# IMAGE PREVIEW
# =========================

if uploaded_file:

    try:

        image = Image.open(uploaded_file)

        st.subheader("IMAGE PREVIEW")

        st.image(
            image,
            use_container_width=True
        )


    except UnidentifiedImageError:

        st.error(
            "Cannot read image file"
        )