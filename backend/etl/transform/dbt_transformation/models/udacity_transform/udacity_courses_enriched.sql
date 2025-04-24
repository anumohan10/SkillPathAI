{{ config(
    materialized='table',
    schema='PROCESSED_DATA'
) }}

WITH base AS (
  SELECT 
    *,

    -- Infer course level if missing
    CASE 
      WHEN TRIM(LEVEL) = '' THEN SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large2',
        'Based on the course title and description, infer the most appropriate course level from the following options:Beginner,Intermediate,Advanced,Discovery, or Fluency. \
Choose the level that best matches the technical depth and learner background required. \
Only return the level name. \
Course Title: ' || COURSE_NAME || '. \
Description: ' || DESCRIPTION
      )
      ELSE LEVEL
    END AS FINAL_LEVEL,

    -- Infer prerequisites if missing
    CASE 
      WHEN (PREREQUISITES IS NULL OR TRIM(PREREQUISITES) = '') AND DESCRIPTION IS NOT NULL THEN SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large2',
        'Extract the specific prerequisites needed to start this course based on the title, description, and instructional level.\
        FORMAT GUIDELINES:\
        - Return ONLY a concise, comma-separated list of specific prerequisites (e.g., "Basic Python, Statistics, Git")\
        - If no clear prerequisites exist, return "No prerequisites required"\
        - For "Discovery" courses, assume no prerequisites unless explicitly stated\
        - For "Fluency" courses, include basic foundational skills relevant to the subject area\
        - For "Beginner" courses, keep prerequisites minimal or none unless explicitly mentioned\
        - For "Intermediate" courses, include foundational knowledge in the subject area\
        - For "Advanced" courses, include advanced prerequisite skills\
        - Exclude generic terms like "willingness to learn" or "dedication"\
        - Focus on technical skills, knowledge, or experience needed\
        - No sentences, explanations, or bullet points\
        COURSE INFORMATION:\
        Title: ' || COURSE_NAME || '\
        Description: ' || DESCRIPTION || '\
        Level: ' || COALESCE(LEVEL, 'Not Specified')
      )
      ELSE PREREQUISITES
    END AS FINAL_PREREQUISITES,

    -- Infer skills if missing
    CASE
      WHEN (SKILLS IS NULL OR TRIM(SKILLS) = '') AND DESCRIPTION IS NOT NULL THEN SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large2',
        'Given the following course title, description, and level, extract the most relevant technical or professional skills. \
If the description lacks detail, use the title to infer skills. \
Return only a concise, comma-separated list of skills (e.g., Python, SQL, Agile, Data Analysis). \
Do not include full sentences or general goals. \
Course Info: ' || COURSE_NAME || '. ' || DESCRIPTION || '. Level: ' || COALESCE(LEVEL, 'Not Specified')
      )
      ELSE SKILLS
    END AS FINAL_SKILLS

  FROM {{ source('RAW_DATA', 'STG_UDACITY_COURSES') }}
  WHERE DESCRIPTION IS NOT NULL
)

SELECT 
  ID,
  COURSE_NAME,
  DESCRIPTION,
  FINAL_PREREQUISITES AS PREREQUISITES,
  FINAL_SKILLS AS SKILLS,
  FINAL_LEVEL AS LEVEL,
  LANGUAGE,
  DURATION,
  DURATION_HOURS,
  RATING,
  SOURCE,
  INGESTION_TIME,
  URL,
  HAS_PREREQUISITES
FROM base