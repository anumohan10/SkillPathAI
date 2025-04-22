# frontend/pages/dashboard_page.py

import streamlit as st
import json
from datetime import datetime
from backend.database import get_snowflake_connection

def fetch_recent_chats(user_name, limit=5):
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT chat_history, cur_timestamp, source_page
                FROM chat_history
                WHERE user_name = %s
                ORDER BY cur_timestamp DESC
                LIMIT %s
            """, (user_name, limit))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()
    return []

def render_dashboard_page():
    st.header("Dashboard")
    st.write(f"Welcome, {st.session_state.get('username', 'Guest')}!")

    # --- Chat History Section Only ---
    with st.container():
        st.markdown('<div class="container-card" style="margin-top: 20px;">', unsafe_allow_html=True)
        st.subheader("🕓 Recent Chat History")

        username = st.session_state.get("username", "User")
        recent_chats = fetch_recent_chats(username)

        if not recent_chats:
            st.info("No chat history found.")
        else:
            for i, (chat_json, timestamp, source) in enumerate(recent_chats):
                try:
                    chat_list = json.loads(chat_json)
                    preview = chat_list[-1]["content"][:80] + "..." if chat_list else "(empty)"
                except:
                    preview = "(could not load preview)"

                label = f"🗨️ {source.replace('_', ' ').title()} Chat – {timestamp.strftime('%b %d, %Y %I:%M %p')}"
                if st.button(label, key=f"chat_{i}"):
                    if source == "career_transition":
                        st.session_state.ct_messages = chat_list
                        st.session_state.ct_state = "display_results"
                        st.session_state.current_page = "Career Transition"
                    elif source == "learning_path":
                        st.session_state.lp_messages = chat_list
                        st.session_state.lp_state = "display_results"
                        st.session_state.current_page = "Learning Path"
                    st.session_state.results_displayed = True
                    st.session_state.chat_resumed = True
                    st.rerun()

                st.caption(preview)

        st.markdown('</div>', unsafe_allow_html=True)
