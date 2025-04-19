import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from backend.services.auth_service import (
    hash_password, check_password,
    create_users_table, insert_user,
    get_user_by_username
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
                if user and check_password(password, user["password"]):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["user_id"] = user["user_id"]
                    st.session_state["name"] = user["name"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Sign Up Page ---
def signup_page():
    st.title("SkillPath - Career Transition Platform")
    st.header("Sign Up")

    create_users_table()  # Ensure the users table exists

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
                    st.success("Sign-up successful! Please log in.")
                    st.session_state["auth_page"] = "Login"
                    st.session_state["user_id"] = user_id
                    st.session_state["name"] = new_name
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
