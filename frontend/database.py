import os
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        print("❌ Error connecting to Snowflake:", e)
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
            print("✅ Snowflake table 'resumes' is ready.")
        except Exception as e:
            print("❌ Error creating resumes table:", e)
        finally:
            cur.close()
            conn.close()
