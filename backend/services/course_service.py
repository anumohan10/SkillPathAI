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

        # Build and execute Cortex Search query
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
      '{{"query": "I am targeting a career as a {target_role}{skill_query_text}",
        "columns": ["COURSE_NAME","DESCRIPTION","SKILLS","URL","LEVEL","PREREQUISITES","PLATFORM"],
        "limit": 20}}'
    )))
  ) AS result,
  LATERAL FLATTEN(INPUT => result.value) AS course
),
tagged AS (
  SELECT *,
    CASE
      WHEN LOWER(LEVEL) LIKE '%advanced%' THEN 'ADVANCED'
      WHEN LOWER(LEVEL) IN ('intermediate','fluency') THEN 'INTERMEDIATE'
      WHEN LOWER(LEVEL) LIKE '%beginner%' THEN 'BEGINNER'
      WHEN LOWER(LEVEL) = 'all levels' THEN 'INTERMEDIATE'
      ELSE 'UNKNOWN'
    END AS LEVEL_CATEGORY
  FROM results
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY LEVEL_CATEGORY ORDER BY COURSE_NAME) AS rn
  FROM tagged
)
SELECT COURSE_NAME, DESCRIPTION, SKILLS, PREREQUISITES, URL, LEVEL, PLATFORM, LEVEL_CATEGORY
FROM ranked
WHERE rn <= 2 AND LEVEL_CATEGORY IN ('BEGINNER','INTERMEDIATE','ADVANCED')
ORDER BY LEVEL_CATEGORY;
"""

        logger.debug(f"Executing search query with service {service_name}")
        cur.execute(query)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)

        # Post-filter to remove advanced courses if all skill ratings are 1 or 2
        if ratings_dict:
            try:
                if all(int(r) <= 2 for r in ratings_dict.values()):
                    df = df[df["LEVEL_CATEGORY"].isin(["BEGINNER", "INTERMEDIATE"])]
                    logger.info("Filtered out advanced courses based on skill ratings <= 2")
            except Exception as e:
                logger.warning(f"Rating filter failed: {e}")

        return df.to_dict('records')

    except Exception:
        logger.error("Error in get_course_recommendations", exc_info=True)
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()
