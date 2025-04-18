# dashboard.py
import sys
import os
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.resume_parser import extract_text
from backend.services.cortex_service import ResumeSearchService
from backend.services.chat_service import ChatService
from backend.services.skill_matcher import match_skills, extract_skills_from_text, get_job_requirements, generate_skill_recommendations
from backend.services.learning_path_service import get_learning_path



# Load custom CSS from styles.css
with open("styles.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# --- Dashboard ---
def dashboard():
    st.header("Dashboard")
    st.write(f"Welcome, {st.session_state.get('username', 'Guest')}!")
    
    # User stats in a card
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Skills Identified", "12")
        with col2:
            st.metric("Learning Progress", "65%")
        with col3:
            st.metric("Career Matches", "8")
        st.markdown('</div>', unsafe_allow_html=True)

    # Progress charts in a card
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        st.subheader("Your Learning Progress")
        data = {
            "Python Basics": 100,
            "Data Analysis": 80,
            "Machine Learning": 60,
            "Web Development": 40,
            "Cloud Services": 20
        }
        st.bar_chart(data)
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent activity in a card
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        st.subheader("Recent Activity")
        st.info("Completed Python Basics course")
        st.info("Added new skills to your profile")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Profile ---
def profile():
    st.header("Profile")
    
    # User info in a card
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("https://via.placeholder.com/150", width=150)
        with col2:
            st.write(f"## {st.session_state.get('username', 'Guest')}")
            st.write("Member since: January 2023")
            st.write("Career Goal: Data Scientist")
        st.markdown('</div>', unsafe_allow_html=True)

    # Skills in a card
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        st.subheader("Your Skills")
        skills = {
            "Technical Skills": ["Python", "SQL", "Data Analysis", "Pandas", "Matplotlib"],
            "Soft Skills": ["Communication", "Teamwork", "Problem Solving"],
            "Industry Knowledge": ["Healthcare", "Finance"]
        }
        for category, skill_list in skills.items():
            st.write(f"**{category}:**")
            st.write(", ".join(skill_list))
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Edit Profile"):
        st.session_state["profile_edit"] = True
    
    if st.session_state.get("profile_edit", False):
        with st.container():
            st.markdown('<div class="container-card">', unsafe_allow_html=True)
            with st.form("profile_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                st.form_submit_button("Save")
            st.markdown('</div>', unsafe_allow_html=True)

# --- Courses ---
def courses():
    st.header("Courses")
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        st.write("Search and explore courses available on the platform.")
        search_query = st.text_input("Search for courses:")
        if st.button("Search"):
            st.write(f"Results for '{search_query}' will be displayed here.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Learning Path ---
def learning_path():
    from frontend.pages.learning_path import learning_path_chat
    learning_path_chat()


# --- Career Transition Chat System ---
def career_transition():
    from frontend.pages.career_transition import career_transition_page
    career_transition_page()

# --- Main Application Layout with Full Navigation ---
def main_app():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio(
        "Go to", 
        ["Dashboard", "Profile", "Courses", "Learning Path", "Career Transition"]
    )

    if selection == "Dashboard":
        dashboard()
    elif selection == "Profile":
        profile()
    elif selection == "Courses":
        courses()
    elif selection == "Learning Path":
         learning_path()
    elif selection == "Career Transition":
        career_transition()

    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()