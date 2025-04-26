import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import json
import os

# Define API URL - using environment variable or fallback to Docker service name
API_URL = os.environ.get("API_URL", "http://backend:8000")

# Load custom CSS from styles.css
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(css_path, "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- Login Page ---
def login_page():
    st.title("SkillPath - Career Transition Platform")
    st.header("Login")

    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)

        # Login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                try:
                    response = requests.post(
                        f"{API_URL}/auth/login",
                        json={"username": username, "password": password}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["user_id"] = data["user"]["user_id"]
                        st.session_state["name"] = data["user"]["name"]
                        st.session_state["token"] = data["access_token"]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except Exception as e:
                    st.error(f"Error connecting to the API: {str(e)}")

        # Add a horizontal line or spacer
        st.markdown("<br>", unsafe_allow_html=True)

        # Forgot Password button styled as a link
        if st.button("🔐 Forgot Password?"):
            st.session_state["auth_page"] = "Forgot Password"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# --- Sign Up Page ---
def signup_page():
    st.title("SkillPath - Career Transition Platform")
    st.header("Sign Up")

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
                else:
                    try:
                        # Call the API instead of direct function call
                        response = requests.post(
                            f"{API_URL}/auth/signup",
                            json={
                                "name": new_name,
                                "username": new_username,
                                "email": new_email,
                                "password": new_password
                            }
                        )
                        
                        if response.status_code == 201:
                            data = response.json()
                            st.success("Account created successfully! Please select 'Login' from the sidebar to log in.")
                        elif response.status_code == 400:
                            error_data = response.json()
                            st.error(error_data.get("detail", "Username already exists."))
                        else:
                            st.error("An error occurred during sign up.")
                    except Exception as e:
                        st.error(f"Error connecting to the API: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
# Forget Password 
def forgot_password_page():
    st.title("Forgot Password")

    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        with st.form("forgot_form"):
            username = st.text_input("Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Reset Password")

            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/auth/reset-password",
                            json={"username": username, "new_password": new_password}
                        )
                        if response.status_code == 200:
                            st.success("Password reset successfully! Please select 'Login' from the sidebar to log in.")
                            #st.session_state["auth_page"] = "Login"
                            #st.rerun()
                        else:
                            st.error(response.json().get("detail", "Failed to reset password"))
                    except Exception as e:
                        st.error(f"API error: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)