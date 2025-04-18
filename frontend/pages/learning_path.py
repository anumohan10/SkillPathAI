import logging
import os
import sys
import json
import streamlit as st
import pandas as pd

# Import backend services
from backend.services.learning_path_service import store_learning_path
from backend.services.skill_service import get_top_skills_for_role, format_skills_for_display
from backend.services.course_service import get_course_recommendations
from backend.services.ui_service import format_course_message, format_introduction, format_career_advice
from backend.services.chat_service import ChatService

# Set up logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("learning_path_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("learning_path")


def learning_path_chat():
    """Main function for the Learning Path chat feature with proper error handling."""
    # Add extra padding at the top
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    st.header("🎯 Personalized Learning Path")
    
    # Add expandable debug section
    with st.expander("Diagnostic Information (Click to expand)"):
        debug_container = st.container()
    
    # Apply custom CSS for better chat styling
    st.markdown("""
    <style>
    /* Increase width of main content area */
    .block-container {
        max-width: 1100px !important;
        padding: 0 1rem !important;
    }
    
    /* Add more space at the top of the page */
    header {
        margin-bottom: 2rem !important;
    }
    
    /* Make course details stand out more */
    .stMarkdown h3 {
        font-size: 1.5rem !important;
        margin-top: 1.5rem !important;
        color: #1E88E5 !important;
    }
    
    /* Improve platform and level info */
    .stMarkdown strong {
        font-size: 1.1rem !important;
    }
    
    /* Enhance course descriptions */
    .stMarkdown p {
        font-size: 1.1rem !important;
        line-height: 1.6 !important;
    }
    
    /* Improve section headers */
    .stMarkdown h2 {
        font-size: 1.8rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        color: #202020 !important;
        border-bottom: 2px solid #f0f0f0;
        padding-bottom: 0.5rem;
    }
    
    /* Improve main heading */
    .stMarkdown h3:first-of-type {
        margin-top: 3rem !important;
        font-size: 2rem !important;
        color: #2E7D32 !important;
        padding-top: 1.5rem !important;
    }
    
    /* Make chat messages larger */
    .stChatMessage {
        padding: 1.5rem !important;
        border-radius: 10px !important;
        margin-bottom: 1.5rem !important;
        font-size: 1.1rem !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    }
    
    /* Style user messages */
    .stChatMessage[data-sender="user"] {
        background-color: #E3F2FD !important;
        border-left: 5px solid #2196F3 !important;
    }
    
    /* Style assistant messages */
    .stChatMessage[data-sender="assistant"] {
        background-color: #F1F8E9 !important;
        border-left: 5px solid #8BC34A !important;
    }
    
    /* Make chat container more prominent */
    .stChatContainer {
        border: 1px solid #E0E0E0 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    
    /* Enlarge chat input */
    .stChatInputContainer {
        padding: 1.5rem !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    .stChatInputContainer textarea {
        font-size: 1.2rem !important;
        line-height: 1.6 !important;
        padding: 15px !important;
        min-height: 100px !important;
        border-radius: 10px !important;
        border: 2px solid #4CAF50 !important;
    }
    
    /* Add focus effect to text input */
    .stChatInputContainer textarea:focus {
        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.3) !important;
        border-color: #4CAF50 !important;
    }
    
    /* Make chat submit button larger */
    .stChatInputContainer button[kind="primary"] {
        height: 50px !important;
        width: 50px !important;
        border-radius: 25px !important;
    }
    
    /* Style the send icon */
    .stChatInputContainer button[kind="primary"] svg {
        width: 24px !important;
        height: 24px !important;
    }
    
    /* Improve skills list formatting */
    .stMarkdown ul {
        padding-left: 1.5rem !important;
    }
    
    /* Make links better */
    .stMarkdown a {
        font-size: 1.2rem !important;
        text-decoration: none !important;
        display: inline-block !important;
        background-color: #4CAF50 !important;
        color: white !important;
        padding: 10px 15px !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        margin: 20px 0 !important;
    }
    
    /* Improve horizontal rule between courses */
    .stMarkdown hr {
        margin: 2rem 0 !important;
        border-color: #f0f0f0 !important;
    }
    
    /* Style div elements properly */
    .element-container div div {
        font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state for the learning path conversation
    if "lp_state" not in st.session_state:
        st.session_state.lp_state = "ask_name"
        st.session_state.lp_messages = []
        st.session_state.lp_data = {}

    # Helper function to add messages to the chat
    def add_message(role, content):
        st.session_state.lp_messages.append({"role": role, "content": content})

    # Display chat history
    for msg in st.session_state.lp_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # === Step 1: Ask for name ===
    if st.session_state.lp_state == "ask_name":
        if not st.session_state.lp_messages:
            add_message("assistant", "👋 Hello! I'll help you create a personalized learning path. What's your name?")
            st.rerun()
        
        user_input = st.chat_input("Your name")
        if user_input:
            st.session_state.lp_data["name"] = user_input
            add_message("user", user_input)
            add_message("assistant", f"Nice to meet you, {user_input}! What career would you like to pursue? (e.g., Data Engineer, Data Scientist, Software Engineer)")
            st.session_state.lp_state = "ask_role"
            st.rerun()

    # === Step 2: Ask target role ===
    elif st.session_state.lp_state == "ask_role":
        user_input = st.chat_input("E.g., Data Engineer, Data Scientist")
        if user_input:
            st.session_state.lp_data["target_role"] = user_input
            add_message("user", user_input)
            
            # Get top skills for the role from our skill service
            with st.spinner("Identifying key skills for this role..."):
                try:
                    top_skills = get_top_skills_for_role(user_input)
                    st.session_state.lp_data["top_skills"] = top_skills
                    st.session_state.lp_data["skill_ratings"] = {}
                    st.session_state.lp_data["current_skill_index"] = 0
                    
                    skills_list = "\n".join([f"- {skill}" for skill in top_skills])
                    add_message("assistant", f"Great! For a **{user_input}** role, these are the top skills you'll need:\n\n{skills_list}\n\nLet's assess your current skill level in each area.")
                    st.session_state.lp_state = "rate_skills"
                except Exception as e:
                    debug_container.error(f"Error getting skills: {str(e)}")
                    add_message("assistant", "I'm having trouble identifying key skills for this role. Let me help you build a more general learning path instead. What specific areas are you interested in learning about?")
                    st.session_state.lp_state = "manual_skills"
            st.rerun()
    
    # === Step 2b: Manual skills entry (if automatic fails) ===
    elif st.session_state.lp_state == "manual_skills":
        user_input = st.chat_input("Enter skills (comma-separated)")
        if user_input:
            add_message("user", user_input)
            
            # Parse manually entered skills
            skills = [skill.strip() for skill in user_input.split(',') if skill.strip()]
            if len(skills) < 5:
                # Pad to 5 skills with empty strings
                skills.extend([""] * (5 - len(skills)))
            
            st.session_state.lp_data["top_skills"] = skills[:5]
            st.session_state.lp_data["skill_ratings"] = {}
            st.session_state.lp_data["current_skill_index"] = 0
            
            add_message("assistant", "Thanks for providing those skills. Let's rate your proficiency in each area.")
            st.session_state.lp_state = "rate_skills"
            st.rerun()

    # === Step 3a: Ask for skill ratings ===
    elif st.session_state.lp_state == "rate_skills":
        skills = st.session_state.lp_data["top_skills"]
        index = st.session_state.lp_data["current_skill_index"]
        
        if index < len(skills) and skills[index]:  # Skip empty skills
            current_skill = skills[index]
            add_message("assistant", f"How would you rate your proficiency in **{current_skill}** on a scale of 1-5?\n\n1: No experience\n2: Basic knowledge\n3: Intermediate\n4: Advanced\n5: Expert")
            st.session_state.lp_state = "wait_for_rating"
            st.rerun()
        else:
            # Skip empty skills or move to next step if we've rated all skills
            if index < len(skills):
                st.session_state.lp_data["current_skill_index"] = index + 1
                st.session_state.lp_state = "rate_skills"
                st.rerun()
            else:
                # If all skills are rated, move to generating courses
                st.session_state.lp_state = "generate_courses"
                st.rerun()

    # === Step 3b: Wait for skill rating input ===
    elif st.session_state.lp_state == "wait_for_rating":
        skills = st.session_state.lp_data["top_skills"]
        index = st.session_state.lp_data["current_skill_index"]
        current_skill = skills[index]
        
        user_input = st.chat_input(f"Rate your {current_skill} skills (1-5)")
        if user_input:
            try:
                rating = int(user_input.strip())
                if 1 <= rating <= 5:
                    st.session_state.lp_data["skill_ratings"][current_skill] = rating
                    add_message("user", f"{rating}")
                    
                    # Move to next skill
                    st.session_state.lp_data["current_skill_index"] = index + 1
                    st.session_state.lp_state = "rate_skills"
                    st.rerun()
                else:
                    add_message("assistant", "Please enter a valid rating between 1 and 5.")
                    st.rerun()
            except ValueError:
                add_message("assistant", "Please enter a number between 1 and 5.")
                st.rerun()

    # === Step 4: Generate course recommendations ===
    elif st.session_state.lp_state == "generate_courses":
        with st.spinner("Searching for the best courses for your learning path..."):
            target_role = st.session_state.lp_data["target_role"]
            
            # Store the learning path first to get an ID
            try:
                debug_container.write("Attempting to store learning path...")
                store_result = store_learning_path(st.session_state.lp_data)
                if store_result:
                    debug_container.success("Learning path stored successfully")
                    # Get the ID from the stored data
                    user_id = st.session_state.lp_data.get("record_id")
                    debug_container.write(f"Using record ID: {user_id}")
            except Exception as e:
                debug_container.error(f"Error saving learning path: {str(e)}")
                user_id = None
                # Continue despite storage error
            
            # Get recommended courses with user skill data if available
            try:
                debug_container.write("Attempting to get course recommendations...")
                courses_df = get_course_recommendations(target_role, user_id)
                debug_container.write(f"Retrieved {len(courses_df)} course recommendations")
                st.session_state.lp_data["courses"] = courses_df
            except Exception as e:
                debug_container.error(f"Error retrieving courses: {str(e)}")
                st.session_state.lp_data["courses"] = pd.DataFrame()
                # Don't add a message about the error - we'll handle this in the display step
            
            # Storage is handled above in the updated flow
            
            # Add completion message
            add_message("assistant", f"I've created your personalized learning path for becoming a **{target_role}**!")
            st.session_state.lp_state = "display_results"
            st.rerun()

    # === Step 5: Display results ===
    elif st.session_state.lp_state == "display_results":
        if "results_displayed" not in st.session_state:
            # Get personalized data
            name = st.session_state.lp_data["name"]
            target_role = st.session_state.lp_data["target_role"]
            skill_ratings = st.session_state.lp_data["skill_ratings"]
            courses_df = st.session_state.lp_data.get("courses", pd.DataFrame())
            
            # Use our skill service to format the skill assessment
            skill_assessment = format_skills_for_display(skill_ratings)
            add_message("assistant", skill_assessment)
            
            # Format and display course recommendations using our UI service
            course_msg, has_valid_courses = format_course_message(courses_df, target_role)
            
            if has_valid_courses:
                # Add personalized introduction
                intro = format_introduction(target_role, skill_ratings)
                full_message = intro + course_msg
                add_message("assistant", full_message)
            else:
                debug_container.warning("No valid courses found in the results")
                add_message("assistant", course_msg)  # This will contain the error message
            
            # Add career advice from our UI service
            career_advice = format_career_advice()
            add_message("assistant", career_advice)
            
            # Mark as displayed
            st.session_state.results_displayed = True
            st.rerun()
        
        # Handle follow-up questions
        user_input = st.chat_input("Ask a question about your learning path")
        if user_input:
            add_message("user", user_input)
            
            # Try to get answer from ChatService using the specialized method
            try:
                # Create context dictionary for the chat service
                user_context = {
                    'name': st.session_state.lp_data['name'],
                    'target_role': st.session_state.lp_data['target_role'],
                    'skills': list(st.session_state.lp_data['skill_ratings'].keys()),
                    'skill_ratings': st.session_state.lp_data['skill_ratings']
                }
                
                # Use answer_career_question method to get more focused responses
                chat_service = ChatService()
                followup_response = chat_service.answer_career_question(user_input, user_context)
                add_message("assistant", followup_response)
            except Exception as e:
                debug_container.error(f"Error generating response: {str(e)}")
                add_message("assistant", "I'm having trouble processing your question right now. Could you try asking in a different way?")
            
            st.rerun()
    
    # Add restart button in the sidebar
    with st.sidebar:
        if st.button("Create New Learning Path"):
            # Reset chat state
            st.session_state.lp_state = "ask_name"
            st.session_state.lp_messages = []
            st.session_state.lp_data = {}
            if "results_displayed" in st.session_state:
                del st.session_state.results_displayed
            st.rerun()