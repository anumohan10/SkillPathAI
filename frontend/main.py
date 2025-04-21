import streamlit as st
from auth import login_page, signup_page, forgot_password_page 
from dashboard import main_app

# Load custom CSS from styles.css
with open("styles.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def main():
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "Login"

    if st.session_state["authenticated"]:
        main_app()
    else:
        with st.sidebar:
            st.markdown('<div class="container-card">', unsafe_allow_html=True)
            st.title("Welcome")

            # Radio button for switching between Login, Sign Up, Forgot Password
            auth_selection = st.radio(
                "Choose an action",
                ["Login", "Sign Up", "Forgot Password"],
                index=["Login", "Sign Up", "Forgot Password"].index(st.session_state["auth_page"]),
                key=f"auth_radio_key_{st.session_state.get('auth_page', 'Login')}"
            )

            st.session_state["auth_page"] = auth_selection
            st.markdown('</div>', unsafe_allow_html=True)

        # Render the correct page based on selection
        if st.session_state["auth_page"] == "Login":
            login_page()
        elif st.session_state["auth_page"] == "Sign Up":
            signup_page()
        elif st.session_state["auth_page"] == "Forgot Password":
            forgot_password_page()

if __name__ == '__main__':
    main()
