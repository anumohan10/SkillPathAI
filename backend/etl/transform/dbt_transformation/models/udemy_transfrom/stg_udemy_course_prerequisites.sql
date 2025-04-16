{{ config(materialized='incremental', unique_key='COURSE_ID') }}

{% set course_id_lower = var('course_id_lower', 0) %}
{% set course_id_upper = var('course_id_upper', 100000) %}

WITH base AS (
  SELECT 
    *,
    SNOWFLAKE.CORTEX.COMPLETE(
      'mistral-large2',
      'Extract the specific prerequisites needed to start this course based on the title, objective summary, and instructional level.\
      FORMAT GUIDELINES:\
      - Return ONLY a concise, comma-separated list of specific prerequisites (e.g., "Basic Python, Statistics, Git")\
      - If no clear prerequisites exist, return "No prerequisites required" \
      - For "Beginner Level" courses, keep prerequisites minimal or none unless explicitly mentioned\
      - For "Intermediate Level" courses, include foundational knowledge in the subject area\
      - For "Expert Level" courses, include advanced prerequisite skills\
      - For "All Levels" courses, focus on the minimal entry requirements\
      - Exclude generic terms like "willingness to learn" or "dedication"\
      - Focus on technical skills, knowledge, or experience needed\
      - No sentences, explanations, or bullet points\
      COURSE INFORMATION:\
      Title: ' || TITLE || '\
      Objectives: ' || OBJECTIVES_SUMMARY || '\
      Level: ' || INSTRUCTIONAL_LEVEL
    ) AS prerequisites
  FROM 
    {{ source('PROCESSED_DATA', 'UDEMY_COURSES') }}
  WHERE 
    COURSE_ID >= {{ course_id_lower }}
    AND COURSE_ID < {{ course_id_upper }}
    AND OBJECTIVES_SUMMARY IS NOT NULL
)

SELECT * FROM base
{% if is_incremental() %}
WHERE COURSE_ID NOT IN (SELECT COURSE_ID FROM {{ this }})
{% endif %}

