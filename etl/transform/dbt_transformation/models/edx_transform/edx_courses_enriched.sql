{{ config(
    materialized='table',
    schema='PROCESSED_DATA'
) }}

WITH base AS (
  SELECT 
    *,
    
    -- Fill in prerequisites only if NULL
    CASE 
      WHEN PREREQUISITES IS NULL AND DESCRIPTION IS NOT NULL THEN SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large2',
        'Extract the specific prerequisites needed to start this course based on the title, description, and instructional level.\
        FORMAT GUIDELINES:\
        - Return ONLY a concise, comma-separated list of specific prerequisites (e.g., "Basic Python, Statistics, Git")\
        - If no clear prerequisites exist, return "No prerequisites required"\
        - For "Beginner" courses, keep prerequisites minimal or none unless explicitly mentioned\
        - For "Intermediate" courses, include foundational knowledge in the subject area\
        - For "Advanced" courses, include advanced prerequisite skills\
        - Exclude generic terms like "willingness to learn" or "dedication"\
        - Focus on technical skills, knowledge, or experience needed\
        - No sentences, explanations, or bullet points\
        COURSE INFORMATION:\
        Title: ' || COURSE_NAME || '\
        Description: ' || DESCRIPTION || '\
        Level: ' || LEVEL
      )
      ELSE PREREQUISITES
    END AS FILLED_PREREQUISITES,

    -- Combine SKILLS and GROW_THESE_SKILLS
    TRIM(
      COALESCE(SKILLS, '') || 
      CASE 
        WHEN SKILLS IS NOT NULL AND GROW_THESE_SKILLS IS NOT NULL THEN ', '
        ELSE '' 
      END || 
      COALESCE(GROW_THESE_SKILLS, '')
    ) AS COMBINED_SKILLS,

    -- Derive skills if both SKILLS and GROW_THESE_SKILLS are empty
    CASE
      WHEN (SKILLS IS NULL OR TRIM(SKILLS) = '') 
        AND (GROW_THESE_SKILLS IS NULL OR TRIM(GROW_THESE_SKILLS) = '')
        AND DESCRIPTION IS NOT NULL THEN SNOWFLAKE.CORTEX.COMPLETE(
          'mistral-large2',
          'Based on the course title and description, extract the most relevant technical or professional skills a learner would gain. \
Return a concise, comma-separated list of skills (e.g., Excel, Data Analysis, Agile, Python). \
Avoid generic phrases and full sentences. \
Course Title: ' || COURSE_NAME || '. \
Course Description: ' || DESCRIPTION
        )
      ELSE NULL
    END AS INFERRED_SKILLS

  FROM {{ source('RAW_DATA', 'STG_EDX_COURSES') }}
  WHERE DESCRIPTION IS NOT NULL
)

SELECT 
  ID,
  COURSE_NAME,
  DESCRIPTION,
  URL,
  FILLED_PREREQUISITES AS PREREQUISITES,
  
  -- Use inferred skills only if combined_skills is empty
  CASE 
    WHEN COMBINED_SKILLS = '' OR COMBINED_SKILLS IS NULL THEN INFERRED_SKILLS
    ELSE COMBINED_SKILLS
  END AS SKILLS,

  HAS_PREREQUISITES,
  INSTITUTION,
  LEVEL,
  LANGUAGE,
  DURATION,
  DURATION_HOURS,
  RATING,
  SOURCE,
  INGESTION_TIME
FROM base
