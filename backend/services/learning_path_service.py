# File: backend/services/learning_path_service.py
import json
import logging
import random
import pandas as pd
from backend.database import get_snowflake_connection
from backend.services.target_role_service import get_target_role
from backend.services.course_service import get_course_recommendations

# Set up logger
logger = logging.getLogger(__name__)

def get_learning_path(username="default_user"):
    """
    Get a personalized learning path for a user based on their target role.
    
    Args:
        username (str): The username to get the learning path for
        
    Returns:
        DataFrame: A DataFrame containing course recommendations
    """
    target_role = get_target_role(username)
    return get_course_recommendations(target_role)

def get_user_learning_path(user_id):
    """
    Retrieve a specific user's learning path by ID.
    
    Args:
        user_id (str/int): The ID of the learning path to retrieve
        
    Returns:
        dict: The learning path data including skill ratings
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            ID, NAME, TARGET_ROLE, SKILL_RATINGS, CREATED_AT
        FROM 
            SKILLPATH_DB.PROCESSED_DATA.LEARNING_PATHS 
        WHERE 
            ID = %s
        """
        
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        
        if not row:
            logger.warning(f"No learning path found with ID: {user_id}")
            return None
            
        # Create a dictionary from the row
        columns = [desc[0] for desc in cursor.description]
        learning_path = dict(zip(columns, row))
        
        logger.info(f"Successfully retrieved learning path for ID: {user_id}")
        return learning_path
        
    except Exception as e:
        logger.error(f"Error retrieving learning path: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def store_learning_path(data):
    """
    Store learning path details in Snowflake.

    Args:
        data (dict): Contains name, target_role, skill_ratings, etc.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Extract data from user_data
        name = data.get('name', '')
        target_role = data.get('target_role', '')
        
        # Generate random ID for the record
        record_id = random.randint(1000, 9999)
        
        # Store the record ID in data for later reference
        data['record_id'] = record_id
        
        # Get skill ratings - either from 'skill_ratings' or 'ratings'
        ratings_dict = data.get('skill_ratings', data.get('ratings', {}))
        
        if ratings_dict:
            # Convert ratings dictionary to JSON string for VARIANT column
            ratings_json = json.dumps(ratings_dict)
            
            # Use the SELECT method for PARSE_JSON compatibility
            insert_query = """
            INSERT INTO SKILLPATH_DB.PROCESSED_DATA.LEARNING_PATHS 
            (ID, NAME, TARGET_ROLE, SKILL_RATINGS, CREATED_AT)
            SELECT %s, %s, %s, PARSE_JSON(%s), CURRENT_TIMESTAMP()
            """
            
            logger.debug(f"Executing query with ratings: {insert_query}")
            logger.debug(f"Values: {record_id}, {name}, {target_role}, {ratings_json}")
            
            cursor.execute(insert_query, (record_id, name, target_role, ratings_json))
        else:
            # If no ratings, insert empty JSON for the VARIANT column
            insert_query = """
            INSERT INTO SKILLPATH_DB.PROCESSED_DATA.LEARNING_PATHS 
            (ID, NAME, TARGET_ROLE, SKILL_RATINGS, CREATED_AT)
            SELECT %s, %s, %s, PARSE_JSON('{}'), CURRENT_TIMESTAMP()
            """
            
            logger.debug(f"Executing simple query: {insert_query}")
            logger.debug(f"Values: {record_id}, {name}, {target_role}")
            
            cursor.execute(insert_query, (record_id, name, target_role))
        
        conn.commit()
        logger.info(f"Successfully stored learning path data for {name}")
        return data["record_id"]
        
    except Exception as e:
        logger.error(f"Failed to store learning path: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()
