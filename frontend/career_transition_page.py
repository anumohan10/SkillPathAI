import logging
import os
import sys
import json
import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# Ensure backend services can be imported
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import backend services
from frontend.ui_service import format_transition_plan

# Set up logging
logging.basicConfig(
    level=logging.INFO, # Changed default level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("career_transition_debug.log", mode='a'), # Append mode
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
now = datetime.now()

# Define API URL - should be configurable in production
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Custom JSON encoder to handle non-serializable objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return str(obj)

def save_session_state_api(user_name, session_state_data, cur_timestamp, source_page, role):
    """Save entire session state data via API instead of direct function call."""
    try:
        logger.info(f"Type of session state data: {type(session_state_data)}")
        
        # Convert to JSON string for API using the custom encoder
        session_state_json = json.dumps(session_state_data, cls=CustomJSONEncoder)
        
        # Call the API endpoint to save session state data
        logger.info(f"Session state data: {session_state_json[:100]}...")  # Log only first 100 chars
        
        response = requests.post(
            f"{API_URL}/user-input/save-session-state",
            json={
                "user_name": user_name,
                "session_state": session_state_json,  # Send as JSON string
                "timestamp": cur_timestamp,
                "source_page": source_page,
                "role": role
            }
        )
        
        if response.status_code == 200:
            logger.info("Session state data saved successfully via API")
            return True
        else:
            logger.error(f"API error saving session state data: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error calling session state API: {str(e)}")
        return False

def extract_resume_text_api(file):
    """Extract text from a resume file using the API."""
    try:
        # Prepare the file for upload
        files = {"file": (file.name, file, file.type)}
        
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/resume/extract",
            files=files
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info("Resume text extracted successfully via API")
                return data.get("text", "")
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return ""
        else:
            logger.error(f"API error extracting resume text: {response.status_code}")
            return ""
    except Exception as e:
        logger.error(f"Error calling resume extraction API: {str(e)}")
        return ""

def extract_skills_api(resume_text):
    """Extract skills from resume text using the API."""
    try:
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/skills/extract",
            json={"resume_text": resume_text}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info(f"Successfully extracted {len(data['skills'])} skills via API")
                return data.get("skills", [])
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return []
        else:
            logger.error(f"API error extracting skills: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error calling skills extraction API: {str(e)}")
        return []

def extract_skills_regex_api(resume_text):
    """Extract skills from resume text using regex via the API."""
    try:
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/skills/extract-regex",
            json={"resume_text": resume_text}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info(f"Successfully extracted {len(data['skills'])} skills via regex API")
                return data.get("skills", [])
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return []
        else:
            logger.error(f"API error extracting skills with regex: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error calling skills regex extraction API: {str(e)}")
        return []

def process_missing_skills_api(extracted_skills, target_role):
    """Process missing skills for a target role using the API."""
    try:
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/skills/missing",
            json={
                "extracted_skills": extracted_skills,
                "target_role": target_role
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info(f"Successfully identified {len(data['missing_skills'])} missing skills via API")
                return data.get("missing_skills", [])
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return []
        else:
            logger.error(f"API error processing missing skills: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error calling missing skills API: {str(e)}")
        return []

def store_career_analysis_api(username, resume_text, extracted_skills, target_role, missing_skills):
    """Store career analysis data using the API."""
    try:
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/career-analysis/store",
            json={
                "username": username,
                "resume_text": resume_text,
                "extracted_skills": extracted_skills,
                "target_role": target_role,
                "missing_skills": missing_skills
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info(f"Successfully stored career analysis, ID: {data.get('resume_id')}")
                return data.get("resume_id")
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return None
        else:
            logger.error(f"API error storing career analysis: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error calling career analysis storage API: {str(e)}")
        return None

def get_career_transition_courses_api(target_role, missing_skills, limit=6):
    """Get career transition courses using the API."""
    try:
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/career-courses",
            json={
                "target_role": target_role,
                "missing_skills": missing_skills,
                "limit": limit
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info(f"Successfully retrieved {data.get('count', 0)} courses via API")
                return data
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return {"courses": [], "count": 0}
        else:
            logger.error(f"API error getting career transition courses: {response.status_code}")
            return {"courses": [], "count": 0}
    except Exception as e:
        logger.error(f"Error calling career transition courses API: {str(e)}")
        return {"courses": [], "count": 0}

def format_transition_plan_api(username, current_skills, target_role, missing_skills, courses):
    """Format transition plan using the API."""
    try:
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/transition-plan",
            json={
                "username": username,
                "current_skills": current_skills,
                "target_role": target_role,
                "missing_skills": missing_skills,
                "courses": courses
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info("Successfully formatted transition plan via API")
                return data
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return None
        else:
            logger.error(f"API error formatting transition plan: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error calling transition plan API: {str(e)}")
        return None

def answer_career_question_api(question, user_context):
    """Answer a career-related question using the API."""
    try:
        # Call the API endpoint
        response = requests.post(
            f"{API_URL}/user-input/career-question",
            json={
                "question": question,
                "user_context": user_context
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info("Successfully received answer from career question API")
                return data.get("response", "")
            else:
                logger.warning(f"API returned failure: {data.get('message')}")
                return "I'm having trouble answering your question right now. Please try asking in a different way."
        elif response.status_code == 503:
            # Service unavailable - extract error message from response
            error_detail = response.json().get("detail", "Unknown error")
            logger.error(f"Service unavailable: {error_detail}")
            return f"I'm having trouble answering your question right now: {error_detail}"
        else:
            logger.error(f"API error answering career question: {response.status_code}")
            return "I'm having trouble answering your question right now. Please try again later."
    except Exception as e:
        logger.error(f"Error calling career question API: {str(e)}")
        return "I'm having trouble connecting to the service right now. Please try again later."

def render_career_transition_page(): # Renamed function
    """Main function for the Career Transition feature with resume analysis."""

    # --- Log state at the beginning of each execution ---
    logger.info(f"--- Entering render_career_transition_page ---")
    logger.info(f"Current ct_state: {st.session_state.get('ct_state', 'Not Set')}")
    logger.info(f"Current page: {st.session_state.get('current_page', 'Not Set')}")
    logger.info(f"CT Messages count: {len(st.session_state.get('ct_messages', []))}")
    logger.info(f"CT Data keys: {list(st.session_state.get('ct_data', {}).keys())}")
    # --- End Logging ---

    # Add Back button
    if st.button("⬅️ Back to Guidance Hub"):
        st.session_state.current_page = "Guidance Hub"
        # Save chat history before clearing
        if 'ct_messages' in st.session_state and len(st.session_state.ct_messages) > 0 and st.session_state.get('results_displayed', False):
            save_session_state_api(
                user_name=st.session_state.get("username", "User"),
                session_state_data=st.session_state.to_dict(),
                cur_timestamp=st.session_state.cur_timestamp,
                source_page="career_transition",
                role=st.session_state.ct_data.get("target_role", "Unknown Role")
            )
            logger.info("Saved chat history on navigation back (results were displayed)")
        else:
            logger.info("No chat history to save on navigation back (results were not displayed)")
        # Clear specific states for this page
        if 'ct_state' in st.session_state: del st.session_state.ct_state
        if 'ct_messages' in st.session_state: del st.session_state.ct_messages
        if 'ct_data' in st.session_state: del st.session_state.ct_data
        if 'results_displayed' in st.session_state: del st.session_state.results_displayed
        if 'cur_timestamp' in st.session_state: del st.session_state.cur_timestamp
        logger.info("Navigating back to Guidance Hub, resetting CT state.")
        st.rerun()

    # Add extra padding at the top
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.header("🚀 Career Transition Assistant")

    # Add expandable debug section
    with st.expander("Diagnostic Information (Click to expand)"):
        debug_container = st.container()

    # Apply custom CSS (Handled globally in main.py)
    # Removed CSS block
    # Optionally display session state for debugging
    debug_container.json(st.session_state.to_dict())

    # Initialize session state variables
    if "ct_state" not in st.session_state:
        st.session_state.ct_state = "ask_name"
        st.session_state.ct_messages = []
        st.session_state.ct_data = {}
        st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Initialized career transition session state.")

    # Helper function to add messages to the chat
    def add_message(role, content):
        # Ensure messages list exists
        if "ct_messages" not in st.session_state: st.session_state.ct_messages = []
        st.session_state.ct_messages.append({"role": role, "content": content})
        logger.debug(f"Added CT message: {role} - {content[:50]}...") # Optional debug log

    # Display chat history
    if "ct_messages" in st.session_state:
        for msg in st.session_state.ct_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # === State Machine ===
    current_ct_state = st.session_state.get("ct_state", "ask_name")

    # --- Ask Name --- #
    if current_ct_state == "ask_name":
        logger.info("Inside 'ask_name' state block.")
        # Check if messages list exists and is empty
        if not st.session_state.get("ct_messages", []):
            add_message("assistant", "👋 Hello! I'll help you transition to a new career based on your resume. What's your name?")
            logger.info("Added initial CT welcome message.")
            # Rerun needed ONLY to display the very first message
            st.rerun()

        user_input = st.chat_input("Your name", key="ct_user_input") # Added key
        if user_input:
            logger.info(f"Received name input: {user_input}")
            st.session_state.ct_data["name"] = user_input
            add_message("user", user_input)
            add_message("assistant", f"Nice to meet you, {user_input}! Please upload your resume so I can analyze your current skills.")
            st.session_state.ct_state = "ask_resume"
            logger.info(f"User name set: {user_input}. Updated ct_state to 'ask_resume'. Preparing to rerun.")
            st.rerun()

    # --- Ask Resume --- #
    elif current_ct_state == "ask_resume":
        logger.info("Inside 'ask_resume' state block.")
        uploaded_file = st.file_uploader("Upload your resume (PDF/DOCX):", type=["pdf", "docx"], key="ct_resume_uploader") # Unique key
        if uploaded_file:
            with st.spinner("Analyzing your resume..."):
                try:
                    # Use the API function instead of direct call
                    resume_text = extract_resume_text_api(uploaded_file)
                    if not resume_text or len(resume_text) < 50:
                        add_message("assistant", "⚠️ I couldn't extract enough text from your resume. Please try uploading a different file.")
                        logger.warning(f"Insufficient text extracted from {uploaded_file.name}")
                        st.rerun()

                    st.session_state.ct_data["resume_text"] = resume_text
                    logger.info("Resume text extracted.")

                    try:
                        # Use the API function instead of direct call
                        extracted_skills = extract_skills_api(resume_text)
                        logger.info("Skills extracted using API.")
                    except Exception as e:
                        logger.warning(f"API skill extraction failed: {e}. Falling back to regex.")
                        # Use the regex API function as fallback
                        extracted_skills = extract_skills_regex_api(resume_text)
                        logger.info("Skills extracted using regex API fallback.")

                    st.session_state.ct_data["extracted_skills"] = extracted_skills
                    add_message("user", f"*Uploaded resume: {uploaded_file.name}*")
                    skills_list = "\n".join([f"- {skill}" for skill in extracted_skills])
                    add_message("assistant", f"I've analyzed your resume and identified these skills:\n\n{skills_list}\n\nWhat career would you like to transition to?")
                    st.session_state.ct_state = "ask_target_role"
                    logger.info(f"Resume processed, {len(extracted_skills)} skills found. Moving to ask_target_role state.")
                    st.rerun()

                except Exception as e:
                    logger.error(f"Error processing resume: {str(e)}", exc_info=True)
                    debug_container.error(f"Error processing resume: {str(e)}")
                    add_message("assistant", "⚠️ There was an error processing your resume. Please try again with a different file format.")
                    st.rerun()

    # --- Ask Target Role --- #
    elif current_ct_state == "ask_target_role":
        logger.info("Inside 'ask_target_role' state block.")
        user_input = st.chat_input("E.g., Data Scientist, Software Engineer", key="ct_target_role_input") # Added key
        if user_input:
            target_role = user_input.strip()
            st.session_state.ct_data["target_role"] = target_role
            add_message("user", target_role)
            add_message("assistant", f"Thanks! I'll now analyze the skill gaps between your current profile and the requirements for a {target_role} role. This will take a moment...")
            logger.info(f"Target role set: {target_role}. Moving to analyze_skills state.")

            # Store data in the resume database (optional step before analysis)
            try:
                with st.spinner("Storing initial career data..."):
                    name = st.session_state.ct_data["name"]
                    resume_text = st.session_state.ct_data["resume_text"]
                    extracted_skills = st.session_state.ct_data["extracted_skills"]

                    # Use the ResumeSearchService from database.py for storage
                    # NOTE: Decide if storing here is necessary or if it should happen after analysis
                    # If using create_resumes_table, ensure it has a method like store_initial_resume
                    # or adapt store_career_analysis to handle potentially missing fields.
                    # For now, we assume store_career_analysis can handle this or we skip initial storage.
                    # Example using a hypothetical method:
                    # service = create_resumes_table()
                    # service.store_initial_resume(name, resume_text, extracted_skills, target_role)
                    debug_container.info("Skipping initial resume storage for now.") # Adjusted log
                    logger.info("Skipping initial resume data storage before full analysis.")
            except Exception as e:
                logger.error(f"Error during placeholder initial resume storage: {str(e)}", exc_info=True)
                debug_container.warning(f"Could not store initial resume data (placeholder): {str(e)}")
                # Continue analysis despite storage error

            st.session_state.ct_state = "analyze_skills"
            st.rerun()

    # --- Analyze Skills --- #
    elif current_ct_state == "analyze_skills":
        logger.info("Inside 'analyze_skills' state block.")
        # Prevent re-analysis on page refresh if already done
        if "missing_skills" not in st.session_state.ct_data:
            # Check if the 'Analyzing...' message needs to be added (avoid duplication)
            last_msg_role = st.session_state.ct_messages[-1]["role"] if st.session_state.get("ct_messages") else None
            if last_msg_role == "user": # Only add if the last message was the user setting the role
                 add_message("assistant", f"Analyzing skill gaps for {st.session_state.ct_data.get('target_role', 'the target role')}...")
                 st.rerun() # Rerun to show the message before the spinner starts

            with st.spinner("Analyzing skill gaps and generating recommendations..."):
                try:
                    name = st.session_state.ct_data["name"]
                    resume_text = st.session_state.ct_data["resume_text"]
                    extracted_skills = st.session_state.ct_data["extracted_skills"]
                    target_role = st.session_state.ct_data["target_role"]
                    logger.info(f"Starting skill analysis for {name} -> {target_role}.")

                    skill_progress = st.progress(0.0, text="Identifying missing skills...")
                    debug_container.write("Identifying missing skills...")
                    # Use the API function instead of direct call
                    missing_skills = process_missing_skills_api(extracted_skills, target_role)
                    st.session_state.ct_data["missing_skills"] = missing_skills
                    debug_container.success(f"Identified {len(missing_skills)} missing skills: {missing_skills}")
                    logger.info(f"Identified {len(missing_skills)} missing skills.")

                    skill_progress.progress(0.3, text="Storing analysis results...")
                    debug_container.write("Storing career analysis data...")
                    # Use the API function instead of direct call
                    try:
                        resume_id = store_career_analysis_api(
                            username=name,
                            resume_text=resume_text,
                            extracted_skills=extracted_skills,
                            target_role=target_role,
                            missing_skills=missing_skills
                        )
                        st.session_state.ct_data["resume_id"] = resume_id
                        debug_container.success(f"Analysis stored with ID: {resume_id}")
                        logger.info(f"Analysis stored with ID: {resume_id}")
                    except Exception as e:
                        logger.error(f"Failed to store career analysis: {e}", exc_info=True)
                        debug_container.warning(f"Failed to store analysis: {e}")
                        st.session_state.ct_data["resume_id"] = None # Indicate storage failure

                    skill_progress.progress(0.6, text="Searching for relevant courses...")
                    debug_container.write("Getting course recommendations...")
                    try:
                        # Use the API function instead of direct call
                        courses_result = get_career_transition_courses_api(
                            target_role=target_role,
                            missing_skills=missing_skills
                        )
                        if courses_result and courses_result.get("count", 0) > 0:
                            courses_df = pd.DataFrame(courses_result["courses"])
                            debug_container.success(f"Found {len(courses_df)} course recommendations.")
                            logger.info(f"Found {len(courses_df)} courses.")
                            st.session_state.ct_data["courses"] = courses_df
                        else:
                            debug_container.warning("No courses found for missing skills.")
                            logger.warning("No courses found for missing skills.")
                            st.session_state.ct_data["courses"] = pd.DataFrame()
                    except Exception as e:
                        logger.error(f"Failed to get courses: {e}", exc_info=True)
                        debug_container.error(f"Failed to get courses: {e}")
                        st.session_state.ct_data["courses"] = pd.DataFrame()

                    skill_progress.progress(1.0, text="Analysis complete!")
                    add_message("assistant", f"I've analyzed your path to becoming a {target_role}!")
                    st.session_state.ct_state = "display_results"
                    logger.info("Skill analysis complete. Moving to display_results state.")
                    st.rerun()

                except Exception as e:
                    logger.error(f"Error during skill analysis phase: {str(e)}", exc_info=True)
                    debug_container.error(f"Error during skill analysis: {str(e)}")
                    add_message("assistant", "I encountered an error during analysis. Let's try setting the target role again.")
                    st.session_state.ct_state = "ask_target_role"
                    # Clean up potentially partial analysis data
                    if "missing_skills" in st.session_state.ct_data: del st.session_state.ct_data["missing_skills"]
                    if "courses" in st.session_state.ct_data: del st.session_state.ct_data["courses"]
                    if "resume_id" in st.session_state.ct_data: del st.session_state.ct_data["resume_id"]
                    st.rerun()
        else:
             # If analysis already done, just ensure we are in display state
             if st.session_state.ct_state != "display_results":
                 logger.info("Analysis already done, ensuring state is display_results.")
                 st.session_state.ct_state = "display_results"
                 st.rerun() # Rerun if state was wrong
             else:
                 logger.info("Analysis already done, state is correct (display_results).")

    # --- Display Results --- #
    elif current_ct_state == "display_results":
        logger.info("Inside 'display_results' state block.")
        if "results_displayed" not in st.session_state:
            logger.info("Displaying career transition results.")
            name = st.session_state.ct_data.get("name", "User")
            target_role = st.session_state.ct_data.get("target_role", "your target role")
            extracted_skills = st.session_state.ct_data.get("extracted_skills", [])
            missing_skills = st.session_state.ct_data.get("missing_skills", [])
            courses_df = st.session_state.ct_data.get("courses", pd.DataFrame())

            courses_list = []
            if not courses_df.empty:
                try:
                    # Ensure columns are suitable for to_dict('records')
                    # Example: Rename columns if they cause issues
                    # courses_df.columns = ['title', 'url', 'description']
                    courses_list = courses_df.to_dict('records')
                except Exception as e:
                    logger.error(f"Error converting courses DataFrame to dict: {e}")
                    debug_container.warning(f"Could not format course data for display: {e}")

            # Use formatting function for consistent UI
            try:
                # Use the API function instead of direct call
                transition_plan = format_transition_plan_api(
                    username=name,
                    current_skills=extracted_skills,
                    target_role=target_role,
                    missing_skills=missing_skills,
                    courses=courses_list
                )

                if transition_plan:
                    add_message("assistant", transition_plan.get("skill_assessment", ""))

                    if transition_plan.get("has_valid_courses", False):
                        full_message = transition_plan.get("introduction", "") + transition_plan.get("course_recommendations", "")
                        add_message("assistant", full_message)
                    else:
                        add_message("assistant", transition_plan.get("introduction", ""))
                        add_message("assistant", "I couldn't find specific courses for your skill gaps. Try searching for courses related to the skills mentioned above on platforms like Coursera, Udemy, or LinkedIn Learning.")
                        logger.warning("No valid courses found for transition plan display.")

                    add_message("assistant", transition_plan.get("career_advice", ""))
                else:
                    # Fallback to direct formatting if API fails
                    transition_plan = format_transition_plan(
                        username=name,
                        current_skills=extracted_skills,
                        target_role=target_role,
                        missing_skills=missing_skills,
                        courses=courses_list
                    )
                    
                    add_message("assistant", transition_plan["skill_assessment"])

                    if transition_plan["has_valid_courses"]:
                        full_message = transition_plan["introduction"] + transition_plan["course_recommendations"]
                        add_message("assistant", full_message)
                    else:
                        add_message("assistant", transition_plan["introduction"])
                        add_message("assistant", "I couldn't find specific courses for your skill gaps. Try searching for courses related to the skills mentioned above on platforms like Coursera, Udemy, or LinkedIn Learning.")
                        logger.warning("No valid courses found for transition plan display.")

                    add_message("assistant", transition_plan["career_advice"])

            except Exception as e:
                 logger.error(f"Error formatting transition plan: {e}", exc_info=True)
                 debug_container.error(f"Error formatting results: {e}")
                 # Display raw data as fallback
                 add_message("assistant", f"**Skill Assessment:**\nCurrent Skills: {json.dumps(extracted_skills)}\nMissing Skills for {target_role}: {json.dumps(missing_skills)}")
                 if not courses_df.empty:
                     try:
                         add_message("assistant", f"**Course Recommendations:**\n{courses_df.to_string()}")
                     except Exception as df_e:
                         add_message("assistant", f"**Course Recommendations:** Could not display DataFrame: {df_e}")
                         logger.error(f"Could not display courses DataFrame: {df_e}")
                 else:
                     add_message("assistant", "No specific courses found.")
                 add_message("assistant", "Focus on bridging the identified skill gaps through projects and learning.")

            st.session_state.results_displayed = True
            st.rerun() # Rerun once to display all messages

        # Handle follow-up questions
        user_input = st.chat_input("Ask a question about your career transition plan or type 'restart' to begin again", key="ct_followup_input") # Added key
        if user_input:
            add_message("user", user_input)
            logger.info(f"User asked follow-up question: {user_input}")

            # Check if user wants to restart
            if user_input.lower() in ['restart', 'start over', 'reset']:
                add_message("assistant", "Let's start fresh with a new career transition analysis!")
                # Save chat history before resetting
                if st.session_state.get('results_displayed', False):
                    save_session_state_api(
                        user_name=st.session_state.get("username", "User"),
                        session_state_data=st.session_state.to_dict(),
                        cur_timestamp=st.session_state.cur_timestamp,
                        source_page="career_transition",
                        role=st.session_state.ct_data.get("target_role", "Unknown Role")
                    )
                    logger.info("Saved chat history on restart via chat (results were displayed)")
                # Reset session state
                st.session_state.ct_state = "ask_name"
                st.session_state.ct_messages = []
                st.session_state.ct_data = {}
                st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                if "results_displayed" in st.session_state:
                    del st.session_state.results_displayed
                st.rerun()

            with st.spinner("Thinking..."):
                try:
                    # Create context for the chat service
                    user_context = {
                        'name': st.session_state.ct_data.get('name', 'User'),
                        'target_role': st.session_state.ct_data.get('target_role', 'Unknown'),
                        'skills': list(st.session_state.ct_data.get('missing_skills', {})),
                        'chat_history': st.session_state.ct_messages
                        # Optionally add course info if relevant to context
                        # 'courses': st.session_state.lp_data.get("courses", pd.DataFrame()).to_dict('records')
                    }

                    # Use API instead of direct function call
                    followup_response = answer_career_question_api(user_input, user_context)
                    add_message("assistant", followup_response)
                    logger.info("Generated follow-up response.")
                except Exception as e:
                    logger.error(f"Error generating follow-up response: {str(e)}", exc_info=True)
                    debug_container.error(f"Error generating response: {str(e)}")
                    add_message("assistant", "I'm having trouble processing your question right now. Could you try asking in a different way or focusing on the provided path?")

            st.rerun() # Rerun to display the new messages

    # --- Fallback for unexpected state --- #
    else:
        logger.error(f"Reached unexpected career transition state: {current_ct_state}")
        st.error("Something went wrong. Resetting career transition conversation.")
        # Reset state
        st.session_state.ct_state = "ask_name"
        st.session_state.ct_messages = []
        st.session_state.ct_data = {}
        st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if "results_displayed" in st.session_state:
            del st.session_state.results_displayed
        st.rerun()

    # --- Sidebar Actions ---
    st.sidebar.divider()
    st.sidebar.header("Chat Controls")
    if st.sidebar.button("🔄 Restart Analysis"):
        logger.info("User initiated career transition reset from sidebar button.")
        # Save chat history before resetting
        if len(st.session_state.get("ct_messages", [])) > 0 and st.session_state.get('results_displayed', False):
            save_session_state_api(
                user_name=st.session_state.get("username", "User"),
                session_state_data=st.session_state.to_dict(),
                cur_timestamp=st.session_state.cur_timestamp,
                source_page="career_transition",
                role=st.session_state.ct_data.get("target_role", "Unknown Role")
            )
            logger.info("Saved chat history on sidebar restart (results were displayed)")
        # Reset chat state
        st.session_state.ct_state = "ask_name"
        st.session_state.ct_messages = []
        st.session_state.ct_data = {}
        st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if "results_displayed" in st.session_state:
            del st.session_state.results_displayed
        st.rerun()

    if st.sidebar.button("⏹️ End Chat"):
        logger.info("User clicked End Chat from sidebar button.")
        st.session_state.current_page = "Dashboard"
        # Save chat history
        if st.session_state.get('results_displayed', False):
            save_session_state_api(
                user_name=st.session_state.get("username", "User"),
                session_state_data=st.session_state.to_dict(),
                cur_timestamp=st.session_state.cur_timestamp,
                source_page="career_transition",
                role=st.session_state.ct_data.get("target_role", "Unknown Role")
            )
            logger.info("Saved chat history on end chat (results were displayed)")
        # Clear specific states for this page
        if 'ct_state' in st.session_state: del st.session_state.ct_state
        if 'ct_messages' in st.session_state: del st.session_state.ct_messages
        if 'ct_data' in st.session_state: del st.session_state.ct_data
        if 'results_displayed' in st.session_state: del st.session_state.results_displayed
        if 'cur_timestamp' in st.session_state: del st.session_state.cur_timestamp
        logger.info("Navigating back to Guidance Hub, resetting CT state.")
        st.rerun()
