import kaggle
import os
import pandas as pd
import io
import gzip

def fetch_kaggle_dataset(dataset_id, output_path):
    """
    Fetch dataset from Kaggle, attempt to read CSV with different encodings,
    and save as a single compressed gzip file if multiple CSVs are present.
    """
    print(f"Fetching dataset: {dataset_id}")
    print(os.getcwd())
    kaggle.api.dataset_download_files(dataset_id, path="./tmp_unprocessed", unzip=True)

    # Find all CSV files in the temp directory
    csv_files = [f for f in os.listdir("./tmp_unprocessed") if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError("No CSV files found.")

    # Try reading CSV files with multiple encodings
    data_frames = []
    for file in csv_files:
        file_path = os.path.join("./tmp_unprocessed", file)
        success = False
        for encoding in ['utf-8', 'ISO-8859-1', 'ascii']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                data_frames.append(df)
                print(f"Successfully read {file} with encoding {encoding}")
                success = True
                break  # Stop trying encodings if successful
            except UnicodeDecodeError:
                print(f"Failed to read {file} with encoding {encoding}")
        if not success:
            raise ValueError(f"Failed to decode {file} with standard encodings")

    # Concatenate all data frames if multiple files are found
    if data_frames:
        combined_df = pd.concat(data_frames, ignore_index=True)

    # Save concatenated DataFrame to a single compressed gzip file
# Save the DataFrame directly as a CSV file (without compression)
    combined_df.to_csv(os.path.join("./tmp", output_path), index=False, encoding="utf-8")


    # for file in csv_files:
    #     file_path = os.path.join("./tmp", file)
    #     os.rename(file_path, os.path.join("./tmp", output_path))
    
    print(f"Dataset concatenated and saved to {output_path}")
    return os.path.join("./tmp", output_path)
