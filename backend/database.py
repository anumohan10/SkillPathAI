import os
import snowflake.connector
from dotenv import load_dotenv
import logging
import json
# Load environment variables
load_dotenv()

# TODO: Move all create table queries to dbt for better schema management and version control

logger = logging.getLogger(__name__)

def get_snowflake_connection():
    """Establish a connection to Snowflake using .env credentials."""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            role=os.getenv("SNOWFLAKE_ROLE"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
        )
        logger.info("Env_Variable:\n", os.getenv("SNOWFLAKE_USER"),os.getenv("SNOWFLAKE_ACCOUNT"), os.getenv("SNOWFLAKE_ROLE"), os.getenv("SNOWFLAKE_WAREHOUSE"), os.getenv("SNOWFLAKE_DATABASE"),os.getenv("SNOWFLAKE_SCHEMA"))
        return conn
    except Exception as e:
        logger.error(f"❌ Error connecting to Snowflake: {e}")
        return None
        
def get_latest_resume_missing_skills(username, target_role=None):
    """
    Retrieve missing skills from the most recent resume entry in the database.
    
    Args:
        username (str): The username to lookup
        target_role (str, optional): The target role to filter by
        
    Returns:
        list: List of missing skills, or None if not found
    """
    conn = None
    cursor = None
    
    try:
        conn = get_snowflake_connection()
        if not conn:
            logger.error("Failed to connect to Snowflake")
            return None
            
        cursor = conn.cursor()
        
        # Build query based on whether target_role is provided
        if target_role:
            query = """
            SELECT MISSING_SKILLS
            FROM SKILLPATH_DB.PUBLIC.RESUMES
            WHERE USER_NAME = %s AND TARGET_ROLE = %s
            ORDER BY CREATED_AT DESC
            LIMIT 1
            """
            cursor.execute(query, (username, target_role))
        else:
            query = """
            SELECT MISSING_SKILLS, TARGET_ROLE
            FROM SKILLPATH_DB.PUBLIC.RESUMES
            WHERE USER_NAME = %s
            ORDER BY CREATED_AT DESC
            LIMIT 1
            """
            cursor.execute(query, (username,))
            
        row = cursor.fetchone()
        
        if not row:
            logger.warning(f"No resume entry found for user {username}")
            return None
            
        # Parse missing skills from JSON
        missing_skills = row[0]
        
        if isinstance(missing_skills, str):
            try:
                import json
                return json.loads(missing_skills)
            except:
                logger.error(f"Failed to parse missing skills for user {username}")
                return None
        
        return missing_skills
        
    except Exception as e:
        logger.error(f"Error retrieving missing skills: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_resumes_table():
    """Ensure the resumes table exists before inserting data."""
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS resumes (
                id STRING PRIMARY KEY,
                user_name VARCHAR(255),  -- Small names
                resume_text VARCHAR(16777216),  -- Large text storage
                extracted_skills ARRAY,
                target_role VARCHAR(255),
                missing_skills ARRAY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            );
            """
            cur.execute(create_table_query)
            conn.commit()
            logger.info("✅ Snowflake table 'resumes' is ready.")
        except Exception as e:
            logger.error(f"❌ Error creating resumes table: {e}")
        finally:
            cur.close()
            conn.close()

def save_session_state(user_name, session_state, cur_timestamp, source_page, role):
    """Save session state to Snowflake."""
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            # create_table_query = """
            # CREATE TABLE IF NOT EXISTS chat_history (
            #     user_name VARCHAR(255),
            #     chat_history VARCHAR,
            #     cur_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
            #     source_page VARCHAR(50)
            # );
            # """
            # cur.execute(create_table_query)
            insert_query = """
            INSERT INTO SKILLPATH_DB.RAW_DATA.CHAT_HISTORY (user_name, chat_history, cur_timestamp, source_page, role)
            VALUES (%s, %s, %s, %s, %s);
            """
            cur.execute(insert_query, (user_name, session_state, cur_timestamp, source_page, role))
            conn.commit()
            logger.info(f"✅ Chat history saved to SKILLPATH_DB.RAW_DATA.CHAT_HISTORY for user {user_name} with role {role}")
            return True, "Chat history saved successfully"
        except Exception as e:
            logger.error(f"❌ Error saving chat history: {e}")
            return False, f"Database error: {e}"
        finally:
            cur.close()
            conn.close()
            
def retrieve_session_state(user_name, limit):
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT chat_history, cur_timestamp, source_page, role
            FROM SKILLPATH_DB.RAW_DATA.CHAT_HISTORY
            WHERE user_name = %s
            ORDER BY cur_timestamp DESC
            LIMIT %s
        """, (user_name, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logger.warning(f"Database error while retrieving session data: {e}") 
        
def clean_up_session(cur):
    pass
    