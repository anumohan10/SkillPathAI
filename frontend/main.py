# main.py
import streamlit as st
from auth import login_page, signup_page
from dashboard import main_app

# Load custom CSS from styles.css
with open("frontend/styles.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

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
    main()