{{ config(
    materialized='table',
    schema='PROCESSED_DATA'
) }}

WITH ranked_duplicates AS (
  SELECT *,
         ROW_NUMBER() OVER (
           PARTITION BY COMPANY_REPORTED, BODY_TEXT, SOC_LABEL, TITLE_REPORTED
           ORDER BY ID
         ) AS dup_rn
  FROM {{ source('RAW_DATA', 'STG_JOB_POSTINGS') }}
  WHERE COMPANY_REPORTED IS NOT NULL
),
numbered AS (
  SELECT *,
         ROW_NUMBER() OVER (ORDER BY ID) AS row_num
  FROM ranked_duplicates
  WHERE dup_rn = 1
)

SELECT
  ID,
  COMPANY_REPORTED,
  SOC_LABEL,

  -- Cleaned BODY_TEXT renamed as BODY_TEXT
  REGEXP_REPLACE(
    TRIM(
      REGEXP_REPLACE(BODY_TEXT, '[\r\n]+', ' ')
    ),
    '[ ]{2,}', ' '
  ) AS BODY_TEXT,

  TITLE_REPORTED,

  -- Combine hard and soft skill arrays into one string
  ARRAY_TO_STRING(
    ARRAY_CAT(
      COALESCE(HARD_SKILL_LABELS, ARRAY_CONSTRUCT()),
      COALESCE(SOFT_SKILL_LABELS, ARRAY_CONSTRUCT())
    ), ', '
  ) AS SKILLS,

  row_num

FROM numbered
