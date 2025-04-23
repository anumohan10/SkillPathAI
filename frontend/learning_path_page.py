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
from frontend.ui_service import format_course_message, format_introduction, format_career_advice, format_skills_for_display

# Set up logging (consider moving configuration to a central place)
logging.basicConfig(
    level=logging.INFO, # Changed default level to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("learning_path_debug.log", mode='a'), # Append mode
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__) # Use __name__ for logger
now = datetime.now()

# Define API URL - should be configurable in production
API_URL = "http://localhost:8000"

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
    """Save session state to the database."""
    try:
        
        session_state_json = json.dumps(session_state_data, cls=CustomJSONEncoder)
        # Call the API endpoint to save session state
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
            logger.info("Chat/session data saved successfully")
        else:
            logger.error(f"Failed to save chat/session data: {response.status_code} | {response.text}")
    except Exception as e:
        logger.error(f"Error saving chat/session data: {str(e)}", exc_info=True)

def get_top_skills_for_role_api(target_role):
    """Call the API to get top skills for a role."""
    try:
        # Call the API endpoint to get top skills
        response = requests.get(
            f"http://localhost:8000/recommendations/skills/top/{target_role}"
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success", False):
                logger.info(f"Successfully retrieved {len(data['skills'])} skills for {target_role}")
                return data["skills"]
            else:
                logger.warning(f"API returned no skills for role {target_role}: {data.get('message')}")
                return []
        else:
            logger.error(f"API error getting skills for {target_role}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error calling skills API: {str(e)}", exc_info=True)
        return []

def get_course_recommendations_api(target_role, user_id=None):
    """Call the API to get course recommendations for a role."""
    try:
        # Call the API endpoint to get course recommendations
        response = requests.post(
            f"http://localhost:8000/recommendations/courses",
            json={"role": target_role, "user_id": user_id, "limit": 5}
        )
        if response.status_code == 200:
            # Get the raw response
            courses = response.json()
            
            # Log the raw response structure
            logger.info(f"API returned courses data type: {type(courses)}")
            logger.info(f"API response first item structure: {str(courses)[:200]}...")
            
            # Return raw response for more flexible handling
            return courses
        else:
            # Try to get more detailed error info
            error_msg = f"API error getting courses: {response.status_code}"
            try:
                error_details = response.json()
                error_msg += f" - {error_details.get('detail', 'No details')}"
            except:
                error_msg += f" - {response.text[:100]}"
            
            logger.error(error_msg)
            return []
    except Exception as e:
        logger.error(f"Error calling courses API: {str(e)}", exc_info=True)
        return []

def store_skill_ratings_api(learning_path_data):
    """Call the API to store learning path data."""
    try:
        # Prepare data for API call
        api_data = {
            "name": learning_path_data.get("name", "Unknown"),
            "target_role": learning_path_data.get("target_role", "Unknown Role"),
            "top_skills": learning_path_data.get("top_skills", []),
            "skill_ratings": learning_path_data.get("skill_ratings", {})
        }
        
        # # If courses exist and it's a DataFrame, convert to dict
        # courses = learning_path_data.get("courses")
        # if isinstance(courses, pd.DataFrame) and not courses.empty:
        #     api_data["courses"] = courses.to_dict('records')
        
        # Call the API endpoint
        response = requests.post(
            "http://localhost:8000/user-input/skill-ratings/store",
            json=api_data
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                logger.info(f"Successfully stored learning path, record ID: {data.get('record_id')}")
                return data.get('record_id')
            else:
                logger.warning(f"Learning path API returned failure: {data.get('message')}")
                return None
        else:
            logger.error(f"API error storing learning path: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error calling learning path storage API: {str(e)}", exc_info=True)
        return None

def answer_career_question_api(question, user_context):
    """Call the API to get an answer to a career-related question."""
    try:
        # Prepare request data
        request_data = {
            "question": question,
            "user_context": user_context
        }
        
        # Call the API endpoint
        response = requests.post(
            "http://localhost:8000/user-input/career-question",
            json=request_data
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "I'm sorry, I couldn't find an answer.")
        else:
            # Extract error message from response if possible
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", "Unknown error")
                logger.error(f"API error ({response.status_code}): {error_msg}")
                
                # For service unavailable errors, we can show a more specific message
                if response.status_code == 503:
                    return f"I'm having trouble with that question: {error_msg}"
                else:
                    return "I'm sorry, there was an error processing your question."
            except:
                logger.error(f"Failed to parse error response: {response.status_code}, {response.text}")
                return "I'm sorry, there was an error processing your question."
    except Exception as e:
        logger.error(f"Error calling career question API: {str(e)}", exc_info=True)
        return "I'm sorry, I'm having trouble connecting to the service right now."

def render_learning_path_page(): # Renamed function
    """Main function for the Learning Path chat feature with proper error handling."""

    # --- Log state at the beginning of each execution --- 
    logger.info(f"--- Entering render_learning_path_page ---")
    logger.info(f"Current lp_state: {st.session_state.get('lp_state', 'Not Set')}")
    logger.info(f"Current page: {st.session_state.get('current_page', 'Not Set')}")
    logger.info(f"LP Messages count: {len(st.session_state.get('lp_messages', []))}")
    logger.info(f"LP Data keys: {list(st.session_state.get('lp_data', {}).keys())}")
    # --- End Logging --- 
    # Add Back button
    if st.button("⬅️ Back to Guidance Hub"):
        st.session_state.current_page = "Guidance Hub"
        # Save chat history before clearing
        if 'lp_messages' in st.session_state and len(st.session_state.lp_messages) > 0 and st.session_state.get('results_displayed', False):
            # Get the target role from session state before clearing
            current_target_role = st.session_state.lp_data.get("target_role", "Unknown Role")
            save_session_state_api(
                user_name=st.session_state.get("username", "User"),
                session_state_data=st.session_state.to_dict(),
                cur_timestamp=st.session_state.cur_timestamp,
                source_page="learning_path",
                role=current_target_role
            )
            logger.info(f"Saved chat history on navigation back (results were displayed) for role {current_target_role}")
        else:
            logger.info("No chat history to save on navigation back (results were not displayed)")
        # Clear specific states for this page if needed when going back
        if 'lp_state' in st.session_state: del st.session_state.lp_state
        if 'lp_messages' in st.session_state: del st.session_state.lp_messages
        if 'lp_data' in st.session_state: del st.session_state.lp_data
        if 'results_displayed' in st.session_state: del st.session_state.results_displayed
        if 'cur_timestamp' in st.session_state: del st.session_state.cur_timestamp
        logger.info("Navigating back to Guidance Hub, resetting LP state.")
        st.rerun()

    # Add extra padding at the top
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True) # Reduced padding slightly
    st.header("🎯 Personalized Learning Path")

    # Add expandable debug section with more functionality
    with st.expander("Diagnostic Information (Click to expand)"):
        debug_container = st.container()
        
        # Add troubleshooting options
        debug_container.write("### Troubleshooting Tools")
        debug_col1, debug_col2 = debug_container.columns(2)
        
        with debug_col1:
            if st.button("Test API Connectivity"):
                try:
                    response = requests.get("http://localhost:8000/recommendations/health")
                    if response.status_code == 200:
                        debug_container.success("✅ API is accessible and returning 200 OK")
                    else:
                        debug_container.error(f"❌ API returned status code: {response.status_code}")
                except Exception as e:
                    debug_container.error(f"❌ Could not connect to API: {str(e)}")
        
        with debug_col2:
            if st.button("Test Course API"):
                try:
                    response = requests.post(
                        "http://localhost:8000/recommendations/courses",
                        json={"role": "Data Scientist", "limit": 1}
                    )
                    if response.status_code == 200:
                        courses = response.json()
                        if courses:
                            debug_container.success(f"✅ Received {len(courses)} courses from API")
                            debug_container.write(courses)
                        else:
                            debug_container.warning("⚠️ API returned empty course list")
                    else:
                        debug_container.error(f"❌ API returned status code: {response.status_code}")
                except Exception as e:
                    debug_container.error(f"❌ Could not get courses: {str(e)}")
        
        # Display current session state 
        debug_container.write("### Session State")
        debug_container.json(st.session_state.to_dict()) # Display full state as JSON
        
        # Add detailed data view
        debug_container.write("### Course Data")
        if "lp_data" in st.session_state and "courses" in st.session_state.lp_data:
            courses_df = st.session_state.lp_data["courses"]
            
            # Check if courses_df is actually a DataFrame
            if not isinstance(courses_df, pd.DataFrame):
                debug_container.warning(f"courses_df is not a DataFrame, it's a {type(courses_df)}. Converting for display...")
                try:
                    # Only convert for display, don't modify session state here
                    display_df = pd.DataFrame(courses_df)
                    debug_container.write(f"Converted DataFrame shape: {display_df.shape}")
                    debug_container.write(f"Columns: {list(display_df.columns)}")
                    debug_container.dataframe(display_df)
                except Exception as e:
                    debug_container.error(f"Error converting to DataFrame: {str(e)}")
                    debug_container.warning("Showing raw data instead:")
                    debug_container.write(courses_df)
            # Regular DataFrame case
            elif not courses_df.empty:
                debug_container.write(f"DataFrame shape: {courses_df.shape}")
                debug_container.write(f"Columns: {list(courses_df.columns)}")
                debug_container.dataframe(courses_df)
            else:
                debug_container.warning("Courses DataFrame is empty")
                
                # Show raw data if available
                if "raw_courses" in st.session_state.lp_data:
                    raw_courses = st.session_state.lp_data["raw_courses"]
                    if raw_courses:
                        debug_container.write("Raw courses data:")
                        debug_container.write(raw_courses)
                    else:
                        debug_container.warning("Raw courses data is empty")
        else:
            debug_container.warning("No course data in session state")

    # Initialize session state for the learning path conversation
    if "lp_state" not in st.session_state:
        st.session_state.lp_state = "ask_name"
        st.session_state.lp_messages = []
        st.session_state.lp_data = {}
        st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Initialized learning path session state.")
        # Don't rerun here, let the ask_name block handle the first message

    # Helper function to add messages to the chat
    def add_message(role, content):
        # Ensure messages list exists
        if "lp_messages" not in st.session_state: st.session_state.lp_messages = []
        st.session_state.lp_messages.append({"role": role, "content": content})
        # logger.debug(f"Added message: {role} - {content[:50]}...") # Optional debug log

    # Display chat history
    if "lp_messages" in st.session_state:
        for msg in st.session_state.lp_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # === State Machine for Learning Path ===

    # --- Ask Name --- #
    # Use .get() for safety, although we initialize above
    current_lp_state = st.session_state.get("lp_state", "ask_name") 

    if current_lp_state == "ask_name":
        logger.info("Inside 'ask_name' state block.")
        # Check if messages list exists and is empty
        if not st.session_state.get("lp_messages", []):
             add_message("assistant", "👋 Hello! I'll help you create a personalized learning path. What's your name?")
             logger.info("Added initial welcome message.")
             # Rerun needed ONLY to display the very first message before input is possible
             st.rerun()

        user_input = st.chat_input("Your name", key="lp_name_input") # Added key for stability
        if user_input:
            logger.info(f"Received name input: {user_input}")
            st.session_state.lp_data["name"] = user_input
            add_message("user", user_input)
            add_message("assistant", f"Nice to meet you, {user_input}! What career would you like to pursue? (e.g., Data Engineer, Data Scientist, Software Engineer)")
            st.session_state.lp_state = "ask_role" # <<< State updated here
            logger.info(f"User name set: {user_input}. Updated lp_state to 'ask_role'. Preparing to rerun.")
            logger.info(f"LP Messages count before rerun: {len(st.session_state.get('lp_messages', []))}")
            st.rerun() # <<< Rerun triggered here

    # --- Ask Target Role --- #
    elif current_lp_state == "ask_role":
        logger.info("Inside 'ask_role' state block.")
        user_input = st.chat_input("E.g., Data Engineer, Data Scientist", key="lp_role_input") # Added key
        if user_input:
            target_role = user_input.strip()
            st.session_state.lp_data["target_role"] = target_role
            add_message("user", target_role)
            logger.info(f"Target role set: {target_role}. Fetching skills.")

            # Create columns for better spinner placement
            skill_spinner_col1, skill_spinner_col2, skill_spinner_col3 = st.columns([1, 2, 1])
            with skill_spinner_col2:
                with st.spinner("🔍 Identifying key skills for this role..."):
                    st.info(f"Please wait while we analyze the skills needed for a {target_role} role...")
                    try:
                        top_skills = get_top_skills_for_role_api(target_role)
                        if not top_skills: # Handle case where no skills are found
                            logger.warning(f"No top skills found for role: {target_role}")
                            add_message("assistant", f"I couldn't find specific top skills for '{target_role}'. Let's try defining some key areas manually. What are 5 important skills or topics for this role?")
                            st.session_state.lp_state = "manual_skills"
                        else:
                            st.session_state.lp_data["top_skills"] = top_skills
                            st.session_state.lp_data["skill_ratings"] = {}
                            st.session_state.lp_data["current_skill_index"] = 0

                            skills_list = "\n".join([f"- {skill}" for skill in top_skills])
                            add_message("assistant", f"Great! For a **{target_role}** role, these are the top skills you'll need:\n\n{skills_list}\n\nLet's assess your current skill level in each area.")
                            st.session_state.lp_state = "rate_skills"
                            logger.info(f"Found {len(top_skills)} skills for {target_role}. Moving to rate_skills state.")

                    except Exception as e:
                        logger.error(f"Error getting skills for {target_role}: {str(e)}", exc_info=True)
                        debug_container.error(f"Error getting skills: {str(e)}")
                        add_message("assistant", "I'm having trouble identifying key skills for this role right now. Let me help you build a more general learning path instead. What specific areas are you interested in learning about? (Please list 5)")
                        st.session_state.lp_state = "manual_skills"
            st.rerun()

    # --- Manual Skills Entry --- #
    elif current_lp_state == "manual_skills":
        logger.info("Inside 'manual_skills' state block.")
        user_input = st.chat_input("Enter 5 skills or topics (comma-separated)", key="lp_manual_skills_input") # Added key
        if user_input:
            add_message("user", user_input)

            skills = [skill.strip() for skill in user_input.split(',') if skill.strip()]
            if len(skills) != 5:
                add_message("assistant", "Please enter exactly 5 skills or topics, separated by commas.")
                st.rerun()
            else:
                st.session_state.lp_data["top_skills"] = skills
                st.session_state.lp_data["skill_ratings"] = {}
                st.session_state.lp_data["current_skill_index"] = 0

                add_message("assistant", "Thanks! Let's rate your proficiency in each area.")
                st.session_state.lp_state = "rate_skills"
                logger.info(f"Received manual skills: {skills}. Moving to rate_skills state.")
                st.rerun()

    # --- Rate Skills (Loop) --- #
    elif current_lp_state == "rate_skills":
        logger.info("Inside 'rate_skills' state block.")
        skills = st.session_state.lp_data.get("top_skills", [])
        index = st.session_state.lp_data.get("current_skill_index", 0)

        if index < len(skills):
            current_skill = skills[index]
            # Check if message already exists to prevent duplicates on rerun
            last_msg_content = st.session_state.lp_messages[-1]["content"] if st.session_state.get("lp_messages") else ""
            prompt_text = f"How would you rate your proficiency in **{current_skill}** on a scale of 1-5?"
            # Avoid adding duplicate prompts if the state didn't advance properly
            if not last_msg_content.startswith(prompt_text.split("\n")[0]): # Check start of prompt
                 add_message("assistant", f"{prompt_text}\n\n1: No experience\n2: Basic knowledge\n3: Intermediate\n4: Advanced\n5: Expert")
                 logger.info(f"Asking for rating for skill: {current_skill}")
            st.session_state.lp_state = "wait_for_rating"
            st.rerun()
            # Do not rerun here, wait for user input via chat_input in the next state block
        else:
            # If all skills are rated, move to generating courses
            st.session_state.lp_state = "generate_courses"
            logger.info("All skills rated. Moving to generate_courses state.")
            st.rerun()

    # --- Wait for Rating --- #
    elif current_lp_state == "wait_for_rating":
        logger.info("Inside 'wait_for_rating' state block.")
        skills = st.session_state.lp_data.get("top_skills", [])
        index = st.session_state.lp_data.get("current_skill_index", 0)

        if index < len(skills):
            current_skill = skills[index]
            # Use a unique key for each skill rating input
            user_input = st.chat_input(f"Rate your {current_skill} skills (1-5)", key=f"lp_rating_{current_skill.replace(' ','_')}")
            if user_input:
                try:
                    rating = int(user_input.strip())
                    if 1 <= rating <= 5:
                        st.session_state.lp_data.setdefault("skill_ratings", {})[current_skill] = rating
                        add_message("user", f"{rating}")
                        logger.info(f"Skill '{current_skill}' rated: {rating}")

                        # Move to next skill
                        st.session_state.lp_data["current_skill_index"] = index + 1
                        st.session_state.lp_state = "rate_skills" # Go back to rating state to ask next or move on
                        st.rerun()
                    else:
                        add_message("assistant", "Please enter a valid rating between 1 and 5.")
                        st.rerun()
                except ValueError:
                    add_message("assistant", "Please enter a number between 1 and 5.")
                    st.rerun()
        else:
             logger.warning("Entered wait_for_rating state with invalid index or no skills. Resetting.")
             st.session_state.lp_state = "ask_role"
             st.rerun()

    # --- Generate Courses --- #
    elif current_lp_state == "generate_courses":
        logger.info("Inside 'generate_courses' state block.")
        # Check if courses already generated to prevent re-running on refresh
        if "courses" not in st.session_state.lp_data:
            # Check if messages list exists before adding
            if not st.session_state.get("lp_messages", []):
                add_message("assistant", "Preparing to generate learning path...") # Initial message if needed
            elif not st.session_state.lp_messages[-1]["content"].startswith("Thanks for the ratings!"):
                 add_message("assistant", "Thanks for the ratings! Now generating your personalized learning path...")
            
            # Display a spinner at the top of the page before doing processing
            spinner_col1, spinner_col2, spinner_col3 = st.columns([1, 2, 1])
            with spinner_col2:
                with st.spinner("🔍 Searching for the best courses for you..."):
                    st.info("Please wait while we find the perfect courses to help you build your skills. This may take a moment...")
                    
                    target_role = st.session_state.lp_data.get("target_role", "Unknown Role")
                    user_id = None # Placeholder for user ID if needed by course service

                    # Store the learning path data first (optional, depends on whether ID is needed for courses)
                    try:
                        debug_container.write("Storing learning path data...")
                        store_result = store_skill_ratings_api(st.session_state.lp_data)
                        if store_result:
                            debug_container.success("Learning path stored successfully")
                            # Get the ID from the stored data
                            user_id = store_result
                            debug_container.write(f"Using record ID: {user_id}")
                        else:
                            debug_container.warning("Learning path stored, but no ID returned.")
                            logger.warning("Learning path stored, but no ID returned.")
                    except Exception as e:
                        debug_container.error(f"Error saving learning path: {str(e)}")
                        logger.error(f"Error saving learning path: {str(e)}", exc_info=True)
                        user_id = None
                        # Continue without stored ID

                    # Get recommended courses
                    try:
                        debug_container.write("Fetching course recommendations...")
                        courses = get_course_recommendations_api(target_role, user_id)
                        
                        # First store the raw data for fallback
                        st.session_state.lp_data["raw_courses"] = courses
                        
                        # Check what we got from the API
                        if courses:
                            debug_container.success(f"Retrieved {len(courses)} course recommendations.")
                            logger.info(f"Retrieved {len(courses)} course recommendations for role '{target_role}'.")
                            logger.info(f"Courses data type: {type(courses)}")
                            
                            # Log detailed info about courses for each level category
                            level_counts = {}
                            for course in courses:
                                level = course.get('LEVEL_CATEGORY', 'UNKNOWN')
                                level_counts[level] = level_counts.get(level, 0) + 1
                            
                            logger.info(f"Course level distribution: {level_counts}")
                            logger.info(f"Full courses data: {json.dumps(courses)}")
                            
                            # Log the raw course data to debug
                            logger.info(f"Raw courses data sample: {str(courses[:1])[:200]}...")
                            
                            # Make sure we have a proper DataFrame
                            if isinstance(courses, pd.DataFrame):
                                courses_df = courses
                                logger.info("API returned courses as DataFrame directly")
                            else:
                                # Convert list of dicts to DataFrame
                                try:
                                    courses_df = pd.DataFrame(courses)
                                    logger.info(f"Successfully converted courses to DataFrame with shape {courses_df.shape}")
                                    logger.info(f"DataFrame columns: {list(courses_df.columns)}")
                                except Exception as e:
                                    logger.error(f"Error converting courses to DataFrame: {e}", exc_info=True)
                                    debug_container.error(f"Error converting to DataFrame: {str(e)}")
                                    # Create empty DataFrame as fallback
                                    courses_df = pd.DataFrame()
                        else:
                            logger.warning("API returned empty or null courses data")
                            debug_container.warning("No courses received from API")
                            courses_df = pd.DataFrame()  # Create empty DataFrame
                        
                        # Store in session state (even if empty)
                        st.session_state.lp_data["courses"] = courses_df
                    except Exception as e:
                        debug_container.error(f"Error retrieving courses: {str(e)}")
                        logger.error(f"Error retrieving courses for role '{target_role}': {str(e)}", exc_info=True)
                        st.session_state.lp_data["courses"] = pd.DataFrame() # Store empty DataFrame
                        add_message("assistant", "Sorry, I encountered an error while searching for courses. I can still provide general advice.")

            # Move to display state regardless of course fetching success
            st.session_state.lp_state = "display_results"
            logger.info("Course generation/fetch complete. Moving to display_results state.")
            st.rerun()
        else:
            # If courses are already generated, ensure we are in display state
            if st.session_state.lp_state != "display_results":
                logger.info("Courses already generated, ensuring state is display_results.")
                st.session_state.lp_state = "display_results"
                st.rerun() # Rerun if state was wrong
            else:
                logger.info("Courses already generated, state is correct (display_results).")

    # --- Display Results --- #
    elif current_lp_state == "display_results":
        logger.info("Inside 'display_results' state block.")
        if "results_displayed" not in st.session_state:
            # Show spinner while formatting results
            results_spinner_col1, results_spinner_col2, results_spinner_col3 = st.columns([1, 2, 1])
            with results_spinner_col2:
                with st.spinner("📊 Creating your personalized learning path..."):
                    st.info("Formatting your personalized learning path with courses tailored to your skill levels...")
                    
                    logger.info("Displaying learning path results for the first time.")
                    # Get personalized data
                    name = st.session_state.lp_data.get("name", "User")
                    target_role = st.session_state.lp_data.get("target_role", "your chosen role")
                    skill_ratings = st.session_state.lp_data.get("skill_ratings", {})
                    courses_df = st.session_state.lp_data.get("courses", pd.DataFrame())

                    # Add Skill Assessment section
                    skill_assessment = format_skills_for_display(skill_ratings)
                    add_message("assistant", skill_assessment)

                    # Format and display Intro + Course Recommendations
                    try:
                        intro = format_introduction(target_role, skill_ratings)
                        
                        # Debug what's in the session state
                        raw_courses = st.session_state.lp_data.get("raw_courses", [])
                        logger.info(f"Debug - raw_courses in session state: {len(raw_courses)} items")
                        
                        # Ensure courses_df is actually a DataFrame
                        if not isinstance(courses_df, pd.DataFrame):
                            logger.warning(f"courses_df is not a DataFrame, it's a {type(courses_df)}. Converting it now.")
                            try:
                                courses_df = pd.DataFrame(courses_df)
                                logger.info(f"Successfully converted to DataFrame with shape: {courses_df.shape}")
                            except Exception as e:
                                logger.error(f"Error converting courses_df to DataFrame: {str(e)}", exc_info=True)
                                courses_df = pd.DataFrame()  # Create empty DataFrame as fallback
                            
                            # Update the session state with the converted DataFrame
                            st.session_state.lp_data["courses"] = courses_df
                        
                        # Try with raw courses data if DataFrame is empty
                        if courses_df.empty and raw_courses:
                            logger.warning("courses_df is empty but raw_courses exists, trying direct use of raw data")
                            # Create a simplified course message directly from raw data
                            course_msg = "# 📋 Learning Path\n\n"
                            course_msg += "# 📚 Course Recommendations\n\n"
                            
                            for course in raw_courses:
                                course_name = course.get('COURSE_NAME', course.get('course_name', 'Unknown Course'))
                                course_url = course.get('URL', course.get('url', '#'))
                                course_description = course.get('DESCRIPTION', course.get('description', 'No description available'))
                                
                                course_msg += f"### {course_name}\n\n"
                                course_msg += f"**What you'll learn**:\n\n{course_description[:300]}...\n\n"
                                course_msg += f"**[➡️ Enroll in this course]({course_url})**\n\n"
                                course_msg += "---\n\n"
                            
                            has_valid_courses = bool(raw_courses)
                        else:
                            logger.info(f"Formatting courses with DataFrame of shape: {courses_df.shape}")
                            course_msg, has_valid_courses = format_course_message(courses_df, target_role)
                        
                        # Display with what we have
                        logger.info(f"Course formatting result: has_valid_courses={has_valid_courses}")
                        if has_valid_courses:
                            logger.info("Adding full message with courses to the chat")
                            full_message = intro + course_msg
                            add_message("assistant", full_message)
                        else:
                            logger.info("No valid courses, adding intro and error message separately")
                            add_message("assistant", intro) # Show intro even if no courses
                            add_message("assistant", "I couldn't find specific courses for your skill gaps. Consider searching for courses related to your rated skills on platforms like Coursera, Udemy, or LinkedIn Learning.")
                            logger.warning("No valid courses found to display.")
                            
                            # Added explicit debug for troubleshooting
                            debug_container.warning("⚠️ No courses could be displayed. Check the logs for details.")
                            debug_container.write(f"Raw courses data: {raw_courses}")
                            
                    except Exception as e:
                        logger.error(f"Error formatting courses for display: {str(e)}", exc_info=True)
                        # Ensure we at least show something in case of error
                        add_message("assistant", intro)
                        add_message("assistant", "I encountered an error while formatting your course recommendations. Please try again later.")
                        
                        # Add debug information to the debug container
                        debug_container.error(f"Error formatting courses: {str(e)}")
                        debug_container.write("Stack trace:", exc_info=True)

                    # Add Career Advice with LLM
                    career_advice = format_career_advice(target_role=target_role, skill_ratings=skill_ratings)
                    add_message("assistant", career_advice)

            # Mark results as displayed to prevent re-adding messages on rerun
            st.session_state.results_displayed = True
            st.rerun() # Rerun once to ensure all messages are shown

        # Handle follow-up questions
        user_input = st.chat_input("Ask a question about your learning path or type 'restart' to begin again", key="lp_followup_input")
        if user_input:
            add_message("user", user_input)
            
            # Check if user wants to restart
            if user_input.lower() in ['restart', 'start over', 'reset']:
                add_message("assistant", "Let's start fresh with a new learning path analysis!")
                # Simply reset the session state without saving
                st.session_state.lp_state = "ask_name"
                st.session_state.lp_messages = []
                st.session_state.lp_data = {}
                st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                if "results_displayed" in st.session_state:
                    del st.session_state.results_displayed
                logger.info("Reset learning path session for new analysis through chat interface")
                st.rerun()
            
            logger.info(f"User asked follow-up question: {user_input}")
            with st.spinner("Thinking..."):
                try:
                    # Create context for the chat service
                    user_context = {
                        'name': st.session_state.lp_data.get('name', 'User'),
                        'target_role': st.session_state.lp_data.get('target_role', 'Unknown'),
                        'skills': list(st.session_state.lp_data.get('skill_ratings', {}).keys()),
                        'chat_history': st.session_state.lp_messages
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
        logger.error(f"Reached unexpected learning path state: {current_lp_state}")
        st.error("Something went wrong. Resetting learning path conversation.")
        # Reset state
        st.session_state.lp_state = "ask_name"
        st.session_state.lp_messages = []
        st.session_state.lp_data = {}
        st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if "results_displayed" in st.session_state:
            del st.session_state.results_displayed
        st.rerun()

    # --- Sidebar Actions ---
    st.sidebar.divider()
    st.sidebar.header("Chat Controls")
    if st.sidebar.button("🔄 Restart Analysis"):
        logger.info("User initiated learning path reset from sidebar button.")
        # Simply reset the session state without saving
        st.session_state.lp_state = "ask_name"
        st.session_state.lp_messages = []
        st.session_state.lp_data = {}
        st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if "results_displayed" in st.session_state:
            del st.session_state.results_displayed
        logger.info("Reset learning path session for new analysis")
        st.rerun()
        
    if st.sidebar.button("⏹️ End Chat"):
        logger.info("User clicked End Chat from sidebar button.")
        st.session_state.current_page = "Dashboard"
        # Save chat history
        if st.session_state.get('results_displayed', False):
            # Get the target role from session state before clearing
            current_target_role = st.session_state.lp_data.get("target_role", "Unknown Role")
            save_session_state_api(
                user_name=st.session_state.get("username", "User"),
                session_state_data=st.session_state.to_dict(),
                cur_timestamp=st.session_state.cur_timestamp,
                source_page="learning_path",
                role=current_target_role
            )
            logger.info(f"Saved chat history on end chat (results were displayed) for role {current_target_role}")
        # Clear specific states for this page
        for key in ['lp_state', 'lp_messages', 'lp_data', 'results_displayed', 'cur_timestamp']:
            st.session_state.pop(key, None)
        st.session_state.current_page = "Dashboard"
        st.rerun() 