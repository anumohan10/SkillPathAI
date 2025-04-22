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

def save_chat_history(user_name, chat_history, cur_timestamp, source_page):
    """Save chat history to Snowflake."""
    conn = get_snowflake_connection()
    if conn:
        try:
            cur = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS chat_history (
                user_name VARCHAR(255),
                chat_history VARCHAR,
                cur_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                source_page VARCHAR(50)
            );
            """
            cur.execute(create_table_query)
            insert_query = """
            INSERT INTO chat_history (user_name, chat_history, cur_timestamp, source_page)
            VALUES (%s, %s, %s, %s);
            """
            cur.execute(insert_query, (user_name, json.dumps(chat_history), cur_timestamp, source_page))
            conn.commit()
            logger.info("Chat history saved to Snowflake.")
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
        finally:
            cur.close()
            conn.close()
