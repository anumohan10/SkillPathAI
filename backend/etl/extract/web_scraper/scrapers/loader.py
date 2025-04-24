import json
import snowflake.connector
from dotenv import load_dotenv
import os

# Load environment variables
env_path = "/Users/anusreemohanan/Documents/GitHub/SkillPathAI/.env"
load_dotenv(env_path)

print("SNOWFLAKE_ACCOUNT:", os.getenv("SNOWFLAKE_ACCOUNT"))

# Snowflake connection details
conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)

cursor = conn.cursor()

# Load JSON data from file
with open("/Users/anusreemohanan/Documents/GitHub/SkillPathAI/course_metadata.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

# Ensure json_data is a list
if not isinstance(json_data, list):
    json_data = [json_data]  # Convert a single dictionary into a list

# Prepare SQL INSERT statement
insert_query = """
    INSERT INTO UDACITY_COURSES_NEW (URL, Course_Name, Description, Level, Prerequisites, Duration, Language, Skills, Rating)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Loop through each entry in JSON and insert data
rows_inserted = 0
for record in json_data:
    try:
        data_tuple = (
            record.get("URL", None),
            record.get("Course Name", None),
            record.get("Description", None),
            record.get("Level", None),
            record.get("Prerequisites", None),
            record.get("Duration", None),
            record.get("Language", None),
            record.get("Skills", None),
            record.get("Rating", None),
        )

        cursor.execute(insert_query, data_tuple)
        rows_inserted += 1

    except KeyError as e:
        print(f"🚨 KeyError: Missing key in JSON record - {e}")

print(f"✅ {rows_inserted} rows successfully inserted into Snowflake!")

# Close the connection
cursor.close()
conn.close()
