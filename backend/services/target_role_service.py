# File: backend/services/target_role_service.py
from backend.database import get_snowflake_connection
import streamlit as st

def get_target_role(username: str) -> str:
    """Retrieve the target role for the given username from LEARNING_PATHS."""
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        query = """
        SELECT TARGET_ROLE 
        FROM SKILLPATH_DB.PROCESSED_DATA.LEARNING_PATHS
        WHERE NAME = %s
        ORDER BY CREATED_AT DESC
        LIMIT 1
        """
        cur.execute(query, (username,))
        result = cur.fetchone()
        return result[0] if result else "data engineer"
    except Exception as e:
        st.error(f"Error fetching target role: {e}")
        return "data engineer"
    finally:
        cur.close()
        conn.close()


