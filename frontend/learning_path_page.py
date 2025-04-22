import logging
import os
import sys
import json
import streamlit as st
import pandas as pd
from datetime import datetime

# Ensure backend services can be imported
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import backend services
from backend.services.learning_path_service import store_learning_path
from backend.services.skill_service import get_top_skills_for_role
from backend.services.course_service import get_course_recommendations
from frontend.ui_service import format_course_message, format_introduction, format_career_advice, format_skills_for_display
from backend.services.chat_service import ChatService
from backend.database import save_chat_history

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


def render_learning_path_page():
    """Main function for the Learning Path chat feature with proper error handling."""

    # --- Log state ---
    logger.info(f"--- Entering render_learning_path_page ---")
    logger.info(f"Current lp_state: {st.session_state.get('lp_state', 'Not Set')}")
    logger.info(f"Current page: {st.session_state.get('current_page', 'Not Set')}")
    logger.info(f"LP Messages count: {len(st.session_state.get('lp_messages', []))}")
    logger.info(f"LP Data keys: {list(st.session_state.get('lp_data', {}).keys())}")

    if st.session_state.get("chat_resumed", False):
        st.success("🔁 Resumed previous chat.")
        del st.session_state.chat_resumed

    # Convert JSON string to list of dicts if needed
    if "lp_messages" in st.session_state and isinstance(st.session_state.lp_messages, str):
        try:
            st.session_state.lp_messages = json.loads(st.session_state.lp_messages)
            logger.info("Deserialized lp_messages from JSON string.")
        except json.JSONDecodeError as e:
            st.error("Failed to load previous chat history.")
            logger.error(f"JSON parsing error in lp_messages: {e}")
            st.session_state.lp_messages = []
        
    # Add Back button
    if st.button("⬅️ Back to Guidance Hub"):
        st.session_state.current_page = "Guidance Hub"
        # Save chat history before clearing
        if 'lp_messages' in st.session_state and len(st.session_state.lp_messages) > 0 and st.session_state.get('results_displayed', False):
            save_chat_history(
                user_name=st.session_state.get("username", "User"),
                chat_history=json.dumps(st.session_state.lp_messages),
                cur_timestamp=st.session_state.cur_timestamp,
                source_page="learning_path"
            )
            logger.info("Saved chat history on navigation back (results were displayed)")
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

    # Add expandable debug section
    with st.expander("Diagnostic Information (Click to expand)"):
        debug_container = st.container()
        # Optionally display session state for debugging
        debug_container.json(st.session_state.to_dict()) # Display full state as JSON

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

            with st.spinner("Identifying key skills for this role..."):
                try:
                    top_skills = get_top_skills_for_role(target_role)
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
            
            with st.spinner("Searching for the best courses..."):
                target_role = st.session_state.lp_data.get("target_role", "Unknown Role")
                user_id = None # Placeholder for user ID if needed by course service

                # Store the learning path data first (optional, depends on whether ID is needed for courses)
                try:
                    debug_container.write("Storing learning path data...")
                    store_result = store_learning_path(st.session_state.lp_data)
                    if store_result:
                        # Store record_id back into session state if needed
                        debug_container.success("Learning path stored successfully")
                        # Get the ID from the stored data
                        user_id = st.session_state.lp_data.get("record_id")
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
                    courses_df = get_course_recommendations(target_role, user_id)
                    debug_container.success(f"Retrieved {len(courses_df)} course recommendations.")
                    logger.info(f"Retrieved {len(courses_df)} course recommendations for role '{target_role}'.")
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
            course_msg, has_valid_courses = format_course_message(courses_df, target_role)
            intro = format_introduction(target_role, skill_ratings)

            if has_valid_courses:
                full_message = intro + course_msg
                add_message("assistant", full_message)
            else:
                add_message("assistant", intro) # Show intro even if no courses
                add_message("assistant", course_msg) # Show the "no courses found" message
                logger.warning("No valid courses found to display.")

            # Add Career Advice
            career_advice = format_career_advice()
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
                # Save chat history before resetting
                if st.session_state.get('results_displayed', False):
                    save_chat_history(
                        user_name=st.session_state.get("username", "User"),
                        chat_history=json.dumps(st.session_state.lp_messages),
                        cur_timestamp=st.session_state.cur_timestamp,
                        source_page="learning_path"
                    )
                    logger.info("Saved chat history on restart via chat (results were displayed)")
                # Reset session state
                st.session_state.lp_state = "ask_name"
                st.session_state.lp_messages = []
                st.session_state.lp_data = {}
                st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                if "results_displayed" in st.session_state:
                    del st.session_state.results_displayed
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

                    chat_service = ChatService() # Initialize here or use session state
                    followup_response = chat_service.answer_career_question(user_input, user_context)
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
        # Save chat history before resetting
        if len(st.session_state.get("lp_messages", [])) > 0 and st.session_state.get('results_displayed', False):
            save_chat_history(
                user_name=st.session_state.get("username", "User"),
                chat_history=json.dumps(st.session_state.lp_messages),
                cur_timestamp=st.session_state.cur_timestamp,
                source_page="learning_path"
            )
            logger.info("Saved chat history on sidebar restart (results were displayed)")
        # Reset chat state
        st.session_state.lp_state = "ask_name"
        st.session_state.lp_messages = []
        st.session_state.lp_data = {}
        st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if "results_displayed" in st.session_state:
            del st.session_state.results_displayed
        st.rerun()
        
    # --- Sidebar: End Chat ---
st.sidebar.divider()
if st.sidebar.button("⏹️ End Chat"):
    logger.info("User clicked End Chat from sidebar button.")
    
    # Safely get the current timestamp if it exists, fallback if not
    cur_time = st.session_state.get("cur_timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Save chat history only if results were shown
    if st.session_state.get('results_displayed', False):
        try:
            save_chat_history(
                user_name=st.session_state.get("username", "User"),
                chat_history=json.dumps(st.session_state.get("lp_messages", [])),
                cur_timestamp=cur_time,
                source_page="learning_path"
            )
            logger.info("Saved chat history on end chat (results were displayed)")
        except Exception as e:
            logger.error(f"Error saving chat history: {e}", exc_info=True)

    # Clear session state keys related to Learning Path
    for key in ['lp_state', 'lp_messages', 'lp_data', 'results_displayed', 'cur_timestamp']:
        if key in st.session_state:
            del st.session_state[key]

    # Redirect user to Dashboard
    st.session_state.current_page = "Dashboard"
    logger.info("Navigated to Dashboard. LP state reset.")
    st.rerun()