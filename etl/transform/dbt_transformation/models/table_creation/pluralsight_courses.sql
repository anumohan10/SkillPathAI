{{ config(
    materialized='table',
    pre_hook=[
        "CREATE OR REPLACE TABLE PLURALSIGHT_COURSES USING TEMPLATE ( SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*)) FROM TABLE( INFER_SCHEMA( LOCATION=>'@PLURALSIGHT_STAGE', FILE_FORMAT=>'inferSchema', IGNORE_CASE=>TRUE ) ) );",
        "COPY INTO PLURALSIGHT_COURSES FROM @PLURALSIGHT_STAGE FILE_FORMAT=(FORMAT_NAME='inferSchema') MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;"
    ]
) }}
 
SELECT * FROM PLURALSIGHT_COURSES