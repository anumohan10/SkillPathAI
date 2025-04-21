import streamlit as st

def render_guidance_hub_page():
    """Renders the Guidance Hub selection page."""
    st.header("🧭 Guidance Hub")
    st.markdown("Choose the tool that best suits your current goals:")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Personalized Learning Path")
        st.write("Define your target role and assess your skills to get a curated list of courses and resources.")
        if st.button("Go to Learning Path", key="goto_lp"):
            # Update the current page state to navigate
            st.session_state.current_page = "Learning Path"
            st.rerun() # Rerun to trigger the display logic in dashboard.py

    with col2:
        st.subheader("🚀 Career Transition Assistant")
        st.write("Analyze your resume against a target role, identify skill gaps, and get tailored advice.")
        if st.button("Go to Career Transition", key="goto_ct"):
            # Update the current page state to navigate
            st.session_state.current_page = "Career Transition"
            st.rerun() # Rerun to trigger the display logic in dashboard.py

    st.markdown("---") 