{{ config(
    materialized='table',
    schema='PROCESSED_DATA'
) }}

SELECT
  ID,
  COMPANY_REPORTED,
  SOC_LABEL,
  BODY_TEXT,
  TITLE_REPORTED,

  -- Combine hard and soft skill arrays into one string
  ARRAY_TO_STRING(
    ARRAY_CAT(
      COALESCE(HARD_SKILL_LABELS, ARRAY_CONSTRUCT()),
      COALESCE(SOFT_SKILL_LABELS, ARRAY_CONSTRUCT())
    ), ', '
  ) AS SKILLS

FROM {{ source('RAW_DATA', 'STG_JOB_POSTINGS') }}

-- Only include rows with non-null COMPANY_REPORTED
WHERE COMPANY_REPORTED IS NOT NULL
