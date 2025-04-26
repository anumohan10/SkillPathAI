# File: backend/services/course_service.py
import json
import logging
import pandas as pd
from backend.database import get_snowflake_connection

# Set up logger
logger = logging.getLogger(__name__)

def get_course_recommendations(target_role, user_id=None, resume_id=None):
    """
    Get recommended courses using the Snowflake Cortex Search query with specific service,
    taking into account either missing skills or skill ratings for query focus.
    """
    logger.info(f"Getting recommended courses for role: {target_role}")
    conn = None
    cur = None

    try:
        # Establish connection and context
        conn = get_snowflake_connection()
        if not conn:
            raise ConnectionError("Could not connect to Snowflake")
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE();")
        db, schema, role = cur.fetchone()
        logger.info(f"Connected to: Database={db}, Schema={schema}, Role={role}")

        service_name = 'SKILLPATH_SEARCH_POC'
        skill_query_text = ""
        missing_skills = []
        ratings_dict = {}

        # 1) Use missing skills if provided
        if resume_id:
            try:
                cur.execute(f"""
                SELECT TARGET_ROLE, MISSING_SKILLS
                FROM SKILLPATH_DB.PUBLIC.RESUMES
                WHERE ID = '{resume_id}'
                """)
                tgt, raw_missing = cur.fetchone() or (None, None)
                if raw_missing:
                    missing_skills = json.loads(raw_missing) if isinstance(raw_missing, str) else raw_missing
                    if missing_skills:
                        skill_query_text = (
                            f". My main skill gaps are: {', '.join(missing_skills[:5])}. Please recommend beginner, intermediate, and advanced-level courses that cover these skills, including practical and degree-level options where available."
                        )
                        logger.debug(f"Using missing skills for query: {skill_query_text}")
            except Exception:
                logger.error("Error fetching missing skills", exc_info=True)

        # 2) If no missing skills, fetch skill ratings
        elif user_id:
            try:
                cur.execute(f"""
                SELECT SKILL_RATINGS
                FROM SKILLPATH_DB.PROCESSED_DATA.LEARNING_PATHS
                WHERE ID = '{user_id}'
                ORDER BY CREATED_AT DESC
                LIMIT 1
                """)
                raw = cur.fetchone()[0] if cur.rowcount else None
                if raw:
                    ratings_dict = json.loads(raw) if isinstance(raw, str) else raw
                    logger.debug(f"Skill ratings fetched: {ratings_dict}")

                    formatted = ", ".join([f"{skill} ({rating})" for skill, rating in ratings_dict.items()])
                    skill_query_text = (
                        f". My self-assessed skill ratings are: {formatted}. "
                        "Rating scale: 1 = No experience, 2 = Basic knowledge, 3 = Intermediate, 4 = Advanced, 5 = Expert. "
                        "If most of my skills are rated 1–2, please recommend beginner and intermediate-level courses to build a solid foundation. "
                        "If I have some skills rated 3–5, include advanced-level, Nanodegree, or specialized courses to deepen my expertise."
                    )
                    logger.debug(f"Using skill ratings for query: {skill_query_text}")
                else:
                    logger.warning("No skill ratings found for the given user ID")
            except Exception:
                logger.error("Error fetching skill ratings", exc_info=True)

        # 3) Fallback if neither missing_skills nor user_id provided
        if not skill_query_text:
            skill_query_text = (
                ". Recommend courses across beginner, intermediate, and advanced levels "
                "to help users at any stage of their learning journey."
            )
            logger.debug(f"Using default query focus: {skill_query_text}")

        # Prepare a skill ratings string for the query
        skill_ratings_str = ""
        if ratings_dict:
            skill_ratings_str = ", ".join([f"{skill} ({rating})" for skill, rating in ratings_dict.items()])
        else:
            skill_ratings_str = "Python (4), SQL (4), Machine Learning (4), Data Visualization (4), Cloud Computing (4)"
        
        # Log what we're using for the query
        logger.info(f"Using target_role: {target_role}")
        logger.info(f"Using skill_ratings: {skill_ratings_str}")
            
        # Build and execute Cortex Search query - using the exact format that works in Snowflake
        query = f"""
WITH results AS (
  SELECT 
    course.value:"COURSE_NAME"::string       AS COURSE_NAME,
    course.value:"DESCRIPTION"::string       AS DESCRIPTION,
    course.value:"SKILLS"::string            AS SKILLS,
    course.value:"PREREQUISITES"::string     AS PREREQUISITES,
    course.value:"URL"::string               AS URL,
    course.value:"LEVEL"::string             AS LEVEL,
    course.value:"PLATFORM"::string          AS PLATFORM,
    course.value                             AS RAW_JSON
  FROM TABLE(
    FLATTEN(INPUT => PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
      '{service_name}',
      CONCAT('{{
        "query": "I am targeting a career as a {target_role}. My self-assessed skill ratings are: {skill_ratings_str}. Rating scale: 1 = No experience, 2 = Basic knowledge, 3 = Intermediate, 4 = Advanced, 5 = Expert. All my skills are rated 4 or 5, indicating a strong foundation. Please recommend advanced-level, expert-level, or specialized courses. Include degree-level, Nanodegree, or professional certificate programs if available. Focus on deepening expertise, advanced projects, and real-world applications.",
        "columns": ["COURSE_NAME", "DESCRIPTION", "SKILLS", "URL", "LEVEL", "PREREQUISITES", "PLATFORM"],
        "limit": 20
      }}')
    )))
  ) AS result,
  LATERAL FLATTEN(INPUT => result.value) AS course
),

-- Categorize level into buckets
tagged AS (
  SELECT *,
    CASE 
      WHEN LOWER(LEVEL) LIKE '%advanced%' THEN 'ADVANCED'
      WHEN LOWER(LEVEL) IN ('intermediate', 'fluency') THEN 'INTERMEDIATE'
      WHEN LOWER(LEVEL) LIKE '%beginner%' THEN 'BEGINNER'
      WHEN LOWER(LEVEL) = 'all levels' THEN 'INTERMEDIATE'
      ELSE 'UNKNOWN'
    END AS LEVEL_CATEGORY
  FROM results
),

-- Rank courses within each level
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY LEVEL_CATEGORY ORDER BY COURSE_NAME) AS rn
  FROM tagged
)

-- Return up to 2 courses per level
SELECT 
  COURSE_NAME,
  DESCRIPTION,
  SKILLS,
  PREREQUISITES,
  URL,
  LEVEL,
  PLATFORM,
  LEVEL_CATEGORY
FROM ranked
WHERE rn <= 2 AND LEVEL_CATEGORY IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')
ORDER BY LEVEL_CATEGORY;
"""

        logger.debug(f"Executing search query with service {service_name}")
        cur.execute(query)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)

        # Log the distribution of courses by level category
        try:
            level_counts = df.groupby("LEVEL_CATEGORY").size().to_dict()
            logger.info(f"Courses by level returned from Snowflake: {level_counts}")
            
            # No filtering for high skill ratings - just logging
            if ratings_dict:
                # Count how many skills are rated highly (3 or above)
                high_rated_skills = sum(1 for r in ratings_dict.values() if int(r) >= 3)
                total_skills = len(ratings_dict)
                logger.info(f"User has {high_rated_skills}/{total_skills} skills rated 3 or higher")
                
                if high_rated_skills > 0:
                    logger.info("Keeping ADVANCED courses because user has skill ratings ≥ 3")
                    
                    # Extra logging to check for ADVANCED courses
                    advanced_courses = df[df["LEVEL_CATEGORY"] == "ADVANCED"]
                    if len(advanced_courses) > 0:
                        logger.info(f"Found {len(advanced_courses)} ADVANCED courses:")
                        for _, course in advanced_courses.iterrows():
                            logger.info(f"  - {course['COURSE_NAME']} [{course['LEVEL']}]")
                    else:
                        logger.warning("No ADVANCED courses returned from the query despite high skill ratings")
                        
            # Make sure we have courses from each level
            levels_needed = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
            missing_levels = [level for level in levels_needed if level not in level_counts]
            
            if missing_levels:
                logger.warning(f"Missing courses for levels: {missing_levels}")
                
                # Special case for ADVANCED courses - try to find some with an advanced-specific query if needed
                if "ADVANCED" in missing_levels and ratings_dict and any(int(r) >= 3 for r in ratings_dict.values()):
                    try:
                        logger.info("Attempting to retrieve ADVANCED courses with specialized query")
                        advanced_query = f"""
                        WITH results AS (
                          SELECT 
                            course.value:"COURSE_NAME"::string       AS COURSE_NAME,
                            course.value:"DESCRIPTION"::string       AS DESCRIPTION,
                            course.value:"SKILLS"::string            AS SKILLS,
                            course.value:"PREREQUISITES"::string     AS PREREQUISITES,
                            course.value:"URL"::string               AS URL,
                            course.value:"LEVEL"::string             AS LEVEL,
                            course.value:"PLATFORM"::string          AS PLATFORM,
                            course.value                             AS RAW_JSON
                          FROM TABLE(
                            FLATTEN(INPUT => PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                              '{service_name}',
                              '{{
                                "query": "I need ADVANCED level courses for {target_role}. ONLY return courses that are explicitly labeled as ADVANCED level. Focus only on advanced courses.",
                                "columns": ["COURSE_NAME", "DESCRIPTION", "SKILLS", "URL", "LEVEL", "PREREQUISITES", "PLATFORM"],
                                "limit": 4
                              }}'
                            )))
                          ) AS result,
                          LATERAL FLATTEN(INPUT => result.value) AS course
                        )
                        SELECT 
                          COURSE_NAME, 
                          DESCRIPTION, 
                          SKILLS,
                          PREREQUISITES,
                          URL, 
                          LEVEL, 
                          PLATFORM,
                          'ADVANCED' as LEVEL_CATEGORY
                        FROM results
                        WHERE LOWER(LEVEL) LIKE '%advanced%'
                        LIMIT 2;
                        """
                        
                        # Execute the advanced-specific query
                        cur.execute(advanced_query)
                        advanced_rows = cur.fetchall()
                        
                        if advanced_rows:
                            # Create a DataFrame with the advanced courses
                            advanced_df = pd.DataFrame(advanced_rows, columns=cols)
                            logger.info(f"Successfully retrieved {len(advanced_df)} additional ADVANCED courses")
                            
                            # Append the advanced courses to the original DataFrame
                            df = pd.concat([df, advanced_df], ignore_index=True)
                    except Exception as e:
                        logger.error(f"Error retrieving additional ADVANCED courses: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error analyzing course levels: {e}", exc_info=True)

        return df.to_dict('records')

    except Exception:
        logger.error("Error in get_course_recommendations", exc_info=True)
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()