WITH source AS (
    SELECT * FROM SKILLPATH_DB.RAW_DATA.STG_EDX_RAW
),

transformed AS (
    SELECT 
        UUID_STRING() AS id,
        raw_content:URL::STRING AS url,
        TRIM(raw_content:course_name::STRING) AS course_name,
        TRIM(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(raw_content:course_description::VARCHAR, '\\n', ' '),
                    '\\r', ' '
                ),
                '\\t', ' '
            )
        ) AS description,
        NULLIF(
            TRIM(
                CASE 
                    WHEN UPPER(REGEXP_REPLACE(raw_content:prerequisites::STRING, '\\.', '')) IN ('NOT FOUND', 'NONE', '') 
                    THEN NULL
                    ELSE raw_content:prerequisites::STRING
                END
            ), 
            ''
        ) AS prerequisites,
        CASE 
            WHEN UPPER(REGEXP_REPLACE(raw_content:prerequisites::STRING, '\\.', '')) IN ('NOT FOUND', 'NONE', '') 
                 OR raw_content:prerequisites::STRING IS NULL 
            THEN FALSE
            ELSE TRUE
        END AS has_prerequisites,
        NULLIF(
            REPLACE(raw_content:associated_skills::STRING, 'Not found', ''), 
            ''
        ) AS skills,
        NULLIF(
            TRIM(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(
                            REPLACE(raw_content:grow_these_skills::STRING, 'Not found', ''),
                            '\\n', ' '
                        ),
                        '\\r', ' '
                    ),
                    '\\t', ' '
                )
            ),
            ''
        ) AS grow_these_skills,
        TRIM(raw_content:institution::STRING) AS institution,
        TRIM(raw_content:level::STRING) AS level,
        CASE
            WHEN raw_content:language::STRING = 'en' THEN 'ENGLISH'
            ELSE 'OTHERS'
        END AS language,
        TRIM(raw_content:duration::STRING) AS duration,
        CASE 
            WHEN raw_content:duration::STRING LIKE '%weeks%' THEN 
                REGEXP_SUBSTR(raw_content:duration::STRING, '[0-9]+')::FLOAT * 168  -- Weeks to hours
            WHEN raw_content:duration::STRING LIKE '%week%' THEN 
                REGEXP_SUBSTR(raw_content:duration::STRING, '[0-9]+')::FLOAT * 168  -- Weeks to hours
            ELSE NULL
        END AS duration_hours,
        COALESCE(
            TRY_CAST(
                CASE 
                    WHEN raw_content:rating::STRING = 'Not found' THEN '-1'
                    ELSE raw_content:rating::STRING 
                END AS FLOAT
            ), 
            -1
        ) AS rating,
        'edX' AS source,
        CURRENT_TIMESTAMP AS ingestion_time
    FROM source
)

SELECT * FROM transformed