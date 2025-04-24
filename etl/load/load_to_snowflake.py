import os
from backend.database import get_snowflake_connection

def upload_to_snowflake(file_path, file_name, stage_name):
    print(f"Uploading {file_name} to {stage_name}...")
    
    # Establish Snowflake connection
    conn = get_snowflake_connection()
    cur = conn.cursor()

    # Upload file to Snowflake stage
    stage_command = f"PUT file://{file_path} @{stage_name} AUTO_COMPRESS=TRUE OVERWRITE=TRUE;"
    cur.execute(stage_command)
    
    
    # Cleanup: Remove the local file after upload
    # os.rename(file_path, os.getcwd()+f"processed/{file_name}")

    print(f"File {file_name} successfully uploaded to {stage_name} and deleted locally.")
    cur.close()
    conn.close()
