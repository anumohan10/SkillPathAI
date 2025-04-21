import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from backend.services.auth_service import (
    hash_password, check_password,
    create_users_table, insert_user,
    get_user_by_username, update_user_password
)

# Load custom CSS from styles.css
with open("styles.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- Login Page ---
def login_page():
    st.title("SkillPath - Career Transition Platform")
    st.header("Login")

    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                user = get_user_by_username(username)
                if user:
                    if check_password(password, user["password"]):
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["user_id"] = user["user_id"]
                        st.session_state["name"] = user["name"]
                        st.success("Login successful! Redirecting to dashboard...")
                        st.rerun()
                    else:
                        st.error("Incorrect password. Please try again.")
                else:
                    st.error("Account does not exist. Please sign up first.")
        st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Forgot Password?"):
        st.session_state["auth_page"] = "Forgot Password"
        st.rerun()
        
# -- Forget Password --
def forgot_password_page():
    st.title("Reset Your Password")

    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        st.subheader("Forgot Password")

        with st.form("reset_form"):
            username = st.text_input("Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            submit = st.form_submit_button("Reset Password")

            if submit:
                user = get_user_by_username(username)
                if not user:
                    st.error("No account found with this username.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    hashed_pw = hash_password(new_password)
                    if update_user_password(username, hashed_pw):
                        st.success("Password updated successfully! Please log in.")
                        st.session_state["auth_page"] = "Login"
                        st.rerun()
                    else:
                        st.error("Failed to update password. Please try again.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Sign Up Page ---
def signup_page():
    st.title("SkillPath - Career Transition Platform")
    st.header("Sign Up")

    # create_users_table()  # Ensure the users table exists

    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        with st.form("signup_form"):
            new_name = st.text_input("Full Name", key="signup_name")
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
            signup_submit = st.form_submit_button("Sign Up")

            if signup_submit:
                if not new_name or not new_username or not new_email or not new_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif get_user_by_username(new_username):
                    st.error("Username already exists.")
                else:
                    hashed_password = hash_password(new_password)
                    user_id = insert_user(new_name, new_username, new_email, hashed_password)
                    st.success("Account created successfully! Please select 'Login' from the sidebar to log in.")
                    # No redirect; user stays on signup page
        st.markdown('</div>', unsafe_allow_html=True)