import kaggle
import pandas as pd
import os
import zipfile
import snowflake.connector
import io
import os
from dotenv import load_dotenv
import snowflake.connector

# Kaggle dataset ID
dataset = "mortezasalarkia/udemy-courses-meta-data-110k-courses"

# Get file list from Kaggle API
files = kaggle.api.dataset_list_files(dataset)
file_list = files.files  # Convert to list
filename = file_list[0].name if file_list else None  # Get the first file

if filename:
    print(f"Downloading file: {filename}")

    # Download the dataset file
    kaggle.api.dataset_download_files(dataset, path="./", unzip=True)  # ✅ Downloads and unzips

    # Check if the file is a ZIP or CSV
    if filename.endswith(".zip"):
        print("Extracting ZIP file...")
        with zipfile.ZipFile(f"./{filename}", 'r') as z:
            z.extractall("./")  # Extract files into the current directory
            extracted_filename = z.namelist()[0]  # Get extracted CSV name
        
        df = pd.read_csv(f"./{extracted_filename}")  # Read the extracted CSV
    else:
        print("Reading CSV file directly...")
        df = pd.read_csv(f"./{filename}")  # Read the CSV directly

    # Display first 5 rows
    print(df.head())

    # Optional: Remove downloaded files after processing
    os.remove(f"./{filename}")

else:
    print("No files found in the dataset.")

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)
cur = conn.cursor()

# ✅ Automatically Generate CREATE TABLE SQL Statement
def generate_create_table_sql(table_name, df):
    type_mapping = {
        "int64": "INT",
        "float64": "FLOAT",
        "object": "STRING",
        "bool": "BOOLEAN"
    }
    
    columns = []
    for col, dtype in df.dtypes.items():
        snowflake_type = type_mapping.get(str(dtype), "STRING")  # Default to STRING if unknown
        columns.append(f'"{col}" {snowflake_type}')
    
    create_table_sql = f'CREATE OR REPLACE TABLE {table_name} ({", ".join(columns)});'
    return create_table_sql

# Generate and Execute CREATE TABLE statement
table_name = "UDEMY_COURSES"
create_table_sql = generate_create_table_sql(f"RAW_DATA.{table_name}", df)
cur.execute(create_table_sql)
print(f"Table {table_name} created successfully!")

# ✅ Convert DataFrame to List of Tuples for Snowflake
data = [tuple(row) for row in df.itertuples(index=False, name=None)]

# ✅ Insert Data into Snowflake
insert_sql = f"INSERT INTO RAW_DATA.{table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['%s'] * len(df.columns))})"
cur.executemany(insert_sql, data)

# ✅ Commit and Close Connection
conn.commit()
cur.close()
conn.close()
print(f"✅ Inserted {len(df)} records into {table_name} successfully!")

