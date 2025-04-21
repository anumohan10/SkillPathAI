# frontend/pages/dashboard_page.py
import streamlit as st

def render_dashboard_page():
    st.header("Dashboard")
    st.write(f"Welcome, {st.session_state.get('username', 'Guest')}!")

    # User stats in a card
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            # Replace with dynamic data later
            st.metric("Skills Identified", "12")
        with col2:
            # Replace with dynamic data later
            st.metric("Learning Progress", "65%")
        with col3:
            # Replace with dynamic data later
            st.metric("Career Matches", "8")
        st.markdown('</div>', unsafe_allow_html=True)

    # Progress charts in a card
    with st.container():
        st.markdown('<div class="container-card" style="margin-top: 20px;">', unsafe_allow_html=True) # Added margin
        st.subheader("Your Learning Progress (Placeholder)")
        # Replace with actual chart data later
        data = {
            "Python Basics": 100,
            "Data Analysis": 80,
            "Machine Learning": 60,
            "Web Development": 40,
            "Cloud Services": 20
        }
        st.bar_chart(data)
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent activity in a card
    with st.container():
        st.markdown('<div class="container-card" style="margin-top: 20px;">', unsafe_allow_html=True) # Added margin
        st.subheader("Recent Activity (Placeholder)")
        # Replace with dynamic activity later
        st.info("Completed Python Basics course")
        st.info("Added new skills to your profile")
        st.markdown('</div>', unsafe_allow_html=True) 