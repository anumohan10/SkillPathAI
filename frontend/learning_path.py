import streamlit as st
import importlib
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import auth functions
from auth import login_user, register_user

# Load custom CSS from styles.css
with open("styles.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "login"

def logout():
    """Log out the user and reset session state"""
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["current_page"] = "login"
    st.rerun()

def show_login():
    """Display the login page"""
    st.header("Login")
    
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if login_user(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["current_page"] = "dashboard"
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("Don't have an account?")
    if st.button("Sign Up"):
        st.session_state["current_page"] = "signup"
        st.rerun()

def show_signup():
    """Display the signup page"""
    st.header("Sign Up")
    
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        with st.form("signup_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if password != confirm_password:
                    st.error("Passwords don't match")
                elif register_user(username, email, password):
                    st.success("Account created successfully! Please login.")
                    st.session_state["current_page"] = "login"
                    st.rerun()
                else:
                    st.error("Username already exists")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("Already have an account?")
    if st.button("Login"):
        st.session_state["current_page"] = "login"
        st.rerun()

def main():
    """Main application logic with dynamic page loading"""
    # Check if user is authenticated
    if st.session_state["authenticated"]:
        # Create navigation sidebar only for authenticated users
        with st.sidebar:
            st.title("Navigation")
            available_pages = [
                "Dashboard", 
                "Profile", 
                "Courses", 
                "Learning Path", 
                "Career Transition"
            ]
            
            selected_page = st.sidebar.selectbox(
                "Go to", 
                available_pages,
                index=available_pages.index(st.session_state["current_page"].capitalize()) 
                      if st.session_state["current_page"].capitalize() in available_pages 
                      else 0
            )
            
            st.session_state["current_page"] = selected_page.lower().replace(" ", "_")
            
            if st.button("Logout"):
                logout()
        
        # Dynamic page loading based on selection
        try:
            # Dynamically import the appropriate module
            page_name = st.session_state["current_page"]
            
            if page_name == "dashboard":
                # Load the main dashboard from the dashboard module
                from dashboard import dashboard
                dashboard()
            elif page_name == "profile":
                from dashboard import profile
                profile()
            elif page_name == "courses":
                from dashboard import courses
                courses()
            elif page_name == "learning_path":
                # Use the specialized learning path module
                from frontend.learning_path import learning_path_chat
                learning_path_chat()
            elif page_name == "career_transition":
                from frontend.pages.career_transition import career_transition_page
                career_transition_page()
            else:
                # Default to dashboard if page not found
                from dashboard import dashboard
                dashboard()
                
        except Exception as e:
            st.error(f"Error loading page: {e}")
            st.error("Please try again or contact support if the issue persists.")
            if st.button("Return to Dashboard"):
                st.session_state["current_page"] = "dashboard"
                st.rerun()
    else:
        # Show login/signup for unauthenticated users
        if st.session_state["current_page"] == "login":
            show_login()
        elif st.session_state["current_page"] == "signup":
            show_signup()
        else:
            # Default to login if any other page is attempted without authentication
            st.session_state["current_page"] = "login"
            st.rerun()

if __name__ == "__main__":
    main()