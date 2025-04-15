# File: backend/services/skill_service.py
import logging
from backend.database import get_snowflake_connection

# Set up logger
logger = logging.getLogger(__name__)

def get_top_skills_for_role(role):
    """
    Get the top 5 skills for a specific role using Snowflake Cortex.
    
    Args:
        role (str): The target role to get skills for
        
    Returns:
        list: A list of the top skills for the role
    """
    logger.info(f"Getting top skills for role: {role}")
    
    conn = None
    cur = None
    
    try:
        conn = get_snowflake_connection()
        logger.debug("Snowflake connection established")
        cur = conn.cursor()
        
        # Use a specified model for consistent results
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large2',
            'List the top 5 most important technical skills for a {role} in 2025, separated by commas. Keep skill names short and simple. For example: Python, SQL, AWS, Docker, Kubernetes'
        ) AS skills;
        """
        
        logger.debug(f"Executing skills query: {query}")
        cur.execute(query)
        result = cur.fetchone()[0]
        logger.debug(f"Skills query result: {result}")
        
        # Process the comma-separated list
        if result:
            # Clean up the skills list and ensure proper formatting
            skills = []
            for skill in result.split(','):
                skill = skill.strip()
                # Skip empty skills
                if not skill:
                    continue
                # Fix any parenthesis issues
                if '(' in skill and ')' not in skill:
                    skill = skill.replace('(', '')
                if ')' in skill and '(' not in skill:
                    skill = skill.replace(')', '')
                skills.append(skill)
            
            logger.info(f"Successfully extracted skills: {skills[:5]}")
            return skills[:5]  # Ensure we only get top 5
        else:
            logger.error("Empty result from Cortex")
            raise ValueError("Could not retrieve skills from Snowflake Cortex")
            
    except Exception as e:
        logger.error(f"Error getting skills for role: {str(e)}", exc_info=True)
        raise  # Re-throw the exception to be handled by caller
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

def format_skills_for_display(skill_ratings):
    """
    Format skill ratings for display in the UI.
    
    Args:
        skill_ratings (dict): A dictionary of skill ratings
        
    Returns:
        str: HTML/Markdown formatted skill assessment
    """
    if not skill_ratings:
        return "No skills have been rated yet."
        
    skill_assessment = "### Your Current Skills Assessment\n\n"
    for skill, rating in skill_ratings.items():
        stars = "★" * rating + "☆" * (5 - rating)
        skill_assessment += f"- **{skill}**: {stars} ({rating}/5)\n"
        
    return skill_assessment