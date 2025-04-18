import logging
import os
import sys
import json
import streamlit as st
import pandas as pd

# Import backend services
from backend.services.resume_parser import extract_text
from backend.services.chat_service import ChatService
from backend.services.career_transition_service import (
    get_latest_resume_by_user_role, 
    process_missing_skills, 
    store_career_analysis,
    get_career_transition_courses,
    format_transition_plan
)
from backend.services.skill_matcher import extract_skills_from_text
from backend.services.cortex_service import ResumeSearchService

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("career_transition_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("career_transition")

def career_transition_page():
    """Main function for the Career Transition feature with resume analysis."""
    # Add extra padding at the top
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    st.header("🚀 Career Transition Assistant")
    
    # Create a hidden technical container for debug info (only used for backend errors)
    debug_container = st.empty()
    
    # Apply custom CSS for better styling
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

    # Initialize session state variables
    if "ct_state" not in st.session_state:
        st.session_state.ct_state = "ask_name"
    
    if "ct_messages" not in st.session_state:
        st.session_state.ct_messages = []
    
    if "ct_data" not in st.session_state:
        st.session_state.ct_data = {}

    # Helper function to add messages to the chat
    def add_message(role, content):
        st.session_state.ct_messages.append({"role": role, "content": content})

    # Display chat history
    for msg in st.session_state.ct_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # === Step 1: Ask for name ===
    if st.session_state.ct_state == "ask_name":
        if not st.session_state.ct_messages:
            add_message("assistant", "👋 Hello! I'll help you transition to a new career based on your resume. What's your name?")
            st.rerun()
        
        user_input = st.chat_input("Your name")
        if user_input:
            st.session_state.ct_data["name"] = user_input
            add_message("user", user_input)
            add_message("assistant", f"Nice to meet you, {user_input}! Please upload your resume so I can analyze your current skills.")
            st.session_state.ct_state = "ask_resume"
            st.rerun()

    # === Step 2: Ask for resume ===
    elif st.session_state.ct_state == "ask_resume":
        # Create a file uploader for resume
        uploaded_file = st.file_uploader("Upload your resume (PDF/DOCX):", type=["pdf", "docx"], key="resume_uploader")
        if uploaded_file:
            with st.spinner("Analyzing your resume..."):
                try:
                    # Extract text from the resume
                    resume_text = extract_text(uploaded_file)
                    if not resume_text or len(resume_text) < 50:
                        add_message("assistant", "⚠️ I couldn't extract enough text from your resume. Please try uploading a different file.")
                        st.rerun()
                    
                    # Store resume text
                    st.session_state.ct_data["resume_text"] = resume_text
                    
                    # Extract skills from resume
                    try:
                        if "chat_service" not in st.session_state:
                            st.session_state["chat_service"] = ChatService()
                        chat_service = st.session_state["chat_service"]
                        extracted_skills = chat_service.extract_skills(resume_text)
                    except Exception as e:
                        debug_container.error(f"Error extracting skills with LLM: {str(e)}")
                        extracted_skills = extract_skills_from_text(resume_text)
                    
                    # Store extracted skills
                    st.session_state.ct_data["extracted_skills"] = extracted_skills
                    
                    # Add resume upload message
                    add_message("user", f"*Uploaded resume: {uploaded_file.name}*")
                    
                    # Show extracted skills and ask for target role
                    skills_list = "\n".join([f"- {skill}" for skill in extracted_skills])
                    add_message("assistant", f"I've analyzed your resume and identified these skills:\n\n{skills_list}\n\nWhat career would you like to transition to?")
                    
                    # Update state
                    st.session_state.ct_state = "ask_target_role"
                    st.rerun()
                    
                except Exception as e:
                    debug_container.error(f"Error processing resume: {str(e)}")
                    add_message("assistant", "⚠️ There was an error processing your resume. Please try again with a different file format.")
                    st.rerun()

    # === Step 3: Ask for target role ===
    elif st.session_state.ct_state == "ask_target_role":
        user_input = st.chat_input("E.g., Data Scientist, Software Engineer")
        if user_input:
            st.session_state.ct_data["target_role"] = user_input
            add_message("user", user_input)
            
            # Add analysis message
            add_message("assistant", f"Thanks! I'll now analyze the skill gaps between your current profile and the requirements for a {user_input} role. This will take a moment...")
            
            # Store data in the resume database
            try:
                with st.spinner("Storing and analyzing your career data..."):
                    name = st.session_state.ct_data["name"]
                    resume_text = st.session_state.ct_data["resume_text"]
                    extracted_skills = st.session_state.ct_data["extracted_skills"]
                    target_role = st.session_state.ct_data["target_role"]
                    
                    # Store in database
                    service = ResumeSearchService()
                    service.store_resume(name, resume_text, extracted_skills, target_role)
                    debug_container.success("Resume data stored successfully")
            except Exception as e:
                debug_container.error(f"Error storing resume data: {str(e)}")
                # Continue despite storage error
            
            # Move to analyze state
            st.session_state.ct_state = "analyze_skills"
            st.rerun()

    # === Step 4: Analyze skills and generate recommendations ===
    elif st.session_state.ct_state == "analyze_skills":
        with st.spinner("Analyzing skill gaps and generating recommendations..."):
            try:
                # Get data from session state
                name = st.session_state.ct_data["name"]
                resume_text = st.session_state.ct_data["resume_text"]
                extracted_skills = st.session_state.ct_data["extracted_skills"]
                target_role = st.session_state.ct_data["target_role"]
                
                # Start showing immediate feedback
                skill_progress = st.progress(0.0, text="Processing skills...")
                
                # Get missing skills using our optimized service (direct LLM approach)
                debug_container.write("Identifying missing skills...")
                missing_skills = process_missing_skills(extracted_skills, target_role)
                st.session_state.ct_data["missing_skills"] = missing_skills
                debug_container.success(f"Identified {len(missing_skills)} missing skills")
                
                # Update progress
                skill_progress.progress(0.3, text="Storing analysis...")
                
                # Store analysis in database and get record ID
                debug_container.write("Storing career analysis data...")
                resume_id = store_career_analysis(
                    username=name,
                    resume_text=resume_text,
                    extracted_skills=extracted_skills,
                    target_role=target_role,
                    missing_skills=missing_skills
                )
                st.session_state.ct_data["resume_id"] = resume_id
                debug_container.success(f"Analysis stored with ID: {resume_id}")
                
                # Update progress
                skill_progress.progress(0.6, text="Searching for courses...")
                
                # Get course recommendations directly from our optimized service
                debug_container.write("Getting course recommendations...")
                courses_result = get_career_transition_courses(
                    target_role=target_role,
                    missing_skills=missing_skills
                )
                
                # Convert to DataFrame for compatibility
                if courses_result["count"] > 0:
                    courses_df = pd.DataFrame(courses_result["courses"])
                    debug_container.success(f"Found {len(courses_df)} course recommendations")
                    st.session_state.ct_data["courses"] = courses_df
                    
                    # Add course distribution analysis to chain of thought
                    beginner_count = len(courses_df[courses_df['LEVEL_CATEGORY'] == 'BEGINNER'])
                    intermediate_count = len(courses_df[courses_df['LEVEL_CATEGORY'] == 'INTERMEDIATE'])
                    advanced_count = len(courses_df[courses_df['LEVEL_CATEGORY'] == 'ADVANCED'])
                    
                else:
                    debug_container.warning("No courses found")
                    st.session_state.ct_data["courses"] = pd.DataFrame()
                
                # Complete progress
                skill_progress.progress(1.0, text="Analysis complete!")
                
                # Add completion message
                add_message("assistant", f"I've analyzed your path to becoming a {target_role}!")
                
                # Move to display state
                st.session_state.ct_state = "display_results"
                st.rerun()
                
            except Exception as e:
                debug_container.error(f"Error during skill analysis: {str(e)}")
                add_message("assistant", "I encountered an error during analysis. Please try again.")
                # Reset to target role state
                st.session_state.ct_state = "ask_target_role"
                st.rerun()

    # === Step 5: Display results ===
    elif st.session_state.ct_state == "display_results":
        if "results_displayed" not in st.session_state:
            # Get all necessary data
            name = st.session_state.ct_data["name"]
            target_role = st.session_state.ct_data["target_role"]
            extracted_skills = st.session_state.ct_data["extracted_skills"]
            missing_skills = st.session_state.ct_data["missing_skills"]
            courses_df = st.session_state.ct_data.get("courses", pd.DataFrame())
            
            # Convert DataFrame to list of records if not empty
            courses_list = []
            if not courses_df.empty:
                courses_list = courses_df.to_dict('records')
            
            # Use our new formatting function to create a consistent UI with learning path
            transition_plan = format_transition_plan(
                username=name,
                current_skills=extracted_skills,
                target_role=target_role,
                missing_skills=missing_skills,
                courses=courses_list
            )
            
            # Add the skill assessment section
            add_message("assistant", transition_plan["skill_assessment"])
            
            # Add introduction and course recommendations if valid courses were found
            if transition_plan["has_valid_courses"]:
                full_message = transition_plan["introduction"] + transition_plan["course_recommendations"]
                add_message("assistant", full_message)
            else:
                add_message("assistant", transition_plan["introduction"])
                add_message("assistant", "I couldn't find specific courses for your skill gaps. Try searching for courses related to the skills mentioned above on platforms like Coursera, Udemy, or LinkedIn Learning.")
            
            # Add career advice
            add_message("assistant", transition_plan["career_advice"])
            
            # Mark as displayed
            st.session_state.results_displayed = True
            st.rerun()
        
        # Handle follow-up questions
        user_input = st.chat_input("Ask a question about your career transition plan")
        if user_input:
            add_message("user", user_input)
            
            with st.spinner("Generating response..."):
                try:
                    # Create optimized context with fewer details for faster processing
                    context_prompt = (
                        f"You are a career coach helping someone transition to a {st.session_state.ct_data['target_role']} role. "
                        f"They have skills in: {', '.join(st.session_state.ct_data['extracted_skills'][:10])}. "
                        f"They need to learn: {', '.join(st.session_state.ct_data['missing_skills'])}. "
                        f"Keep your answer brief and actionable."
                    )
                    
                    # Get a fast response using our direct LLM approach
                    chat_service = ChatService()
                    followup_response = chat_service.get_llm_response(
                        prompt=user_input,
                        context=context_prompt,
                        max_retries=1  # Only try once for faster response
                    )
                    
                    add_message("assistant", followup_response)
                except Exception as e:
                    debug_container.error(f"Error generating response: {str(e)}")
                    # Fallback to a simple templated response
                    add_message("assistant", f"To answer your question about {user_input}: Focus on building the specific skills I recommended for a {st.session_state.ct_data['target_role']} role, especially through practical projects and courses that directly address your skill gaps.")
            
            st.rerun()
    
    # Add restart button in the sidebar
    with st.sidebar:
        if st.button("Start New Career Analysis"):
            # Reset career transition state
            st.session_state.ct_state = "ask_name"
            st.session_state.ct_messages = []
            st.session_state.ct_data = {}
            if "results_displayed" in st.session_state:
                del st.session_state.results_displayed
            st.rerun()