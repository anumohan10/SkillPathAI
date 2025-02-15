import os
from database import get_snowflake_connection

def upload_to_snowflake(gzip_buffer, file_name, stage_name):
    """
    Uploads the compressed dataset to Snowflake internal storage.
    
    Parameters:
    gzip_buffer (BytesIO): Compressed dataset in memory
    file_name (str): Name of the file to be stored in Snowflake
    stage_name (str): The Snowflake internal stage (e.g., "SKILLPATH_DB.RAW_DATA.COURSES_STAGE")
    """
    # Replace spaces in the file name to prevent syntax errors in SQL command
    safe_file_name = file_name.replace(" ", "_").replace("-", "_")  # replace spaces and dashes with underscores
    temp_path = f"/tmp/{safe_file_name}"
    
    print(f"Uploading {safe_file_name} to {stage_name}...")

    # Establish Snowflake connection
    conn = get_snowflake_connection()
    cur = conn.cursor()

    # Save compressed file temporarily
    with open(temp_path, "wb") as f:
        f.write(gzip_buffer.getvalue())

    # Upload file to Snowflake stage
    stage_command = f"""
    PUT file://{temp_path} @{stage_name}
    AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
    """
    cur.execute(stage_command)

    # Remove the temporary file after upload
    os.remove(temp_path)
    print(f"File {safe_file_name} successfully uploaded to {stage_name} and deleted locally.")

    cur.close()
    conn.close()
