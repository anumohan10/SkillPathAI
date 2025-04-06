
from backend.database import get_snowflake_connection
import json
import logging

logger = logging.getLogger(__name__)

def store_learning_path(data):
    """
    Store learning path details in Snowflake.

    Args:
        data (dict): Contains name, target_role, ratings, etc.
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        name = data.get("name")
        role = data.get("target_role")
        ratings_json = json.dumps(data.get("ratings", {})) 

        sql = """
        INSERT INTO SKILLPATH_DB.PROCESSED_DATA.learning_paths (NAME, TARGET_ROLE, SKILL_RATINGS)
        SELECT %s, %s, PARSE_JSON(%s)
        """
        cursor.execute(sql, (name, role, ratings_json))
        conn.commit()

        logger.info("✅ Successfully stored learning path in Snowflake.")
    except Exception as e:
        logger.error(f"❌ Failed to insert into Snowflake: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()
