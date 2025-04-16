import os
import sys
import shlex
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
from backend.database import get_snowflake_connection

def upload_to_snowflake(file_path, file_name, stage_name):
    print(f"Uploading {file_name} to {stage_name}...")
    
    # Establish Snowflake connection
    conn = get_snowflake_connection()
    cur = conn.cursor()

    # Upload file to Snowflake stage
    create_json_format = "CREATE OR REPLACE FILE FORMAT SKILLPATH_DB.RAW_DATA.JSON_FORMAT \
    TYPE = 'JSON'\
    STRIP_OUTER_ARRAY = TRUE;"
    create_stage = "CREATE OR REPLACE STAGE SKILLPATH_DB.RAW_DATA.EDX_SCRAPED_STAGE;"
    stage_command = f"PUT file://{file_path} @{stage_name} AUTO_COMPRESS=TRUE OVERWRITE=TRUE;"
    
    cur.execute(create_json_format)
    cur.execute(create_stage)
    cur.execute(stage_command)
    
    # Cleanup: Remove the local file after upload
    # os.rename(file_path, os.getcwd()+f"processed/{file_name}")

    print(f"File {file_name} successfully uploaded to {stage_name} and deleted locally.")
    cur.close()
    conn.close()

def main():
    path = './edx_course_metadata.json'
    upload_to_snowflake(os.path.abspath(path), 'edx_course_metadata.json', 'EDX_SCRAPED_STAGE')
if __name__ == "__main__":
    main()

