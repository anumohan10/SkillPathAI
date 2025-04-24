{{
  config(
    materialized = 'table',
    transient = true
  )
}}

WITH source AS (
    SELECT * FROM {{ source('RAW_DATA', 'STG_UDEMY_COURSE_PREREQUISITES') }}
),

transformed AS (
    SELECT
        COURSE_ID AS id,
        URL::STRING AS url,
        TRIM(TITLE::STRING) AS course_name,
        TRIM(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(OBJECTIVES_SUMMARY::VARCHAR, '\\n', ' '),
                '\\r', ' '
                ),
            '\\t', ' '
            )
        ) AS description,
        NULLIF(TRIM(PREREQUISITES::STRING), '') AS prerequisites,
        CASE 
            WHEN PREREQUISITES IS NULL OR TRIM(PREREQUISITES) = 'No prerequisites required' THEN FALSE
            ELSE TRUE
        END AS has_prerequisites,
        NULLIF(TRIM(SKILLS::STRING), '') AS skills,
        TRIM(INSTRUCTIONAL_LEVEL::STRING) AS level,
        CASE
            WHEN DETECTED_LANGUAGE LIKE '%English%' THEN 'ENGLISH'
            ELSE 'OTHERS'
        END AS language,
        CASE
            WHEN CONTENT_INFO IS NOT NULL THEN
                REGEXP_SUBSTR(CONTENT_INFO::VARCHAR, '[0-9]+(\.[0-9]+)?') || ' ' ||
                CASE
                    WHEN CONTENT_INFO LIKE '%hour%' THEN 'hours'
                    WHEN CONTENT_INFO LIKE '%min%' THEN 'minutes'
                    WHEN CONTENT_INFO LIKE '%question%' THEN 'questions'
                    ELSE 'hours'
                END
            ELSE 'unknown'
        END AS duration,
        CASE
        WHEN CONTENT_INFO IS NOT NULL AND TRIM(CONTENT_INFO) LIKE '%total hour%' THEN
            TRY_CAST(REGEXP_SUBSTR(CONTENT_INFO, '[0-9]+(\.[0-9]+)?') AS FLOAT)
        WHEN CONTENT_INFO IS NOT NULL AND TRIM(CONTENT_INFO) LIKE '%total min%' AND TRIM(CONTENT_INFO) NOT LIKE             '%total hour%' THEN
            TRY_CAST(REGEXP_SUBSTR(CONTENT_INFO, '[0-9]+(\.[0-9]+)?') AS FLOAT) / 60
        WHEN CONTENT_INFO IS NOT NULL AND TRIM(CONTENT_INFO) LIKE '%question%' AND TRIM(CONTENT_INFO) NOT LIKE              '%total hour%' THEN
            TRY_CAST(REGEXP_SUBSTR(CONTENT_INFO, '[0-9]+(\.[0-9]+)?') AS FLOAT) / 60
        ELSE NULL
    END AS duration_hours,
        COALESCE(TRY_CAST(RATING::VARCHAR AS FLOAT), -1) AS rating,
        'Udemy' AS source,
        CURRENT_TIMESTAMP AS ingestion_time
    FROM source
)

SELECT * FROM transformed