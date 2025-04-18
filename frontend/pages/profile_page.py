# frontend/pages/profile_page.py
import streamlit as st

def render_profile_page():
    st.header("Profile")

    # Initialize state for editing if not present
    if "profile_edit" not in st.session_state:
        st.session_state.profile_edit = False

    # User info in a card
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        with col1:
            # Placeholder image
            st.image("https://via.placeholder.com/150", width=150)
        with col2:
            st.write(f"## {st.session_state.get('username', 'Guest')}")
            # Replace with dynamic data later
            st.write("Member since: January 2023")
            st.write("Career Goal: Data Scientist")
        st.markdown('</div>', unsafe_allow_html=True)

    # Skills in a card
    with st.container():
        st.markdown('<div class="container-card" style="margin-top: 20px;">', unsafe_allow_html=True) # Added margin
        st.subheader("Your Skills (Placeholder)")
        # Replace with dynamic skill data later
        skills = {
            "Technical Skills": ["Python", "SQL", "Data Analysis", "Pandas", "Matplotlib"],
            "Soft Skills": ["Communication", "Teamwork", "Problem Solving"],
            "Industry Knowledge": ["Healthcare", "Finance"]
        }
        for category, skill_list in skills.items():
            st.write(f"**{category}:**")
            st.write(", ".join(skill_list))
        st.markdown('</div>', unsafe_allow_html=True)

    # Edit profile button and form section
    if not st.session_state.profile_edit:
        if st.button("Edit Profile"):
            st.session_state.profile_edit = True
            st.rerun() # Rerun to show the form

    if st.session_state.profile_edit:
        with st.container():
            st.markdown('<div class="container-card" style="margin-top: 20px;">', unsafe_allow_html=True) # Added margin
            st.subheader("Edit Profile Details")
            with st.form("profile_form"):
                # Add fields to edit (e.g., name, goal, skills)
                name = st.text_input("Full Name", value=st.session_state.get('username', ''))
                email = st.text_input("Email", value="test@example.com") # Placeholder email
                career_goal = st.text_input("Career Goal", value="Data Scientist") # Placeholder
                # Add more fields as needed

                col_save, col_cancel = st.columns(2)
                with col_save:
                    submitted = st.form_submit_button("Save Changes")
                with col_cancel:
                     cancelled = st.form_submit_button("Cancel", type="secondary")

                if submitted:
                    # Add logic to save changes here (e.g., update database/user file)
                    st.session_state['username'] = name # Example update
                    # Potentially update email, career_goal etc. in users.json or database
                    st.success("Profile updated successfully!")
                    st.session_state.profile_edit = False
                    st.rerun() # Rerun to hide form and show updated info

                if cancelled:
                    st.session_state.profile_edit = False
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True) 