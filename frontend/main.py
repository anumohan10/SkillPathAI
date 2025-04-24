import streamlit as st

# Set page to wide mode - must be the first Streamlit command
st.set_page_config(
    page_title="SkillPathAI", # This sets wide mode
    initial_sidebar_state="expanded"
)


import logging
import sys

# Set up minimal logging
logging.basicConfig(
    level=logging.WARNING,  # Only log warnings and errors
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("logs/app_errors.log"), logging.StreamHandler()]
)

logger = logging.getLogger("SkillPathAI")


from auth import login_page, signup_page, forgot_password_page
from dashboard import main_app
import time
import os

# Load custom CSS from styles.css
try:
    with open("styles.css", "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except Exception as e:
    logger.error("Failed to load CSS: %s", str(e))

def main():
    # Initialize session state variables
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "Login"  # Default to Login page
    if "splash_shown" not in st.session_state:
        st.session_state["splash_shown"] = False

    # Show splash screen if not yet shown
    if not st.session_state["splash_shown"]:
        image_path = os.path.join("assets", "splash_logo.png")
        # Center the content using columns
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Display the logo image using use_container_width
            st.image(image_path, use_container_width=True)
            st.markdown("<h3 style='text-align: center;'>Career Transition Platform</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Loading...</p>", unsafe_allow_html=True)

        # Simulate loading delay (increased to 5 seconds)
        time.sleep(4)

        # Mark splash screen as shown and rerun to transition to login page
        st.session_state["splash_shown"] = True
        st.rerun()

    # After splash screen, proceed with authentication flow
    if st.session_state["authenticated"]:
        main_app()
    else:
        # Sidebar navigation for unauthenticated users
        with st.sidebar:
            st.markdown('<div class="container-card">', unsafe_allow_html=True)
            st.title("Welcome")
            index = 0 if st.session_state["auth_page"] == "Login" else (1 if st.session_state["auth_page"] == "Sign Up" else 2)
            auth_selection = st.radio("Choose an action", ["Login", "Sign Up", "Forgot Password"], index=index)
            st.markdown('</div>', unsafe_allow_html=True)

        # Update the session state based on selection
        st.session_state["auth_page"] = auth_selection

        # Show the appropriate page
        if auth_selection == "Login":
            login_page()
        elif auth_selection == "Sign Up":
            signup_page()
        elif auth_selection == "Forgot Password":
            forgot_password_page()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical("Application crashed: %s", str(e), exc_info=True)