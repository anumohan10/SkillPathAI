import os
from dotenv import load_dotenv
import snowflake.connector

env_path = "/Users/anusreemohanan/Documents/GitHub/SkillPathAI/.env"
load_dotenv(env_path)
print("SNOWFLAKE_ACCOUNT:", os.getenv("SNOWFLAKE_ACCOUNT"))


if os.getenv("SNOWFLAKE_ACCOUNT") is None:
    raise ValueError("SNOWFLAKE_ACCOUNT is not set. Check your .env file.")

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)
 
cur = conn.cursor()
print("Connected to Snowflake successfully!")


