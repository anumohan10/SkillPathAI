# main.py
import streamlit as st
import logging
import sys

# Set up minimal logging
logging.basicConfig(
    level=logging.WARNING,  # Only log warnings and errors
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app_errors.log")]
)

logger = logging.getLogger("SkillPathAI")

# Set page to wide mode - must be the first Streamlit command
st.set_page_config(
    page_title="SkillPathAI",
    layout="wide",  # This sets wide mode
    initial_sidebar_state="expanded"
)

from auth import login_page, signup_page
from dashboard import main_app

# Load custom CSS from styles.css
try:
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except Exception as e:
    logger.error("Failed to load CSS: %s", str(e))

def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        main_app()
    else:
        # Navigation for unauthenticated users
        if "auth_page" not in st.session_state:
            st.session_state["auth_page"] = "Login"  # Default to Login page

        # Sidebar navigation for Login/Sign Up, wrapped in a styled container
        with st.sidebar:
            st.markdown('<div class="container-card">', unsafe_allow_html=True)
            st.title("Welcome")
            auth_selection = st.radio("Choose an action", ["Login", "Sign Up"], index=0 if st.session_state["auth_page"] == "Login" else 1)
            st.markdown('</div>', unsafe_allow_html=True)

        # Update the session state based on selection
        st.session_state["auth_page"] = auth_selection

        # Show the appropriate page
        if auth_selection == "Login":
            login_page()
        else:
            signup_page()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical("Application crashed: %s", str(e), exc_info=True)