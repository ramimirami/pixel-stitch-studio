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
# UPLOAD PANEL
# =========================

def render_upload_panel():

    uploaded_file = st.file_uploader(
        " ",
        label_visibility="hidden"
    )

    return uploaded_file