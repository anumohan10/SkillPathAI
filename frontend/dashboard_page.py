import streamlit as st
import json
import requests
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Configure logging with a rotating file handler
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
log_file = 'logs/dashboard.log'

# Create a handler that rotates log files when they reach 1MB
file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Get logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Remove any duplicate handlers
for handler in logger.handlers[:]:
    if isinstance(handler, logging.FileHandler) and handler != file_handler:
        logger.removeHandler(handler)

FASTAPI_BASE_URL = os.environ.get("API_URL", "http://backend:8000")

def generate_chat_preview(chat_list):
    """
    Generate a preview string from chat data, handling different data structures.
    
    Args:
        chat_list: Can be a list or dictionary containing chat data
        
    Returns:
        str: A preview string of at most 80 characters
    """
    try:
        if isinstance(chat_list, list) and chat_list:
            # Handle list-type chat history
            preview = chat_list[-1]["content"][:80] + "..."
        elif isinstance(chat_list, dict):
            # Handle dictionary-type chat history
            # Look for message-related keys in the dictionary
            if 'ct_messages' in chat_list and isinstance(chat_list['ct_messages'], list) and chat_list['ct_messages']:
                # For career transition messages
                preview = chat_list['ct_messages'][-1]["content"][:80] + "..."
            elif 'lp_messages' in chat_list and isinstance(chat_list['lp_messages'], list) and chat_list['lp_messages']:
                # For learning path messages
                preview = chat_list['lp_messages'][-1]["content"][:80] + "..."
            else:
                # If can't find specific message arrays, look for any descriptive content
                preview_candidates = []
                for key, value in chat_list.items():
                    if isinstance(value, str) and len(value) > 10:
                        preview_candidates.append(value[:80] + "...")
                    
                if preview_candidates:
                    preview = preview_candidates[0]  # Take the first substantial string value
                else:
                    # Fallback to session state details
                    preview = f"Session: {chat_list.get('current_page', 'Unknown')} ({len(chat_list)} values)"
        else:
            preview = "(empty or invalid chat data)"
        
        logger.debug(f"Created preview: {preview[:30]}...")
        return preview
    except Exception as e:
        logger.error(f"Error creating preview: {str(e)}")
        return f"(preview error: {str(e)})"

def fetch_recent_chats(user_name, limit=5):
    logger.info(f"Fetching recent chats for user: {user_name}, limit: {limit}")
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/user-input/chat-history/recent",
            params={"user_name": user_name, "limit": limit}
        )

        logger.debug(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            chats = response.json()
            logger.info(f"Successfully fetched {len(chats)} chat records")
            return chats
        else:
            logger.error(f"Failed to fetch chat history: Status {response.status_code}, Response: {response.text}")
            st.error(f"❌ Failed to fetch chat history: {response.text}")
            return []
    except Exception as e:
        logger.exception(f"API error when fetching chats: {str(e)}")
        st.error(f"🚨 API error: {str(e)}")
        return []

def clean_selected_chat(user_name, timestamp):
    logger.info(f"Cleaning chat for user: {user_name}, timestamp: {timestamp}")
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/user-input/chat-history/clean",
            json={"user_name": user_name, "timestamp": timestamp}
        )

        if response.status_code == 200:
            logger.info(f"Chat history cleaned successfully")
            return True
        else:
            logger.error(f"Failed to clean chat history: Status {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logger.exception(f"API error when cleaning chat: {str(e)}")
        return False

def render_dashboard_page():
    logger.info("Rendering dashboard page")
    st.header("Dashboard")
    username = st.session_state.get("username", "Guest")
    st.write(f"Welcome, {username}!")
    
    with st.expander("Diagnostic Information (Click to expand)"):
        debug_container = st.container()
        debug_container.json(st.session_state.to_dict())
    
    st.subheader("🕓 Recent Chat History")
    
    recent_chats = fetch_recent_chats(username)
    
    if not recent_chats:
        logger.info("No chat history found for user")
        st.info("No chat history found.")
    else:
        # Add some CSS for card styling
        st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            height: 100%;
            background-color: transparent;
            border: none;
            text-align: left;
            padding: 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create a grid layout
        cols = st.columns(2)
        logger.info(f"Processing {len(recent_chats)} chat records")
        
        for i, record in enumerate(recent_chats):
            chat_list = record.get("state_data", [])
            timestamp = record.get("cur_timestamp", "")
            source = record.get("source_page", "unknown")
            role = record.get("role", "")
            
            logger.debug(f"Processing chat record {i+1}: source={source}, timestamp={timestamp}")
            
            # Parse chat list if needed
            if isinstance(chat_list, str):
                try:
                    chat_list = json.loads(chat_list)
                    logger.debug(f"Successfully parsed chat_list JSON for record {i+1}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error for chat record {i+1}: {str(e)}")
                    chat_list = []
            
            # Get preview using the new function
            preview = generate_chat_preview(chat_list)
            
            # Format information
            chat_title = source.replace('_', ' ').title()
            formatted_time = timestamp[:19].replace('T', ' ') if timestamp else ""
            
            # Select column
            col = cols[i % 2]
            
            # Create a nice card using Streamlit's containers
            with col:
                chat_container = st.container(border=True)
                with chat_container:
                    st.markdown(f"### 🗨️ {chat_title} Chat")
                    st.caption(f"**Time:** {formatted_time} | **Role:** {role}")
                    st.markdown("---")
                    st.markdown(f"*{preview}*")
                    
                    # Create a "View Chat" button that fills the container
                    button_key = f"chat_{i}"
                    if st.button(f"Open Chat", key=button_key):
                        logger.info(f"User clicked to open chat: {button_key}, source={source}")
                        if source == "career_transition":
                            success = clean_selected_chat(username, timestamp)
                            if success:
                                logger.info("Successfully cleaned career transition chat")
                            filtered_chat_list = {k: v for k, v in chat_list.items() if k not in ("main_nav", "ct_followup_input")}
                            # st.session_state.clear()
                            st.session_state.update(filtered_chat_list)
                            now = datetime.now()
                            st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.ct_state = "display_results"
                            st.session_state.current_page = "Career Transition"
                            logger.info("Updated session state for career transition page")
                        elif source == "learning_path":
                            success = clean_selected_chat(username, timestamp)
                            if success:
                                logger.info("Successfully cleaned learning path chat")
                            filtered_chat_list = {k: v for k, v in chat_list.items() if k not in ("main_nav", "lp_followup_input")}
                            st.session_state.update(filtered_chat_list)
                            now = datetime.now()
                            st.session_state.cur_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.lp_state = "display_results"
                            st.session_state.current_page = "Learning Path"
                            logger.info("Updated session state for learning path page")
                        st.session_state.results_displayed = True
                        st.session_state.chat_resumed = True
                        logger.info(f"Rerunning app to navigate to {st.session_state.current_page}")
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
    
    logger.info("Dashboard page rendering complete")