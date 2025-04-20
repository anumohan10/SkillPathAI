import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import requests
import json

# Define API URL - should be configurable in production
API_URL = "http://localhost:8000"

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
                try:
                    # Call the API instead of direct function call
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
                            st.success("Sign-up successful! Please log in.")
                            st.session_state["auth_page"] = "Login"
                            st.rerun()
                        elif response.status_code == 400:
                            error_data = response.json()
                            st.error(error_data.get("detail", "Username already exists."))
                        else:
                            st.error("An error occurred during sign up.")
                    except Exception as e:
                        st.error(f"Error connecting to the API: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
