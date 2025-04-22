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

def save_chat_history(user_name, chat_history, cur_timestamp, source_page="Unknown", target_role=None):
    """Save chat history to Snowflake."""
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Use the fully qualified table name and include all required columns
            insert_query = """
            INSERT INTO SKILLPATH_DB.RAW_DATA.CHAT_HISTORY (user_name, chat_history, cur_timestamp, source_page, role)
            VALUES (%s, %s, %s, %s, %s);
            """
            
            # Convert chat history to a string in the appropriate format
            # Check if it's a dict or list (needs to be serialized)
            if isinstance(chat_history, (list, dict)):
                chat_history_str = json.dumps(chat_history)
            # Check if it's already a string that contains JSON
            elif isinstance(chat_history, str):
                try:
                    # Attempt to parse and re-serialize to ensure valid JSON format
                    json_obj = json.loads(chat_history)
                    chat_history_str = json.dumps(json_obj)
                except json.JSONDecodeError:
                    # Not valid JSON, use as-is (unlikely but handled)
                    chat_history_str = chat_history
            else:
                # Fallback case (unlikely)
                chat_history_str = str(chat_history)
                
            # Use target_role as-is, or "Unknown Role" if None
            role_value = target_role if target_role else "Unknown Role"
                
            cur.execute(insert_query, (user_name, chat_history_str, cur_timestamp, source_page, role_value))
            conn.commit()
            logger.info(f"✅ Chat history saved to SKILLPATH_DB.RAW_DATA.CHAT_HISTORY for user {user_name} with role {role_value}")
            return True, "Chat history saved successfully"
        except Exception as e:
            logger.error(f"❌ Error saving chat history: {e}")
            return False, f"Database error: {e}"
        finally:
            cur.close()
            conn.close()
