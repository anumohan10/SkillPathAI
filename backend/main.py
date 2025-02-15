import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.etl.extract.fetch_kaggle_dataset import fetch_kaggle_dataset
from backend.etl.extract.process_data import process_dataframe_to_gzip
from backend.etl.load.load_to_snowflake import upload_to_snowflake

# Mapping datasets to their respective internal stages
datasets = {
    "udemy": {
        "dataset_id": "mortezasalarkia/udemy-courses-meta-data-110k-courses",
        "stage": "UDEMY_STAGE"
    },
    "coursera": {
        "dataset_id": "anusreemohanan/coursera-course-details",
        "stage": "COURSERA_STAGE"
    },
    "edx": {
        "dataset_id": "santoshapatil31/edx-all-courses-3082-courses",
        "stage": "EDX_STAGE"
    },
    "udacity": {
        "dataset_id": "anusreemohanan/udacity-courses",
        "stage": "UDACITY_STAGE"
    },
    "pluralsight": {
        "dataset_id": "anusreemohanan/pluralsight-dataset",
        "stage": "PLURALSIGHT_STAGE"
    }
}

# Process each dataset
for name, details in datasets.items():
    print(f"Processing {name} dataset...")

    # Step 1: Fetch dataset
    dataset_files = fetch_kaggle_dataset(details["dataset_id"])

    # Step 2: Transform and load each file
    for file_name, df in dataset_files.items():
        print(f"Compressing {file_name}...")
        gzip_buffer = process_dataframe_to_gzip(df)

        # Step 3: Load into the correct stage
        file_name_gz = file_name.replace('.csv', '.csv.gz')  # Rename to indicate compression
        upload_to_snowflake(gzip_buffer, file_name_gz, details["stage"])

print("All datasets successfully processed and staged!")
