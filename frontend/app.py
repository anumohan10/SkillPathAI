import sys
import os
import streamlit as st


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from backend.services.resume_parser import extract_text
from backend.services.cortex_service import ResumeSearchService

from backend.services.chat_service import ChatService
from backend.services.skill_matcher import match_skills, extract_skills_from_text, get_job_requirements, generate_skill_recommendations
from frontend.learning_path import learning_path_chat


from frontend.components.career_chat import CareerChat

# --- Authentication Function ---
USER_CREDENTIALS = {
    "alice": "password123",
    "bob": "securepwd",
    "demo" : "demo"
}

def login():
    st.title("SkillPath - Career Transition Platform")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    
    # Demo mode
    st.markdown("---")
    if st.button("Try Demo Mode"):
        st.session_state["authenticated"] = True
        st.session_state["username"] = "demo"
        st.rerun()

# --- Dashboard ---
def dashboard():
    st.header("Dashboard")
    st.write(f"Welcome, {st.session_state.get('username', 'Guest')}!")
    
    # User stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Skills Identified", "12")
    
    with col2:
        st.metric("Learning Progress", "65%")
    
    with col3:
        st.metric("Career Matches", "8")
    
    # Progress charts
    st.subheader("Your Learning Progress")
    data = {
        "Python Basics": 100,
        "Data Analysis": 80,
        "Machine Learning": 60,
        "Web Development": 40,
        "Cloud Services": 20
    }
    
    st.bar_chart(data)
    
    # Recent activity
    st.subheader("Recent Activity")
    st.info("Completed Python Basics course")
    st.info("Added new skills to your profile")

# --- Profile ---
def profile():
    st.header("Profile")
    
    # User info
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.image("https://via.placeholder.com/150", width=150)
    
    with col2:
        st.write(f"## {st.session_state.get('username', 'Guest')}")
        st.write("Member since: January 2023")
        st.write("Career Goal: Data Scientist")
    
    # Skill summary
    st.subheader("Your Skills")
    
    skills = {
        "Technical Skills": ["Python", "SQL", "Data Analysis", "Pandas", "Matplotlib"],
        "Soft Skills": ["Communication", "Teamwork", "Problem Solving"],
        "Industry Knowledge": ["Healthcare", "Finance"]
    }
    
    for category, skill_list in skills.items():
        st.write(f"**{category}:**")
        st.write(", ".join(skill_list))
    
    # Edit profile
    if st.button("Edit Profile"):
        st.session_state["profile_edit"] = True
    
    if st.session_state.get("profile_edit", False):
        with st.form("profile_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")

# --- Courses ---
def courses():
    st.header("Courses")
    st.write("Search and explore courses available on the platform.")
    search_query = st.text_input("Search for courses:")
    if st.button("Search"):
        st.write(f"Results for '{search_query}' will be displayed here.")

# --- Learning Path ---
def learning_path():
    learning_path_chat()


# --- Career Transition Chat System ---
# --- Career Transition Chat System ---
def career_transition():
    st.header("Career Transition Assistant")
    
    # Initialize chat state and history
    if "career_chat_state" not in st.session_state:
        st.session_state["career_chat_state"] = "welcome"
        st.session_state["chat_messages"] = []
    
    # Initialize user data
    if "career_user_data" not in st.session_state:
        st.session_state["career_user_data"] = {}
    
    # Add welcome message if this is the first interaction
    if st.session_state["career_chat_state"] == "welcome":
        welcome_message = {
            "role": "assistant",
            "content": "👋 Hi there! I'm your Career Transition Assistant. I'll help you identify your current skills and create a personalized path to your dream career. What's your name?"
        }
        st.session_state["chat_messages"].append(welcome_message)
        st.session_state["career_chat_state"] = "ask_name"
    
    # Display chat history
    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle user input based on current state
    if st.session_state["career_chat_state"] == "ask_name":
        # Get name via chat input
        user_input = st.chat_input("Enter your name...")
        if user_input:
            # Add user message to chat
            st.session_state["chat_messages"].append({"role": "user", "content": user_input})
            
            # Store name
            st.session_state["career_user_data"]["name"] = user_input
            
            # Add assistant response
            assistant_msg = {
                "role": "assistant", 
                "content": f"Nice to meet you, {user_input}! To help with your career transition, I'll need to analyze your resume. Please upload it as a PDF or DOCX file."
            }
            st.session_state["chat_messages"].append(assistant_msg)
            
            # Move to next state
            st.session_state["career_chat_state"] = "ask_resume"
            st.rerun()
    
    elif st.session_state["career_chat_state"] == "ask_resume":
        # Create file uploader in the chat
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                uploaded_file = st.file_uploader("Upload your resume (PDF/DOCX):", type=["pdf", "docx"], key="resume_uploader")
            with col2:
                submit_button = st.button("Upload", key="resume_submit")
        
        if submit_button and uploaded_file:
            # Process the file
            try:
                with st.spinner("Reading your resume..."):
                    resume_text = extract_text(uploaded_file)
                    
                    if not resume_text or len(resume_text) < 50:
                        error_msg = {"role": "assistant", "content": "⚠️ I couldn't read enough text from that file. Could you try uploading a different format?"}
                        st.session_state["chat_messages"].append(error_msg)
                        st.rerun()
                    
                    # Store resume text
                    st.session_state["career_user_data"]["resume_text"] = resume_text
                    
                    # Add messages to chat
                    user_msg = {"role": "user", "content": f"*Uploaded resume: {uploaded_file.name}*"}
                    st.session_state["chat_messages"].append(user_msg)
                    
                    assistant_msg = {
                        "role": "assistant", 
                        "content": "Great! I've received your resume. What career are you interested in transitioning to?"
                    }
                    st.session_state["chat_messages"].append(assistant_msg)
                    
                    # Update state
                    st.session_state["career_chat_state"] = "ask_target_career"
                    st.rerun()
                    
            except Exception as e:
                error_msg = {"role": "assistant", "content": f"⚠️ There was an error processing your resume: {str(e)}. Please try again."}
                st.session_state["chat_messages"].append(error_msg)
                st.rerun()
    
    elif st.session_state["career_chat_state"] == "ask_target_career":
        # Get target career via chat input
        user_input = st.chat_input("What career are you interested in?")
        if user_input:
            # Add to chat
            st.session_state["chat_messages"].append({"role": "user", "content": user_input})
            
            # Store target career
            st.session_state["career_user_data"]["target_career"] = user_input
            
            # Add thinking message
            assistant_msg = {
                "role": "assistant", 
                "content": f"Thanks! I'll now analyze your resume to determine the best path to transition to a {user_input} role. This will take a moment..."
            }
            st.session_state["chat_messages"].append(assistant_msg)
            
            # Move to analysis state
            st.session_state["career_chat_state"] = "analyzing"
            st.rerun()
    
    elif st.session_state["career_chat_state"] == "analyzing":
        # Perform analysis
        with st.spinner("Analyzing your resume and career path..."):
            try:
                # Get user data
                name = st.session_state["career_user_data"]["name"]
                resume_text = st.session_state["career_user_data"]["resume_text"]
                target_career = st.session_state["career_user_data"]["target_career"]
                
                # Initialize chat service if available
                try:
                    if "chat_service" not in st.session_state:
                        st.session_state["chat_service"] = ChatService()
                    chat_service = st.session_state["chat_service"]
                except Exception as e:
                    chat_service = None
                    st.warning(f"Could not initialize LLM service: {str(e)}")
                
                # Extract skills
                if chat_service:
                    try:
                        extracted_skills = chat_service.extract_skills(resume_text)
                        extraction_method = "LLM"
                    except Exception as e:
                        extracted_skills = extract_skills_from_text(resume_text)
                        extraction_method = "regex"
                else:
                    extracted_skills = extract_skills_from_text(resume_text)
                    extraction_method = "regex"
                
                # Store extracted skills
                st.session_state["career_user_data"]["extracted_skills"] = extracted_skills
                st.session_state["career_user_data"]["extraction_method"] = extraction_method
                
                # Match skills with requirements
                skill_analysis = match_skills(extracted_skills, target_career)
                st.session_state["career_user_data"]["skill_analysis"] = skill_analysis
                
                # Generate career advice
                if chat_service:
                    try:
                        career_advice = chat_service.generate_career_advice(extracted_skills, target_career)
                        advice_method = "LLM"
                    except Exception as e:
                        career_advice = skill_analysis.get("recommendations", "")
                        advice_method = "template"
                else:
                    career_advice = skill_analysis.get("recommendations", "")
                    advice_method = "template"
                
                # Store advice
                st.session_state["career_user_data"]["career_advice"] = career_advice
                st.session_state["career_user_data"]["advice_method"] = advice_method
                
                # Try to store in database (non-critical)
                try:
                    service = ResumeSearchService()
                    service.store_resume(name, resume_text, extracted_skills, target_career)
                except Exception as e:
                    pass
                
                # Add completion message
                completed_msg = {
                    "role": "assistant",
                    "content": f"I've completed my analysis for your transition to a {target_career} role. Here's what I found:"
                }
                st.session_state["chat_messages"].append(completed_msg)
                
                # Move to results state
                st.session_state["career_chat_state"] = "show_results"
                st.rerun()
                
            except Exception as e:
                error_msg = {"role": "assistant", "content": f"⚠️ I encountered an error during analysis: {str(e)}. Let's try again."}
                st.session_state["chat_messages"].append(error_msg)
                st.session_state["career_chat_state"] = "ask_target_career"
                st.rerun()
  

    
    elif st.session_state["career_chat_state"] == "show_results":
        # Display results
        if "results_displayed" not in st.session_state:
            # Get data
            name = st.session_state["career_user_data"]["name"]
            target_career = st.session_state["career_user_data"]["target_career"]
            extracted_skills = st.session_state["career_user_data"]["extracted_skills"]
            skill_analysis = st.session_state["career_user_data"]["skill_analysis"]
            career_advice = st.session_state["career_user_data"]["career_advice"]
            
            # Add skills message
            skills_msg = {
                "role": "assistant",
                "content": f"### Your Current Skills\n" + "\n".join([f"- {skill}" for skill in extracted_skills])
            }
            st.session_state["chat_messages"].append(skills_msg)
            
            # Add skill gap message if available
            if "essential_skills" in skill_analysis and skill_analysis["essential_skills"]:
                gap_content = f"### Skills Needed for {target_career}\n\n**Essential Skills:**\n"
                
                for skill in skill_analysis.get("essential_skills", []):
                    if skill in extracted_skills:
                        gap_content += f"- ✅ {skill}\n"
                    else:
                        gap_content += f"- ❌ {skill}\n"
                
                gap_content += "\n**Preferred Skills:**\n"
                for skill in skill_analysis.get("preferred_skills", []):
                    if skill in extracted_skills:
                        gap_content += f"- ✅ {skill}\n"
                    else:
                        gap_content += f"- ❓ {skill}\n"
                
                gap_msg = {"role": "assistant", "content": gap_content}
                st.session_state["chat_messages"].append(gap_msg)
            
            # Add career advice
            advice_msg = {"role": "assistant", "content": career_advice}
            st.session_state["chat_messages"].append(advice_msg)
            
            # Add follow-up question
            followup_msg = {
                "role": "assistant",
                "content": "Do you have any specific questions about this career transition plan? Feel free to ask!"
            }
            st.session_state["chat_messages"].append(followup_msg)
            
            # Mark as displayed
            st.session_state["results_displayed"] = True
            st.rerun()
        
        # Handle follow-up questions
        user_input = st.chat_input("Ask a follow-up question...")
        if user_input:
            # Add question to chat
            st.session_state["chat_messages"].append({"role": "user", "content": user_input})
            
            # Try to get LLM response
            try:
                if "chat_service" in st.session_state and st.session_state["chat_service"]:
                    chat_service = st.session_state["chat_service"]
                    
                    # Create context
                    user_context = {
                        "name": st.session_state["career_user_data"]["name"],
                        "target_role": st.session_state["career_user_data"]["target_career"],
                        "skills": st.session_state["career_user_data"]["extracted_skills"]
                    }
                    
                    # Get response
                    response = chat_service.answer_career_question(user_input, user_context)
                else:
                    # Fallback template response
                    response = (
                        f"That's a great question about transitioning to a {st.session_state['career_user_data']['target_career']} role. "
                        f"Based on your background, I recommend focusing on building relevant technical skills "
                        f"through online courses and practical projects. Networking with professionals in the field "
                        f"can also provide valuable insights and opportunities."
                    )
            except Exception as e:
                response = (
                    f"That's a good question. For transitioning to {st.session_state['career_user_data']['target_career']}, "
                    f"I generally recommend a combination of structured learning, practical projects, and professional networking. "
                    f"This approach helps you build skills, demonstrate them, and connect with opportunities."
                )
            
            # Add response to chat
            st.session_state["chat_messages"].append({"role": "assistant", "content": response})
            st.rerun()
    
    # Add restart button outside the chat flow
    with st.sidebar:
        if st.button("Start New Career Analysis"):
            # Reset chat
            st.session_state["career_chat_state"] = "welcome"
            st.session_state["chat_messages"] = []
            st.session_state["career_user_data"] = {}
            if "results_displayed" in st.session_state:
                del st.session_state["results_displayed"]
            st.rerun()
            
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

# --- Main Function ---
def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        main_app()
    else:
        login()

if __name__ == '__main__':
    main()
