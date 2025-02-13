import kaggle
import pandas as pd
import os
import zipfile

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
