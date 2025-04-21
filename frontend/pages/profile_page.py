import os
import streamlit as st
from backend.services.auth_service import get_user_profile_by_username

def render_profile_page():
    st.header("Profile")

    # Retrieve user details from the database using the logged-in username
    username = st.session_state.get("username")
    user_details = get_user_profile_by_username(username)

    if not user_details:
        st.error("User details could not be loaded.")
        return

    # Display user info
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            img_path = os.path.join(os.path.dirname(__file__), "..", "assets", "user_profile.png")
            st.image(img_path, width=180)
        with col2:
            st.write(f"### {user_details['name']}")
            st.write(f"**Username:** {user_details['username']}")
            st.write(f"**Email:** {user_details['email']}")
        st.markdown('</div>', unsafe_allow_html=True)
