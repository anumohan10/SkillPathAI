import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.database import get_snowflake_connection
from langdetect import detect, LangDetectException
import pandas as pd
from sqlalchemy import create_engine
import logging
from datetime import datetime
from snowflake.sqlalchemy import URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'language_detection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Snowflake connection and engine
conn = get_snowflake_connection()
engine = create_engine(URL(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database="SKILLPATH_DB",
    schema="PROCESSED_DATA"
))

# Language detection function
def detect_lang_safe(text):
    try:
        return detect(text) if isinstance(text, str) else 'unknown'
    except LangDetectException:
        return 'unknown'

# Main processing
def main():
    logger.info("Starting language detection preprocessing")
    
    chunk_size = 10000
    select_query = "SELECT TITLE, OBJECTIVES_SUMMARY FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES;"
    create_table_query = "CREATE OR REPLACE TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_EN \
                   LIKE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES;"
    # Connect to Snowflake
    cursor = conn.cursor()

    try:
        # Create table
        logger.info("Creating table UDEMY_COURSES_EN")
        cursor.execute(create_table_query)
        logger.info("Table created successfully")

        # Fetch and process data in chunks
        logger.info(f"Executing query: {select_query}")
        chunk_iterator = pd.read_sql(select_query, conn, chunksize=chunk_size)
        
        total_rows = cursor.execute(select_query).rowcount
        if not total_rows or total_rows <= 0:
            logger.warning("No rows in UDEMY_COURSES, exiting")
            return
        total_chunks = (total_rows + chunk_size - 1) // chunk_size  # Ceiling division
        
        for i, chunk in enumerate(chunk_iterator):
            if chunk.empty:
                logger.info(f"Chunk {i+1}/{total_chunks} is empty, skipping")
                continue
                
            logger.info(f"Processing chunk {i+1}/{total_chunks} ({len(chunk)} rows)")
            chunk['title_lang'] = [detect_lang_safe(t) for t in chunk['TITLE']]
            chunk['summary_lang'] = [detect_lang_safe(t) for t in chunk['OBJECTIVES_SUMMARY']]
            
            logger.info(f"Writing chunk {i+1}/{total_chunks} to Snowflake")
            chunk.to_sql(
                'udemy_courses_en',
                engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            logger.info(f"Chunk {i+1}/{total_chunks} written successfully")

        logger.info("Preprocessing completed successfully")

    except Exception as e:
        logger.critical(f"Preprocessing failed: {str(e)}")
        raise
    
    finally:
        cursor.close()
        conn.close()
        engine.dispose()
        logger.info("Snowflake connection closed")

if __name__ == "__main__":
    main()