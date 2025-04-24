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
        # Get environment variables with fallbacks
        user = os.getenv("SNOWFLAKE_USER")
        password = os.getenv("SNOWFLAKE_PASSWORD")
        account = os.getenv("SNOWFLAKE_ACCOUNT")
        role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")  # Default role if not specified
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        database = os.getenv("SNOWFLAKE_DATABASE")
        schema = os.getenv("SNOWFLAKE_SCHEMA")
        
        # Log connection attempt (without sensitive info)
        logger.info(f"Connecting to Snowflake: account={account}, user={user}, warehouse={warehouse}, database={database}, schema={schema}")
        
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )
        logger.info("✅ Successfully connected to Snowflake")
        return conn
    except Exception as e:
        logger.error(f"❌ Error connecting to Snowflake: {e}")
        return None

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
            INSERT INTO chat_history (user_name, chat_history, cur_timestamp, source_page, role)
            VALUES (%s, %s, %s, %s, %s);
            """
            cur.execute(insert_query, (user_name, session_state, cur_timestamp, source_page, role))
            conn.commit()
            logger.info("✅ Chat history saved to Snowflake.")
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
            FROM chat_history
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
        
def clean_chat_history(user_name, timestamp):
    logger.info(f"Cleaning chat history for user {user_name} at timestamp {timestamp}")
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        cur.execute("""
        DELETE FROM chat_history
        WHERE user_name = %s AND cur_timestamp = %s
        """, (user_name, timestamp))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Chat history cleaned successfully"
    except Exception as e:
        logger.error(f"❌ Error cleaning chat history: {e}")
        return False, f"Database error: {e}"