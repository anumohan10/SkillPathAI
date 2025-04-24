{{ config(
    materialized='table',
    schema='PROCESSED_DATA'
) }}

WITH udemy AS (
  SELECT
    CAST(ID AS STRING) AS ID,
    COURSE_NAME,
    DESCRIPTION,
    PREREQUISITES,
    SKILLS,
    CASE
      WHEN TRIM(LEVEL) ILIKE 'beginner%' THEN 'Beginner'
      WHEN TRIM(LEVEL) ILIKE 'intermediate%' THEN 'Intermediate'
      WHEN TRIM(LEVEL) ILIKE 'expert%' THEN 'Advanced'
      WHEN TRIM(LEVEL) ILIKE 'all%' THEN 'All Levels'
      ELSE 'Other'
    END AS LEVEL,
    LANGUAGE,
    DURATION,
    DURATION_HOURS,
    RATING,
    SOURCE,
    INGESTION_TIME,
    URL,
    HAS_PREREQUISITES,
    'Udemy' AS PLATFORM
  FROM {{ source('RAW_DATA_PROCESSED_DATA', 'STG_UDEMY_COURSES') }}
),

udacity AS (
  SELECT
    ID,
    COURSE_NAME,
    DESCRIPTION,
    PREREQUISITES,
    SKILLS,
    CASE
      WHEN TRIM(LEVEL) ILIKE 'beginner' THEN 'Beginner'
      WHEN TRIM(LEVEL) ILIKE 'intermediate' THEN 'Intermediate'
      WHEN TRIM(LEVEL) ILIKE 'advanced' THEN 'Advanced'
      WHEN TRIM(LEVEL) ILIKE 'discovery' THEN 'All Levels'
      WHEN TRIM(LEVEL) ILIKE 'fluency' THEN 'Fluency'
      ELSE 'Other'
    END AS LEVEL,
    LANGUAGE,
    DURATION,
    DURATION_HOURS,
    RATING,
    SOURCE,
    INGESTION_TIME,
    URL,
    HAS_PREREQUISITES,
    'Udacity' AS PLATFORM
  FROM {{ source('RAW_DATA_PROCESSED_DATA', 'UDACITY_COURSES_ENRICHED') }}
),

edx AS (
  SELECT
    ID,
    COURSE_NAME,
    DESCRIPTION,
    PREREQUISITES,
    SKILLS,
    CASE
      WHEN TRIM(LEVEL) ILIKE 'beginner' THEN 'Beginner'
      WHEN TRIM(LEVEL) ILIKE 'intermediate' THEN 'Intermediate'
      WHEN TRIM(LEVEL) ILIKE 'advanced' THEN 'Advanced'
      ELSE 'Other'
    END AS LEVEL,
    LANGUAGE,
    DURATION,
    DURATION_HOURS,
    RATING,
    SOURCE,
    INGESTION_TIME,
    URL,
    HAS_PREREQUISITES,
    'edX' AS PLATFORM
  FROM {{ source('RAW_DATA_PROCESSED_DATA', 'EDX_COURSES_ENRICHED') }}
)

SELECT * FROM udemy
UNION ALL
SELECT * FROM udacity
UNION ALL
SELECT * FROM edx
