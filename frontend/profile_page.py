import streamlit as st
import requests
import os

API_URL = "http://backend:8000"  # Replace with your backend URL

def render_profile_page():
    st.header("Profile")

    username = st.session_state.get("username")
    if not username:
        st.error("You're not logged in.")
        return

    try:
        response = requests.get(f"{API_URL}/auth/user-profile", params={"username": username})
        if response.status_code == 200:
            user_data = response.json()
        else:
            st.error("Failed to load profile.")
            return
    except Exception as e:
        st.error(f"API error: {str(e)}")
        return

    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            image_path = "frontend/assets/user_profile.png"
            if os.path.exists(image_path):
                st.image(image_path, width=150)
            else:
                st.warning("User image not found.")
        with col2:
            st.write(f"### {user_data['name']}")
            st.write(f"**Username:** {user_data['username']}")
            st.write(f"**Email:** {user_data['email']}")
        st.markdown('</div>', unsafe_allow_html=True)
