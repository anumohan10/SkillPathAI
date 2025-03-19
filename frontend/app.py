import streamlit as st

# --- Sample Hardcoded Credentials for Demonstration ---
USER_CREDENTIALS = {
    "alice": "password123",
    "bob": "securepwd"
}

# --- Authentication Function ---
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Login successful!")
            st.experimental_rerun()  # Refresh to load the main app
        else:
            st.error("Invalid username or password.")

# --- Main Application Pages ---
def dashboard():
    st.header("Dashboard")
    st.write(f"Welcome, {st.session_state.get('username', 'Guest')}!")
    st.write("Here you can see an overview of your progress and statistics.")

def profile():
    st.header("Profile")
    st.write("Manage your profile and preferences here.")
    st.write(f"Username: {st.session_state.get('username', 'N/A')}")
    # Additional profile settings can be added here.

def courses():
    st.header("Courses")
    st.write("Search and explore courses available on the platform.")
    search_query = st.text_input("Search for courses:")
    if st.button("Search"):
        st.write(f"Results for '{search_query}' will be displayed here.")
        # Add API calls or database queries to list courses.

def learning_path():
    st.header("Learning Path")
    st.write("Generate your personalized learning path based on your skills and goals.")
    st.write("Configure your preferences below:")
    study_hours = st.slider("Preferred study hours per week:", 1, 40, 10)
    if st.button("Generate Learning Path"):
        st.write("Generating learning path...")
        # Integrate with your backend services or LLM recommendations here.
        st.success("Your personalized learning path is ready!")

# --- Main Application Layout with Navigation ---
def main_app():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", ["Dashboard", "Profile", "Courses", "Learning Path"])

    if selection == "Dashboard":
        dashboard()
    elif selection == "Profile":
        profile()
    elif selection == "Courses":
        courses()
    elif selection == "Learning Path":
        learning_path()

    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.experimental_rerun()

# --- Main Function ---
def main():
    # Initialize session state for authentication if not already set
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        main_app()
    else:
        login()

if __name__ == '__main__':
    main()
