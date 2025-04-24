# dashboard.py
import sys
import os
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from backend.services.resume_parser import extract_text
# from backend.services.cortex_service import ResumeSearchService
# from backend.services.chat_service import ChatService
# from backend.services.skill_matcher import match_skills, extract_skills_from_text, get_job_requirements, generate_skill_recommendations
# from frontend.components.career_chat import CareerChat
# from backend.services.learning_path_service import get_learning_path
#from frontend.pages.learning_path import display_learning_path

# Import page rendering functions
# Import page rendering functions
from frontend.dashboard_page import render_dashboard_page
from frontend.profile_page import render_profile_page
# from frontend.courses_page import render_courses_page
from frontend.guidance_hub_page import render_guidance_hub_page
from frontend.learning_path_page import render_learning_path_page
from frontend.career_transition_page import render_career_transition_page

# Load custom CSS from styles.css
with open("styles.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- Main Application Layout ---
def main_app():
    """Sets up the sidebar navigation and displays the selected page."""

    # Initialize current_page in session state if it doesn't exist
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard" # Default page

    with st.sidebar:
        st.title("SkillPathAI") # Consistent Title
        display_name = st.session_state.get("name") or st.session_state.get("username", "Guest")
        st.write(f"👋 Welcome, {display_name}!")
        st.markdown("---")

        # Define navigation options
        nav_options = ["Dashboard", "Profile", "Guidance Hub"]

        # Use st.session_state.current_page to determine the default index
        try:
            # Find index for current page, default to 0 (Dashboard) if not found
            current_index = nav_options.index(st.session_state.current_page)
        except ValueError:
             # Handle cases where current_page might be 'Learning Path' or 'Career Transition'
            if st.session_state.current_page in ["Learning Path", "Career Transition"]:
                 current_index = nav_options.index("Guidance Hub")
            else:
                 current_index = 0 # Default to Dashboard if page unknown

        # Create the radio button navigation
        selection = st.radio(
            "Navigation",
            nav_options,
            index=current_index,
            key="main_nav" # Add a key for stability
        )

        # Update current_page based on sidebar selection *only if it changed*
        if selection != st.session_state.current_page:
             # Prevent resetting to 'Guidance Hub' when already on LP or CT
             if not (selection == "Guidance Hub" and st.session_state.current_page in ["Learning Path", "Career Transition"]):
                 st.session_state.current_page = selection
                 st.rerun() # Rerun immediately when sidebar selection changes

        st.markdown("---")
        if st.button("Logout"):
            # Reset relevant session state variables on logout
            st.session_state["authenticated"] = False
            st.session_state["current_page"] = "Dashboard" # Reset to default page
            # Clear other potential states if necessary
            # e.g., del st.session_state.lp_state, del st.session_state.ct_state etc.
            st.rerun()

    # Display the selected page based on the session state
    page_to_display = st.session_state.current_page

    # Create main content container
    main_content = st.container()

    # Main content area
    with main_content:
        if st.session_state.current_page == "Dashboard":
            render_dashboard_page()
        elif st.session_state.current_page == "Profile":
            render_profile_page()
        # elif st.session_state.current_page == "Courses":
        #     render_courses_page()
        elif st.session_state.current_page == "Learning Path":
            render_learning_path_page()
        elif st.session_state.current_page == "Guidance Hub":
            render_guidance_hub_page()
        elif st.session_state.current_page == "Career Transition":
            render_career_transition_page()
        else:
            # Fallback if state is somehow invalid
            st.error("Invalid page selected.")
            render_dashboard_page() # Show dashboard as default fallback