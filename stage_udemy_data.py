import kaggle
import pandas as pd
import snowflake.connector
import io
import gzip
import os
import os
from dotenv import load_dotenv
import snowflake.connector

# Kaggle dataset ID
dataset = "mortezasalarkia/udemy-courses-meta-data-110k-courses"

# Fetch the Kaggle dataset without saving locally
print("Fetching Udemy dataset from Kaggle API...")
kaggle.api.dataset_download_files(dataset, path="/tmp", unzip=True)

# Locate the extracted CSV file
csv_files = [f for f in os.listdir("/tmp") if f.endswith(".csv")]
if not csv_files:
    raise FileNotFoundError("No CSV file found in /tmp directory")
csv_filename = csv_files[0]

# Read directly into Pandas (no local storage)
df = pd.read_csv(f"/tmp/{csv_filename}")

# Convert DataFrame to CSV in-memory
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)
csv_buffer.seek(0)  # Reset pointer

# Compress CSV using GZIP
gzip_path = f"/tmp/{csv_filename}.gz"
with gzip.open(gzip_path, "wt", encoding="utf-8") as gz_file:
    gz_file.write(csv_buffer.getvalue())

print(f"Compressed file created: {gzip_path}")

# Connect to Snowflake
print("Connecting to Snowflake...")
conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)
 
cur = conn.cursor()

# Upload the compressed file to Snowflake stage
stage_command = f"""
PUT file://{gzip_path} @SKILLPATH_DB.RAW_DATA.UDEMY_STAGE
AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
"""
print("Uploading data to Snowflake internal stage...")
cur.execute(stage_command)

print("File successfully staged in Snowflake.")

# Remove local compressed file after upload
os.remove(gzip_path)
print("Temporary compressed file removed.")

# Close connection
cur.close()
conn.close()

print("Data successfully uploaded to Snowflake internal stage!")
