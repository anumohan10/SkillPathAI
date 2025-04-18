# frontend/pages/courses_page.py
import streamlit as st
# Import necessary backend services if needed for search functionality later
# Example: from backend.services.course_service import search_courses

def render_courses_page():
    st.header("Courses")
    with st.container():
        st.markdown('<div class="container-card">', unsafe_allow_html=True)
        st.write("Search and explore courses available on the platform.")
        search_query = st.text_input("Search for courses:", key="course_search_input")

        if st.button("Search Courses", key="course_search_button"): # Added keys
            if search_query:
                # Placeholder: Implement actual course search logic here
                # Example: results = search_courses(search_query)
                st.write(f"Searching for '{search_query}'...")
                # Display results here (e.g., in a loop or table)
                st.info("Search results will be displayed here once implemented.")
            else:
                st.warning("Please enter a search term.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Placeholder for displaying course categories or featured courses
    with st.container():
        st.markdown('<div class="container-card" style="margin-top: 20px;">', unsafe_allow_html=True) # Added margin
        st.subheader("Featured Courses (Placeholder)")
        st.write("Display featured or categorized courses here.")
        # Add logic to display courses (e.g., fetch from backend)
        st.markdown('</div>', unsafe_allow_html=True) 