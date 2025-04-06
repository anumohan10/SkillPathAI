import streamlit as st
import json

def learning_path_chat():
    st.header("🎯 Personalized Learning Path Assistant")

    if "lp_state" not in st.session_state:
        st.session_state.lp_state = "ask_name"
        st.session_state.lp_messages = []
        st.session_state.lp_data = {}

    def add_message(role, content):
        st.session_state.lp_messages.append({"role": role, "content": content})

    # Show chat history
    for msg in st.session_state.lp_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # === Step 1: Ask for name ===
    if st.session_state.lp_state == "ask_name":
        if not st.session_state.lp_messages:
            add_message("assistant", "👋 Hi! What's your name?")
            st.rerun()
        user_input = st.chat_input("Your name")
        if user_input:
            st.session_state.lp_data["name"] = user_input
            add_message("user", user_input)
            add_message("assistant", f"Nice to meet you, {user_input}! What career would you like to pursue?")
            st.session_state.lp_state = "ask_role"
            st.rerun()

    # === Step 2: Ask target role ===
    elif st.session_state.lp_state == "ask_role":
        user_input = st.chat_input("E.g., Data Scientist, UX Designer")
        if user_input:
            st.session_state.lp_data["target_role"] = user_input
            add_message("user", user_input)

            # For now, hardcoding sample skills — replace with dynamic fetch later
            st.session_state.lp_data["skills_to_rate"] = ["Python", "Data Analysis", "Machine Learning", "SQL", "Statistics"]
            st.session_state.lp_data["ratings"] = {}
            st.session_state.lp_data["current_skill_index"] = 0

            add_message("assistant", f"Great! Let's assess your skills for **{user_input}**.")
            st.session_state.lp_state = "rate_skills"
            st.rerun()

    # === Step 3a: Assistant asks skill rating ===
    elif st.session_state.lp_state == "rate_skills":
        skills = st.session_state.lp_data["skills_to_rate"]
        index = st.session_state.lp_data["current_skill_index"]
        current_skill = skills[index]

        add_message("assistant", f"How would you rate yourself in **{current_skill}** (1–5)?")
        st.session_state.lp_state = "wait_for_rating"
        st.rerun()

    # === Step 3b: Wait for user rating ===
    elif st.session_state.lp_state == "wait_for_rating":
        skills = st.session_state.lp_data["skills_to_rate"]
        index = st.session_state.lp_data["current_skill_index"]
        current_skill = skills[index]

        user_input = st.chat_input(f"Rate yourself on {current_skill} (1–5)")
        if user_input:
            try:
                rating = int(user_input.strip())
                if 1 <= rating <= 5:
                    st.session_state.lp_data["ratings"][current_skill] = rating
                    add_message("user", f"{rating}")
                    index += 1
                    if index < len(skills):
                        st.session_state.lp_data["current_skill_index"] = index
                        st.session_state.lp_state = "rate_skills"
                    else:
                        st.session_state.lp_state = "generate_path"
                    st.rerun()
                else:
                    add_message("assistant", "❗ Please enter a number between 1 and 5.")
                    st.rerun()
            except ValueError:
                add_message("assistant", "❗ Please enter a valid number (1–5).")
                st.rerun()


    # === Step 4: Generate learning path using Cortex ===
    elif st.session_state.lp_state == "generate_path":
        with st.spinner("🧠 Generating your personalized learning path..."):
            try:
                from backend.services.chat_service import ChatService
                chat = ChatService()

                skills_rated = st.session_state.lp_data["ratings"]
                target_role = st.session_state.lp_data["target_role"]

                prompt = (
                    f"Suggest a personalized learning path for becoming a {target_role}. "
                    f"The user rated themselves on these skills: {json.dumps(skills_rated)}. "
                    "Provide course suggestions, certifications, and practical tips in markdown format."
                )

                response = chat.get_llm_response(prompt)
                add_message("assistant", response)

                # Save to Snowflake
                try:
                    from backend.services.learning_path_service import store_learning_path
                    store_learning_path(st.session_state.lp_data)
                except Exception as e:
                    add_message("assistant", f"⚠️ Failed to save to database: {e}")

                st.session_state.lp_state = "done"
                st.rerun()

            except Exception as e:
                add_message("assistant", f"⚠️ Error generating learning path: {e}")
                st.session_state.lp_state = "ask_name"
                st.rerun()

    # === Step 5: End conversation ===
    elif st.session_state.lp_state == "done":
        user_input = st.chat_input("Do you have any questions?")
        if user_input:
            add_message("user", user_input)
            try:
                from backend.services.chat_service import ChatService
                chat = ChatService()
                context = (
                    f"The user is transitioning to {st.session_state.lp_data['target_role']} with skill ratings: "
                    f"{json.dumps(st.session_state.lp_data['ratings'])}"
                )
                followup_response = chat.get_llm_response(user_input, context=context)
            except Exception as e:
                followup_response = "Sorry, I couldn't process that right now."

            add_message("assistant", followup_response)
            st.rerun()
