import kaggle
import pandas as pd
import os
import zipfile
import snowflake.connector
import math
import re  # For column name cleaning
import numpy as np  # For handling NaN values

# Kaggle dataset ID
dataset = "mortezasalarkia/udemy-courses-meta-data-110k-courses"

# Get file list from Kaggle API
files = kaggle.api.dataset_list_files(dataset)
file_list = files.files  # Convert to list
filename = file_list[0].name if file_list else None  # Get the first file

if filename:
    print(f"Downloading file: {filename}")

    # Download the dataset file
    kaggle.api.dataset_download_files(dataset, path="./", unzip=True)  

    # Check if the file is a ZIP or CSV
    if filename.endswith(".zip"):
        print("Extracting ZIP file...")
        with zipfile.ZipFile(f"./{filename}", 'r') as z:
            z.extractall("./")  
            extracted_filename = z.namelist()[0]  

        df = pd.read_csv(f"./{extracted_filename}")  
    else:
        print("Reading CSV file directly...")
        df = pd.read_csv(f"./{filename}")  

    # Drop 'Unnamed: 0' column if it exists
    if "Unnamed: 0" in df.columns:
        df.drop(columns=["Unnamed: 0"], inplace=True)

    #Replace NaN values with None for Snowflake compatibility
    df.replace({np.nan: None}, inplace=True)

    # Display first 5 rows
    print(df.head())

    # Optional: Remove downloaded files after processing
    os.remove(f"./{filename}")

else:
    print("No files found in the dataset.")

#Clean column names (remove spaces, special characters)
def clean_column_name(name):
    name = re.sub(r'\W+', '_', name)  # Replace special characters with _
    return name.lower()  # Convert to lowercase for consistency

df.columns = [clean_column_name(col) for col in df.columns]  # Apply cleaning

# Snowflake connection
conn = snowflake.connector.connect(
    user="DRAGON",
    password="Skill@12345678",
    account="sfedu02-pdb57018",
    warehouse="SKILLPATH_WH",
    database="SKILLPATH_DB",
    schema="RAW_DATA"
)
cur = conn.cursor()

#Create structured table if not exists (with cleaned column names)
def generate_create_table_sql(table_name, df):
    type_mapping = {
        "int64": "NUMBER(38,0)",
        "float64": "FLOAT",
        "object": "VARCHAR(16777216)",
        "bool": "BOOLEAN"
    }
    
    columns = []
    for col, dtype in df.dtypes.items():
        snowflake_type = type_mapping.get(str(dtype), "VARCHAR(16777216)")  # Default to STRING if unknown
        columns.append(f'"{col}" {snowflake_type}')  # Ensure column names are quoted
    
    create_table_sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(columns)});'
    return create_table_sql

# Generate and Execute CREATE TABLE statement
table_name = "UDEMY_COURSES"
create_table_sql = generate_create_table_sql(f"RAW_DATA.{table_name}", df)
cur.execute(create_table_sql)
print(f"Table {table_name} created successfully!")

#Insert data in chunks (5000 rows per batch)
chunk_size = 5000  
num_chunks = math.ceil(len(df) / chunk_size)

# Prepare SQL statement for structured insert (clean column names)
columns_str = ', '.join(f'"{col}"' for col in df.columns)  # Wrap column names in double quotes
values_placeholder = ', '.join(['%s'] * len(df.columns))

insert_sql = f"INSERT INTO RAW_DATA.{table_name} ({columns_str}) VALUES ({values_placeholder})"

# Insert data in chunks
for i in range(num_chunks):
    chunk_df = df[i * chunk_size:(i + 1) * chunk_size]
    data = [tuple(row) for row in chunk_df.itertuples(index=False, name=None)]
    cur.executemany(insert_sql, data)
    print(f"Inserted chunk {i+1}/{num_chunks} into Snowflake.")

# Commit and Close Connection
conn.commit()
cur.close()
conn.close()
print(f"Inserted {len(df)} records into {table_name} successfully!")
