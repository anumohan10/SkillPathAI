# frontend/components/career_chat.py

import streamlit as st
from typing import List, Dict, Any, Optional
import time

class CareerChat:
    """
    A reusable chat component for career transitions.
    """
    def __init__(self, key_prefix: str = "career_chat"):
        """Initialize the chat component with session state."""
        self.key_prefix = key_prefix
        
        # Initialize session state if not present
        if f"{self.key_prefix}_messages" not in st.session_state:
            st.session_state[f"{self.key_prefix}_messages"] = []
        
        if f"{self.key_prefix}_state" not in st.session_state:
            st.session_state[f"{self.key_prefix}_state"] = "initial"
        
        # User data
        if f"{self.key_prefix}_user_data" not in st.session_state:
            st.session_state[f"{self.key_prefix}_user_data"] = {}
    
    def _get_messages(self) -> List[Dict[str, Any]]:
        """Get chat messages from session state."""
        return st.session_state[f"{self.key_prefix}_messages"]
    
    def _add_message(self, role: str, content: str, avatar: Optional[str] = None):
        """Add a message to the chat history."""
        message = {"role": role, "content": content}
        if avatar:
            message["avatar"] = avatar
        
        st.session_state[f"{self.key_prefix}_messages"].append(message)
    
    def _get_state(self) -> str:
        """Get current chat state."""
        return st.session_state[f"{self.key_prefix}_state"]
    
    def _set_state(self, state: str):
        """Set chat state."""
        st.session_state[f"{self.key_prefix}_state"] = state
    
    def _get_user_data(self) -> Dict[str, Any]:
        """Get user data from session state."""
        return st.session_state[f"{self.key_prefix}_user_data"]
    
    def _set_user_data(self, key: str, value: Any):
        """Set user data in session state."""
        st.session_state[f"{self.key_prefix}_user_data"][key] = value
    
    def _clear_chat(self):
        """Clear chat history and reset state."""
        st.session_state[f"{self.key_prefix}_messages"] = []
        st.session_state[f"{self.key_prefix}_state"] = "initial"
        st.session_state[f"{self.key_prefix}_user_data"] = {}
    
    def render_messages(self):
        """Render all messages in the chat."""
        for message in self._get_messages():
            with st.chat_message(message["role"], avatar=message.get("avatar")):
                st.markdown(message["content"])
    
    def assistant_message(self, content: str, delay: bool = False):
        """Add and display an assistant message with optional typing delay."""
        if delay:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Simulate typing
                for chunk in content.split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            
            # Add to history after animation
            self._add_message("assistant", content)
        else:
            # Add to history first
            self._add_message("assistant", content)
            
            # Then display
            with st.chat_message("assistant"):
                st.markdown(content)
    
    def user_message(self, content: str):
        """Add and display a user message."""
        self._add_message("user", content)
        with st.chat_message("user"):
            st.markdown(content)
    
    def text_input(self, prompt: str, key: Optional[str] = None) -> str:
        """Display a text input for user and capture the response."""
        input_key = f"{self.key_prefix}_{key or 'input'}"
        return st.chat_input(prompt, key=input_key)
    
    def file_uploader(self, label: str, types: List[str], key: Optional[str] = None):
        """Display a file uploader and capture the file."""
        upload_key = f"{self.key_prefix}_{key or 'uploader'}"
        return st.file_uploader(label, type=types, key=upload_key)
    
    def button(self, label: str, key: Optional[str] = None) -> bool:
        """Display a button and return if it was clicked."""
        button_key = f"{self.key_prefix}_{key or 'button'}"
        return st.button(label, key=button_key)
    
    def reset_chat(self):
        """Reset the chat with a confirmation."""
        if st.button("Start New Conversation", key=f"{self.key_prefix}_reset"):
            self._clear_chat()
            st.rerun()