import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print(sys.path)
from etl.extract.fetch_kaggle_dataset import fetch_kaggle_dataset
from etl.load.load_to_snowflake import upload_to_snowflake

# Define datasets and their corresponding stages
datasets = {
    "udemy": {"dataset_id": "mortezasalarkia/udemy-courses-meta-data-110k-courses", "filename": "udemy.csv", "stage": "UDEMY_STAGE"},
    "coursera": {"dataset_id": "anusreemohanan/coursera-course-details", "filename": "coursera.csv","stage": "COURSERA_STAGE"},
    "edx": {"dataset_id": "santoshapatil31/edx-all-courses-3082-courses", "filename": "edx.csv","stage": "EDX_STAGE"},
    "udacity": {"dataset_id": "anusreemohanan/udacity-courses", "filename": "udacity.csv", "stage": "UDACITY_STAGE"},
    "pluralsight": {"dataset_id": "anusreemohanan/pluralsight-dataset", "filename": "pluralsight.csv", "stage": "PLURALSIGHT_STAGE"}
}

# Process each dataset
for name, details in datasets.items():
    print(f"Processing {name} dataset...")

    # Fetch and compress dataset
    output_path = fetch_kaggle_dataset(details["dataset_id"], details["filename"])
    file_name_gz = output_path.split("/")[-1]  # Get the name of the gzipped file

    # Upload compressed file to the designated stage
    upload_to_snowflake(output_path, file_name_gz, details["stage"])

print("All datasets successfully processed and staged!")