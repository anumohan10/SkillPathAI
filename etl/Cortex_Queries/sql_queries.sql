USE WAREHOUSE SKILLPATH_WH

ALTER TABLE SKILLPATH_DB.RAW_DATA.UDEMY_COURSES ADD COLUMN SKILLS STRING;

CREATE OR REPLACE TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES AS 
SELECT * AS SKILLS FROM SKILLPATH_DB.RAW_DATA.UDEMY_COURSES;

ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES ADD COLUMN SKILLS STRING;


select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES

-- Create a temporary table with a few records to process
-- Set the current database, schema, and warehouse
USE DATABASE SKILLPATH_DB;
USE SCHEMA PROCESSED_DATA;
USE WAREHOUSE SKILLPATH_WH;

-- First, select a specific record to identify its values
select OBJECTIVES_SUMMARY from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES

-- First, select a specific record to identify its values
SELECT OBJECTIVES_SUMMARY 
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES


WHERE OBJECTIVES_SUMMARY IS NOT NULL AND SKILLS IS NULL
LIMIT 1;


['You will discover 100% practical ways to optimize your Google ads on autopilot without spending a penny.', 'You will never miss any optimization opportunity from your Google ads', 'You will be able to work smarter and stay productive with your Google ads']

USE DATABASE SKILLPATH_DB;
USE SCHEMA PROCESSED_DATA;
USE WAREHOUSE SKILLPATH_WH;

-- First, find a specific record - look for something with unique text
SELECT * 
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
WHERE SKILLS IS NOT NULL;

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID = 2235574;


-- Or if you found a record with a unique COURSE_NAME:
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_NAME = 'Google Ads Mastery 2023';

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;



UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 1 AND 1000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 2762 AND 1000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 1000001 AND 2000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;





UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 2000001 AND 3000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 3000001 AND 4000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract the skills from this course objectives summary. Only return a comma-separated list of skills: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 4000001 AND 4582612
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;

Select  SKILLS from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES;

Select  * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES ;



CREATE OR REPLACE TABLE SKILLPATH_DB.RAW_DATA.UDACITY_COURSES_NEW (
    URL STRING,
    Course_Name STRING,
    Description STRING,
    Level STRING,
    Prerequisites STRING,
    Duration STRING,
    Language STRING,
    Skills STRING,
    Rating STRING
);



CREATE TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE AS 
SELECT * FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES 
LIMIT 100;

select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE 



DESCRIBE table SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE 



-- 1. Add missing columns only if they don't exist
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE ADD COLUMN IF NOT EXISTS "Time Stamp" TIMESTAMP;
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE ADD COLUMN IF NOT EXISTS "Course ID" STRING;

-- 2. Ensure Platform is 'Udemy' for all records
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SET Platform = 'Udemy';

-- 3. Update Time Stamp with the current timestamp
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SET "Time Stamp" = CURRENT_TIMESTAMP;

-- 4. Assign sequential Course IDs correctly using a temporary table
CREATE OR REPLACE TEMP TABLE temp_course_id AS 
SELECT TITLE, 'U' || ROW_NUMBER() OVER (ORDER BY TITLE) AS new_course_id
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE;

-- 5. Merge the new Course IDs into the original table
MERGE INTO SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE AS target
USING temp_course_id AS source
ON target.TITLE = source.TITLE
WHEN MATCHED THEN 
UPDATE SET target."Course ID" = source.new_course_id;

-- 6. Drop unnecessary columns (confirmed from DESC TABLE output)
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
DROP COLUMN IF EXISTS 
    COURSE_ID, IS_PAID, IMAGE_480X270, PUBLISHED_TITLE, HEADLINE, 
    NUM_SUBSCRIBERS, AVG_RATING, AVG_RATING_RECENT, NUM_REVIEWS, 
    NUM_PUBLISHED_LECTURES, NUM_PUBLISHED_PRACTICE_TESTS, 
    HAS_CLOSED_CAPTION, CREATED_AT, PUBLISHED_AT, 
    IS_RECENTLY_PUBLISHED, LAST_UPDATE_DATE, CATEGORY;



-- 1. Rename existing columns to match the required format
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE RENAME COLUMN OBJECTIVES_SUMMARY TO "Description";
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE RENAME COLUMN INSTRUCTIONAL_LEVEL TO "Level";
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE RENAME COLUMN CONTENT_INFO TO "Duration";

-- 2. Add missing columns if they do not exist
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE ADD COLUMN IF NOT EXISTS "Pre-Requisites" STRING;
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE ADD COLUMN IF NOT EXISTS PRICE STRING;

-- 3. Set default values for new columns
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SET PRICE = '$10';

-- 4. Verify structure after changes
DESC TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE;


select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SET URL = 'https://www.udemy.com' || URL;

ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ADD COLUMN embeddings ARRAY;


ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
RENAME COLUMN "Level" TO SKILL_LEVEL;


ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE 
DROP COLUMN IF EXISTS embeddings;

ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE 
ADD COLUMN embeddings VECTOR(FLOAT, 768);

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SET embeddings = SNOWFLAKE.CORTEX.EMBED_TEXT_768(
    'snowflake-arctic-embed-m-v1.5', 
    "URL" || ' ' || TITLE || ' ' || INSTRUCTORS || ' ' || RATING || ' ' || 
    SKILL_LEVEL || ' ' || "Description" || ' ' || "Duration" || ' ' || SKILLS || ' ' || 
    PLATFORM || ' ' || "Time Stamp" || ' ' || "Course ID" || ' ' || "Pre-Requisites" || ' ' || PRICE
);



SELECT TITLE, URL, PRICE, 
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', 'I want to become a SEO Specialist')) 
            AS similarity_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 5;


SELECT * FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
WHERE LOWER(TITLE) LIKE '%seo%' OR LOWER("Description") LIKE '%seo%'
LIMIT 10;


SELECT TITLE, URL, PRICE, 
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', 'I want to become an SEO Specialist')) 
            AS similarity_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 10;


SELECT TITLE, URL, PRICE, 
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', 
                SKILLS || ' ' || TITLE || ' ' || "Description"
            )) AS similarity_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 5;


SELECT TITLE, URL, PRICE, 
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', 'I want to become a Data Scientist')) 
            AS similarity_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 5;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SET embeddings = SNOWFLAKE.CORTEX.EMBED_TEXT_768(
    'e5-base-v2',  -- Using a retrieval-optimized model
    TITLE || ' ' || SKILLS || ' ' || "Description"
);

select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SELECT *,
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                SKILLS || ' ' || TITLE || ' ' || "Description" || ' ' || "SKILL_LEVEL" ||' ' || RATING ||' ' || "Duration" || ' ' || PRICE
            )) AS similarity_score 
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 5;


SELECT TITLE, URL, PRICE, 
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                'SEO Specialist career guide with digital marketing')
            ) AS similarity_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 5;


SELECT similarity_score, COUNT(*) 
FROM (
    SELECT VECTOR_COSINE_SIMILARITY(embeddings, 
                SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                    'I want to become an SEO Specialist and I am new to it')) AS similarity_score
    FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
)
GROUP BY similarity_score
ORDER BY similarity_score DESC;


SELECT TITLE, URL, PRICE, 
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                'Advanced SEO Specialist training course with marketing analytics and keyword research')
            ) AS similarity_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 5;





SELECT *, 
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                'I want to become a SEO Specialist and I am new to it')
            ) AS similarity_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY similarity_score DESC
LIMIT 5;

SELECT *,
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                'I want to become a SEO Specialist and I am new to it')
            ) AS similarity_score,
       RATING,
       (VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                'I want to become a SEO Specialist and I am new to it')
            ) * 0.7 + (RATING / 5.0) * 0.3) AS hybrid_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY hybrid_score DESC
LIMIT 5;


SELECT TITLE, URL, PRICE, SKILLS, "Description"
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
WHERE LOWER(TITLE) LIKE '%data science%' 
   OR LOWER(TITLE) LIKE '%machine learning%' 
   OR LOWER("Description") LIKE '%python%' 
   OR LOWER(SKILLS) LIKE '%ai%' 
   OR LOWER(SKILLS) LIKE '%data%'
LIMIT 10;


SELECT * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES limit 100;

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract a concise, comma-separated list of technical or professional skills from the following course objective summary. Do not include full sentences or general course goals. Only list actual skills (e.g., Excel, Data Analysis, Agile, JavaScript): ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 4000001 AND 4582612
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;





ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
ADD COLUMN SKILLS_1 STRING;

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS_1 = SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large2',
    'Extract a concise, comma-separated list of technical or professional skills from the following course objective summary. Do not include full sentences or general course goals. Only list actual skills (e.g., Excel, Data Analysis, Agile, JavaScript): ' || OBJECTIVES_SUMMARY || TITLE
)
WHERE COURSE_ID BETWEEN 0 AND 100000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS_1 IS NULL;


select TITLE,objectives_summary, skills, skills_1, skills_2, skills_3, skills_4 from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES WHERE COURSE_ID BETWEEN 0 AND 100000



SELECT * 
FROM SNOWFLAKE.CORTEX.LIST_MODELS();


SELECT MODEL_NAME, PROVIDER, TASK_TYPE
FROM SNOWFLAKE.CORTEX.INFORMATION_SCHEMA.AI_MODELS
WHERE TASK_TYPE = 'TEXT_GENERATION';


ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
ADD COLUMN SKILLS_4 STRING;

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS_2 = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Based on the following course objective summary, extract the 1–2 most relevant technical or professional skills. \
Even if no skills are directly mentioned, infer the best possible related skills based on context. \
Return only a concise, comma-separated list of skills. Do not include explanations or full sentences: ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 0 AND 100000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS_2 IS NULL;



UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Given the following course title and objective summary, extract the most relevant technical or professional skills. \
If the objective summary lacks detail, use the title to infer skills. \
Return only a concise, comma-separated list of skills (e.g., Excel, Data Analysis, Agile, JavaScript). \
Do not include full sentences or general goals. \
Course Info: ' || TITLE || '. ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 2762 AND 1000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;

ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
DROP COLUMN SKILLS_4;

ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
ADD COLUMN SKILLS STRING;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Given the following course title and objective summary, extract the most relevant technical or professional skills. \
If the objective summary lacks detail, use the title to infer skills. \
Return only a concise, comma-separated list of skills (e.g., Excel, Data Analysis, Agile, JavaScript). \
Do not include full sentences or general goals. \
Course Info: ' || TITLE || '. ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 1000001 AND 2000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;

------

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Given the following course title and objective summary, extract the most relevant technical or professional skills. \
If the objective summary lacks detail, use the title to infer skills. \
Return only a concise, comma-separated list of skills (e.g., Excel, Data Analysis, Agile, JavaScript). \
Do not include full sentences or general goals. \
Course Info: ' || TITLE || '. ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 2000001 AND 3000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;
-----

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Given the following course title and objective summary, extract the most relevant technical or professional skills. \
If the objective summary lacks detail, use the title to infer skills. \
Return only a concise, comma-separated list of skills (e.g., Excel, Data Analysis, Agile, JavaScript). \
Do not include full sentences or general goals. \
Course Info: ' || TITLE || '. ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 3000001 AND 4000000
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;

------------

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Given the following course title and objective summary, extract the most relevant technical or professional skills. \
If the objective summary lacks detail, use the title to infer skills. \
Return only a concise, comma-separated list of skills (e.g., Excel, Data Analysis, Agile, JavaScript). \
Do not include full sentences or general goals. \
Course Info: ' || TITLE || '. ' || OBJECTIVES_SUMMARY
)
WHERE COURSE_ID BETWEEN 4000001 AND 4582612
AND OBJECTIVES_SUMMARY IS NOT NULL 
AND SKILLS IS NULL;


select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES where SKILLS is NULL

select * from  SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE

UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
SET SKILLS = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Given the following course title and objective summary, extract the most relevant technical or professional skills. \
  If the objective summary lacks detail, use the title to infer skills. \
  Return only a concise, comma-separated list of skills (e.g., Excel, Data Analysis, Agile, JavaScript). \
  Do not include full sentences or general goals. \
  Course Info: ' || TITLE || '. ' || "Description"
)
WHERE "Description" IS NOT NULL
AND SKILLS IS NULL;


ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ADD COLUMN SKILLS STRING;

ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
DROP COLUMN SKILLS;

select * from SKILLPATH_DB.RAW_DATA.COURSERA_COURSES  
select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES


CREATE TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES;


select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES limit 100



SELECT *,
       VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                'I want to become a SEO Specialist and I am new to it')
            ) AS similarity_score,
       RATING,
       (VECTOR_COSINE_SIMILARITY(embeddings, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', 
                'I want to become a SEO Specialist and I am new to it')
            ) * 0.7 + (RATING / 5.0) * 0.3) AS hybrid_score
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES_SAMPLE
ORDER BY hybrid_score DESC
LIMIT 5;