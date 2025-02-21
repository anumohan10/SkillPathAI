import time
from database import get_snowflake_connection
from snowflake.connector import DictCursor
from snowflake.connector import ProgrammingError

# Establish Snowflake connection
conn = get_snowflake_connection()
cursor = conn.cursor(DictCursor)

# Dictionary mapping stages to table names
stages_to_tables = {
    "COURSERA_STAGE": "COURSERA_COURSES",
    "EDX_STAGE": "EDX_COURSES",
    "UDACITY_STAGE": "UDACITY_COURSES",
    "UDEMY_STAGE": "UDEMY_COURSES",
    "PLURALSIGHT_STAGE": "PLURALSIGHT_COURSES"
}

# Loop through each stage and create a table using the inferred schema
for stage, table_name in stages_to_tables.items():
    try:
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} USING TEMPLATE (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
            FROM TABLE(
            INFER_SCHEMA(
                LOCATION => '@{stage}',
                FILE_FORMAT => 'inferSchema',
                IGNORE_CASE => TRUE
            )
        )  
        );
        """
        cursor.execute(create_table_query) 
        print("Table name",cursor.fetchall()[0]["status"])
    except ProgrammingError as e:
        print(f"Error creating table '{table_name}': {e.msg}")

# Clean up
cursor.close()
conn.close()
