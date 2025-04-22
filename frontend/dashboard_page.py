import streamlit as st
import json
import requests

FASTAPI_BASE_URL = "http://localhost:8000"

def fetch_recent_chats(user_name, limit=5):
    try:
        response = requests.get(
            f"{FASTAPI_BASE_URL}/user-input/chat-history/recent",
            params={"user_name": user_name, "limit": limit}
        )

        # # 👇 Add these debug prints
        # st.write("🔍 API Status Code:", response.status_code)
        # st.write("📦 API Response Text:", response.text)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Failed to fetch chat history: {response.text}")
            return []
    except Exception as e:
        st.error(f"🚨 API error: {str(e)}")
        return []

def render_dashboard_page():
    st.header("Dashboard")
    st.write(f"Welcome, {st.session_state.get('username', 'Guest')}!")

    with st.expander("Diagnostic Information (Click to expand)"):
        debug_container = st.container()
    
   
    
    st.session_state
    debug_container.json(st.session_state.to_dict())
    with st.container():
        st.markdown('<div class="container-card" style="margin-top: 20px;">', unsafe_allow_html=True)
        st.subheader("🕓 Recent Chat History")

        username = st.session_state.get("username", "User")
        recent_chats = fetch_recent_chats(username)
        print("Recent Chat:\n", recent_chats)
        if not recent_chats:
            st.info("No chat history found.")
        else:
            for i, record in enumerate(recent_chats):
                chat_list = record.get("state_data", [])
                print("State_Data:\n", chat_list)
                timestamp = record.get("cur_timestamp")
                source = record.get("source_page", "unknown")

                # 🛡️ Ensure chat_list is properly parsed
                if isinstance(chat_list, str):
                    try:
                        chat_list = json.loads(chat_list)
                    except json.JSONDecodeError:
                        chat_list = []
                try:
                    preview = chat_list[-1]["content"][:80] + "..." if isinstance(chat_list, list) and chat_list else "(empty)"
                except Exception as e:
                    preview = f"(preview error: {e})"

                
                label = f"🗨️ {source.replace('_', ' ').title()} Chat – {timestamp[:19].replace('T',' ')}"
                if st.button(label, key=f"chat_{i}"):
                    if source == "career_transition":
                        filtered_chat_list = {k: v for k, v in chat_list.items() if k not in ("main_nav","ct_followup_input")}
                        st.session_state.update(filtered_chat_list)
                        st.session_state.ct_state = "display_results"
                        st.session_state.current_page = "Career Transition"
                    elif source == "learning_path":
                        filtered_chat_list = {k: v for k, v in chat_list.items() if k not in ("main_nav", "lp_followup_input")}
                        st.session_state.update(filtered_chat_list)
                        st.session_state.lp_state = "display_results"
                        st.session_state.current_page = "Learning Path"
                    st.session_state.results_displayed = True
                    st.session_state.chat_resumed = True
                    st.rerun()

                st.caption(preview)

        st.markdown('</div>', unsafe_allow_html=True)
