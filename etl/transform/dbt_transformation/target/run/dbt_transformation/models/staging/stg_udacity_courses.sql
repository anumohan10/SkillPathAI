
  
    

        create or replace transient table SKILLPATH_DB.RAW_DATA.stg_udacity_courses
         as
        (WITH source AS (
    SELECT * FROM SKILLPATH_DB.RAW_DATA.STG_UDACITY_RAW
),

transformed AS (
    SELECT 
        UUID_STRING() AS id,
        raw_content:URL::STRING AS url,
        TRIM(raw_content:"Course Name"::STRING) AS course_name,
        TRIM(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(raw_content:Description::VARCHAR, '\\n', ' '),
                '\\r', ' '
            ),
            '\\t', ' '
            )
        ) AS description,
        NULLIF(ARRAY_TO_STRING(SPLIT(TRIM(raw_content:Prerequisites::STRING), ','), ', '), '') AS prerequisites,
        CASE 
            WHEN raw_content:Prerequisites::STRING IS NULL OR raw_content:Prerequisites::STRING = '' THEN FALSE
            ELSE TRUE
        END AS has_prerequisites,
        NULLIF(ARRAY_TO_STRING(SPLIT(TRIM(raw_content:Skills::STRING), ', '), ', '), '') AS skills,
        TRIM(raw_content:Level::STRING) AS level,
        CASE
            WHEN raw_content:Language::STRING LIKE 'en' THEN
            'ENGLISH'
            ELSE 'OTHERS'
         END AS language,
        CONCAT(
            REGEXP_SUBSTR(raw_content:Duration::VARCHAR, '[0-9]+'), ' ',
            CASE 
                WHEN raw_content:Duration::VARCHAR LIKE 'P%M' THEN 'months'
                WHEN raw_content:Duration::VARCHAR LIKE 'P%W' THEN 'weeks'
                WHEN raw_content:Duration::VARCHAR LIKE 'PT%H' THEN 'hours'
                ELSE 'unknown'
            END
        ) AS duration,
        CASE 
            WHEN raw_content:Duration::STRING LIKE 'P%M' THEN 
                REGEXP_SUBSTR(raw_content:Duration::STRING, '[0-9]+')::FLOAT * 730  -- Months to hours
            WHEN raw_content:Duration::STRING LIKE 'P%W' THEN 
                REGEXP_SUBSTR(raw_content:Duration::STRING, '[0-9]+')::FLOAT * 168  -- Weeks to hours
            WHEN raw_content:Duration::STRING LIKE 'PT%H' THEN 
                REGEXP_SUBSTR(raw_content:Duration::STRING, '[0-9]+')::FLOAT       -- Hours
            ELSE NULL
        END AS duration_hours,
        COALESCE(TRY_CAST(raw_content:Rating::STRING AS FLOAT),-1) AS rating,
        'Udacity' AS source,
        CURRENT_TIMESTAMP AS ingestion_time
    FROM source
)

SELECT * FROM transformed
        );
      
  