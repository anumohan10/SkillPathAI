select * from SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES ;

-- Getting Skills Data in batches
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


 --concatinating https://www.udemy.com to the URL
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET URL = 'https://www.udemy.com' || URL;



-- transforming data that is in list to strings
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET 
  OBJECTIVES_SUMMARY = REPLACE(REPLACE(REPLACE(OBJECTIVES_SUMMARY, '[', ''), ']', ''), '''', ''),
  SKILLS = REPLACE(REPLACE(REPLACE(SKILLS, '[', ''), ']', ''), '''', '');




--- Detecting Language of data
ALTER TABLE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
ADD COLUMN DETECTED_LANGUAGE STRING;


--- Detecting Language of data in batches
UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET DETECTED_LANGUAGE = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Detect the language of this course. Only return one word (English, Hindi, Urdu, Spanish, etc). ' ||
  'Title: ' || TITLE || 
  '. Headline: ' || HEADLINE || 
  '. Objectives: ' || OBJECTIVES_SUMMARY
)
WHERE DETECTED_LANGUAGE IS NULL
AND  COURSE_ID BETWEEN 2762 AND 1000000
AND OBJECTIVES_SUMMARY IS NOT NULL;



UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET DETECTED_LANGUAGE = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Detect the language of this course. Only return one word (English, Hindi, Urdu, Spanish, etc). ' ||
  'Title: ' || TITLE || 
  '. Headline: ' || HEADLINE || 
  '. Objectives: ' || OBJECTIVES_SUMMARY
)
WHERE DETECTED_LANGUAGE IS NULL
AND COURSE_ID BETWEEN 1000001 AND 2000000
AND OBJECTIVES_SUMMARY IS NOT NULL;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET DETECTED_LANGUAGE = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Detect the language of this course. Only return one word (English, Hindi, Urdu, Spanish, etc). ' ||
  'Title: ' || TITLE || 
  '. Headline: ' || HEADLINE || 
  '. Objectives: ' || OBJECTIVES_SUMMARY
)
WHERE DETECTED_LANGUAGE IS NULL
AND  COURSE_ID BETWEEN 2000001 AND 3000000
AND OBJECTIVES_SUMMARY IS NOT NULL;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET DETECTED_LANGUAGE = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Detect the language of this course. Only return one word (English, Hindi, Urdu, Spanish, etc). ' ||
  'Title: ' || TITLE || 
  '. Headline: ' || HEADLINE || 
  '. Objectives: ' || OBJECTIVES_SUMMARY
)
WHERE DETECTED_LANGUAGE IS NULL
AND  COURSE_ID BETWEEN 3000001 AND 4000000
AND OBJECTIVES_SUMMARY IS NOT NULL;


UPDATE SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
SET DETECTED_LANGUAGE = SNOWFLAKE.CORTEX.COMPLETE(
  'mistral-large2',
  'Detect the language of this course. Only return one word (English, Hindi, Urdu, Spanish, etc). ' ||
  'Title: ' || TITLE || 
  '. Headline: ' || HEADLINE || 
  '. Objectives: ' || OBJECTIVES_SUMMARY
)
WHERE DETECTED_LANGUAGE IS NULL
AND  COURSE_ID BETWEEN 4000001 AND 4582612
AND OBJECTIVES_SUMMARY IS NOT NULL;

SELECT *
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
WHERE TRIM(DETECTED_LANGUAGE) ILIKE 'English' = FALSE;

SELECT 
  COUNT(*) AS total_checked
FROM SKILLPATH_DB.PROCESSED_DATA.UDEMY_COURSES
WHERE URL_ACTIVE IS NOT NULL;









