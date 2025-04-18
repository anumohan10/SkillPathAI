# auth.py
import streamlit as st
import json
import bcrypt
import os.path

# Load custom CSS from styles.css
with open("styles.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- File-based Storage Setup ---
USER_FILE = "users.json"

def init_user_storage():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f)

def load_users():
    init_user_storage()
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

# --- Authentication Functions ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- Login Page ---
def login_page():
    st.title("SkillPath - Career Transition Platform")
    st.header("Login")

    # Wrap the form in a styled container using st.markdown
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                users = load_users()
                if username in users and check_password(password, users[username]["password"]):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Try Demo Mode"):
        st.session_state["authenticated"] = True
        st.session_state["username"] = "demo"
        st.rerun()

# --- Sign Up Page ---
def signup_page():
    st.title("SkillPath - Career Transition Platform")
    st.header("Sign Up")

    # Wrap the form in a styled container using st.markdown
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        with st.form("signup_form"):
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
            signup_submit = st.form_submit_button("Sign Up")

            if signup_submit:
                if not new_username or not new_email or not new_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    users = load_users()
                    if new_username in users:
                        st.error("Username already exists.")
                    elif any(user["email"] == new_email for user in users.values()):
                        st.error("Email already exists.")
                    else:
                        hashed_password = hash_password(new_password)
                        users[new_username] = {
                            "email": new_email,
                            "password": hashed_password
                        }
                        save_users(users)
                        st.success("Sign-up successful! Please log in.")
                        st.session_state["auth_page"] = "Login"
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)