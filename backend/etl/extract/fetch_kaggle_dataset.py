import kaggle
import os
import pandas as pd

def fetch_kaggle_dataset(dataset_id):
    """
    Fetch dataset from Kaggle API and return a Pandas DataFrame, attempting multiple encodings if necessary.
    """
    print(f"Fetching dataset: {dataset_id}")
    kaggle.api.dataset_download_files(dataset_id, path="/tmp", unzip=True)

    # Find extracted CSV file
    csv_files = [f for f in os.listdir("/tmp") if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found for {dataset_id}")
    
    csv_filename = csv_files[0]
    file_path = f"/tmp/{csv_filename}"

    # Try reading the file with multiple encodings
    encodings = ['utf-8', 'ISO-8859-1', 'ascii']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"Reading {csv_filename} with detected encoding: {encoding}")
            break
        except UnicodeDecodeError as e:
            print(f"Error decoding file with {encoding}: {e}")
            if encoding == encodings[-1]:  # if last encoding attempt fails, re-raise the error
                raise
    
    # Cleanup local CSV
    os.remove(file_path)

    print(f"Dataset {dataset_id} fetched successfully!")
    return df
