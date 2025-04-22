# File: backend/services/career_transition_service.py
import json
import logging
import uuid
from typing import Dict, List, Tuple, Any
from backend.database import get_snowflake_connection
from backend.services.chat_service import ChatService

# Set up logger
logger = logging.getLogger(__name__)

def get_latest_resume_by_user_role(username: str, target_role: str):
    """
    Get the most recent resume for a user and target role.
    
    Args:
        username (str): The username to look up
        target_role (str): The target role
        
    Returns:
        dict: Resume data including ID and extracted skills
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Get the most recent resume entry
        query = """
        SELECT 
            ID, EXTRACTED_SKILLS, MISSING_SKILLS, TARGET_ROLE
        FROM 
            SKILLPATH_DB.PUBLIC.RESUMES 
        WHERE 
            USER_NAME = %s AND TARGET_ROLE = %s
        ORDER BY 
            CREATED_AT DESC
        LIMIT 1
        """
        
        cursor.execute(query, (username, target_role))
        row = cursor.fetchone()
        
        if not row:
            logger.warning(f"No resume found for user {username} with target role {target_role}")
            return None
            
        # Create a dictionary from the row
        columns = ["id", "extracted_skills", "missing_skills", "target_role"]
        resume_data = dict(zip(columns, row))
        
        logger.info(f"Successfully retrieved resume for user {username}")
        return resume_data
        
    except Exception as e:
        logger.error(f"Error retrieving resume: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def process_missing_skills(extracted_skills: List[str], target_role: str) -> List[str]:
    """
    Efficiently identify missing skills using LLM with improved accuracy.
    
    Args:
        extracted_skills (list): List of skills extracted from resume
        target_role (str): The target role for career transition
        
    Returns:
        list: Missing skills needed for the target role
    """
    try:
        chat_service = ChatService()
        
        # First identify skills the user already has that are relevant to the target role
        extracted_lower = [skill.lower() for skill in extracted_skills]
        role_related_skills = []
        
        # Use a more dynamic approach to identify role-related skills
        try:
            # Connect to database to get role-specific keywords
            from backend.database import get_snowflake_connection
            conn = get_snowflake_connection()
            cursor = conn.cursor()
            
            # Sanitize role name
            safe_role = target_role.replace("'", "").replace('"', "")
            
            # Query Cortex for role-related keywords
            query = f"""
            SELECT PARSE_JSON(
                SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                    'SKILLPATH_SEARCH_POC',
                    '{{
                        "query": "What are 10 keywords that would identify skills related to a {safe_role} role? Return just a JSON array of single words.",
                        "limit": 1
                    }}'
                )
            )['results'][0]['content']::STRING as KEYWORDS;
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result[0]:
                # Try to extract keywords
                import json
                import re
                
                # Try JSON parsing first
                keywords = []
                try:
                    json_match = re.search(r'\[(.*?)\]', result[0], re.DOTALL)
                    if json_match:
                        keywords_json = f"[{json_match.group(1)}]"
                        keywords = json.loads(keywords_json)
                except:
                    # If JSON parsing fails, try simple keyword extraction
                    keywords = [w.strip().lower() for w in result[0].split(',')]
                
                # Use keywords to identify related skills
                if keywords:
                    for skill in extracted_skills:
                        skill_lower = skill.lower()
                        if any(keyword.lower() in skill_lower for keyword in keywords):
                            role_related_skills.append(skill)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            # Fallback approach if the dynamic one fails
            logger.warning(f"Dynamic keyword extraction failed: {str(e)}")
            
            # Simple fallback based on role name words
            role_words = [word.lower() for word in target_role.split() if len(word) > 3]
            
            for skill in extracted_skills:
                skill_lower = skill.lower()
                # Check if any role word appears in the skill
                if any(word in skill_lower for word in role_words):
                    role_related_skills.append(skill)
        
        # Create a more targeted prompt with specific guidance - but now considering their existing related skills
        prompt = (
            f"You are a career counselor in 2025 specializing in {target_role} career transitions. "
            f"The candidate has the following skills from their resume: {', '.join(extracted_skills[:20])}. "
            f"Of these skills, I've identified these as relevant to the {target_role} role: {', '.join(role_related_skills)}.\n\n"
            f"Given their current skills and the requirements of a {target_role} role in 2025:\n\n"
            f"1. Identify 4-6 CRUCIAL technical skills they're still missing (skills they DON'T already have)\n"
            f"2. Focus on specific technologies, tools, and methodologies rather than general abilities\n"
            f"3. Prioritize skills that would have the highest impact in landing a {target_role} job\n"
            f"4. Do NOT include skills they already have (for example, if they know 'Machine Learning', don't list that)\n\n"
            f"Return ONLY a JSON array of specific skill names they are missing, with NO explanations or additional text."
        )
        
        # Use a more comprehensive approach to get better results
        # ChatService.get_llm_response returns a tuple of (success_flag, response_text)
        success, response = chat_service.get_llm_response(prompt)
        
        # Check if the response was successful or contains an error message
        if not success or "having trouble" in response or "sorry" in response.lower() or "I can't" in response:
            # Make a second attempt with a simpler, more direct prompt
            simple_prompt = (
                f"List the top 5 most important technical skills needed for a {target_role} position in 2025 "
                f"that are not in this list: {', '.join(extracted_skills[:15])}. "
                f"Return only a JSON array."
            )
            
            success, response = chat_service.get_llm_response(simple_prompt)
            
            # If still getting errors, use role-specific defaults
            if not success or "having trouble" in response or "sorry" in response.lower() or "I can't" in response:
                return get_default_skills_for_role(target_role, extracted_skills)
        
        # Extract JSON list from response
        import re
        import json  # Make sure json is imported here
        
        json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
        
        if json_match:
            try:
                skills_json = f"[{json_match.group(1)}]"
                skills = json.loads(skills_json)
                if skills and isinstance(skills, list) and len(skills) > 0:
                    # Verify that suggested skills are not already in extracted skills
                    skills = [skill for skill in skills if not any(extracted.lower() == skill.lower() for extracted in extracted_skills)]
                    return skills if skills else get_default_skills_for_role(target_role, extracted_skills)
                else:
                    # Invalid or empty skills list
                    return get_default_skills_for_role(target_role, extracted_skills)
            except Exception as e:  # Broader exception to catch any JSON parsing issues
                logger.error(f"Error parsing JSON from response: {e}")
                # JSON parsing failed
                return get_default_skills_for_role(target_role, extracted_skills)
        else:
            # Try line-by-line parsing as fallback
            skills = []
            for line in response.split('\n'):
                line = line.strip(' "\',-.')
                if line and len(line) > 3 and not line.startswith('[') and not line.endswith(']'):
                    if not any(extracted.lower() == line.lower() for extracted in extracted_skills):
                        skills.append(line)
            
            if skills:
                return skills[:5]  # Limit to 5 skills
            else:
                return get_default_skills_for_role(target_role, extracted_skills)
            
    except Exception as e:
        logger.error(f"Error identifying missing skills: {str(e)}")
        return get_default_skills_for_role(target_role, extracted_skills)

def get_default_skills_for_role(role: str, extracted_skills: List[str] = None) -> List[str]:
    """
    Use direct LLM query to get role skills for the target role.
    Now fully dynamic with no hardcoded fallbacks.
    
    Args:
        role (str): The target role
        extracted_skills (list, optional): List of skills already extracted from resume
        
    Returns:
        list: Role-appropriate skills or error message
    """
    try:
        # Use the ChatService for a dynamic approach
        from backend.services.chat_service import ChatService
        chat_service = ChatService()
        
        # Create a straightforward prompt asking for skills
        prompt = (
            f"You are a career advisor in 2025 specializing in {role} roles. "
            f"A job candidate has these skills: {', '.join(extracted_skills[:10] if extracted_skills else ['No skills available'])}. "
            f"Identify the 5 most important technical skills they still need to develop "
            f"for a {role} position that are not already in their skill set. "
            f"Return ONLY a JSON array of skill names without any additional text."
        )
        
        # Get response from LLM
        success, response = chat_service.get_llm_response(prompt)
        
        if not success:
            logger.error("LLM failed to generate a response for default skills")
            return ["Sorry, I couldn't analyze your skill gaps at this time. Please try again later."]
            
        # Try to extract skills from the response
        import json
        import re
        
        # First try to parse as JSON
        json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
        if json_match:
            try:
                skills_json = f"[{json_match.group(1)}]"
                skills = json.loads(skills_json)
                if skills and isinstance(skills, list) and len(skills) > 0:
                    # Filter out any skills they might already have
                    if extracted_skills:
                        skills = [s for s in skills if isinstance(s, str) and len(s.strip()) > 2 and 
                                  not any(s.lower() in e.lower() or e.lower() in s.lower() for e in extracted_skills)]
                    else:
                        skills = [s for s in skills if isinstance(s, str) and len(s.strip()) > 2]
                        
                    if skills:
                        return skills[:5]
            except Exception as e:
                logger.error(f"Error parsing JSON skills: {e}")
        
        # If JSON parsing failed, try line-by-line extraction
        skills = []
        for line in response.split('\n'):
            line = line.strip(' "\',-.*•1234567890.[](){}"')
            if line and len(line) > 3 and not line.startswith('#'):
                skills.append(line)
        
        # Filter and return skills if we found any
        if skills:
            if extracted_skills:
                skills = [s for s in skills if not any(s.lower() in e.lower() or e.lower() in s.lower() 
                         for e in extracted_skills)]
            return skills[:5]
        
        # Try one more time with an even simpler prompt
        prompt = f"What are the 5 essential skills needed for a {role} role in 2025? Return only a JSON array."
        success, response = chat_service.get_llm_response(prompt)
        
        if success:
            # Try to extract skills from the response
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            if json_match:
                try:
                    skills_json = f"[{json_match.group(1)}]"
                    skills = json.loads(skills_json)
                    if skills and isinstance(skills, list) and len(skills) > 0:
                        return [s for s in skills if isinstance(s, str)][:5]
                except Exception as e:
                    logger.warning(f"Error parsing JSON from second attempt: {e}")
            
            # Try extracting from text if JSON failed
            skills = []
            for line in response.split('\n'):
                line = line.strip(' "\',-.*•1234567890.[](){}"')
                if line and len(line) > 3 and not line.startswith('#'):
                    skills.append(line)
            
            if skills:
                return skills[:5]
        
        # If we've reached this point, all LLM calls failed
        logger.error("All LLM attempts failed to extract valid skills")
        return ["Sorry, I couldn't analyze your skill gaps at this time. Please try again later."]
        
    except Exception as e:
        logger.error(f"Error getting skills via LLM: {str(e)}")
        return ["Sorry, I couldn't analyze your skill gaps at this time. Please try again later."]

def fallback_llm_skills_for_role(role: str, extracted_skills: List[str] = None) -> List[str]:
    """
    Use the LLM directly to suggest skills when other methods fail.
    No hardcoded skills or keywords.
    
    Args:
        role (str): The target role
        extracted_skills (list, optional): Skills already on the resume
        
    Returns:
        list: Missing skills needed for the role or error message
    """
    logger.info(f"Using fallback LLM for {role} with {len(extracted_skills) if extracted_skills else 0} extracted skills")
    try:
        chat_service = ChatService()
        
        # Create a prompt that lets the LLM determine skill relevance and gaps 
        # without any hardcoded keywords or categories
        prompt = (
            f"As a career advisor for {role} roles in 2025, analyze the candidate's current skills: "
            f"{', '.join(extracted_skills[:15] if extracted_skills else ['No skills provided'])}.\n\n"
            f"First, determine if they already have strong role-relevant skills. "
            f"If they have strong role-relevant skills, suggest 5 specialized/advanced skills to complement their expertise. "
            f"If they lack role-relevant skills, suggest 5 foundational skills for this role. "
            f"Return ONLY a JSON array of skill names, no explanation or categorization."
        )
        
        # Get LLM response
        success, response = chat_service.get_llm_response(prompt)
        
        if not success:
            logger.error("LLM failed to provide a response")
            return ["Sorry, I couldn't analyze your skill gaps at this time. Please try again later."]
            
        # Parse response
        import json
        import re
        
        # Try to find JSON array
        json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
        if json_match:
            try:
                skills_json = f"[{json_match.group(1)}]"
                skills = json.loads(skills_json)
                if isinstance(skills, list) and len(skills) > 0:
                    # Filter to ensure we return only valid string skills
                    valid_skills = [s for s in skills if isinstance(s, str) and len(s.strip()) > 2]
                    if valid_skills:
                        return valid_skills[:5]
            except Exception as e:
                logger.error(f"Error parsing JSON from LLM response: {e}")
        
        # If JSON parsing failed, try line-by-line extraction
        skills = []
        for line in response.split('\n'):
            # Clean the line of common formatting characters
            line = line.strip(' "\',-.*•0123456789')
            if line and len(line) > 3 and not line.startswith('[') and not line.endswith(']'):
                skills.append(line)
        
        # If no skills were found, return an error message
        if not skills:
            logger.error("No skills were extracted from LLM response")
            return ["Sorry, I couldn't analyze your skill gaps at this time. Please try again later."]
        
        return skills[:5]
        
    except Exception as e:
        logger.error(f"Fallback LLM skills error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a clear error message
        return ["Sorry, I couldn't analyze your skill gaps at this time. Please try again later."]

def store_career_analysis(username: str, resume_text: str, extracted_skills: List[str], 
                          target_role: str, missing_skills: List[str] = None) -> str:
    """
    Store career transition analysis in the database with optimized approach.
    Ensures missing skills are always identified and stored.
    
    Args:
        username (str): The username
        resume_text (str): The resume text
        extracted_skills (list): List of extracted skills
        target_role (str): The target role for transition
        missing_skills (list, optional): Missing skills if already identified
        
    Returns:
        str: The ID of the stored record
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Generate ID
        record_id = str(uuid.uuid4())
        
        # If missing skills not provided, identify them
        if not missing_skills or len(missing_skills) == 0:
            logger.info(f"Missing skills not provided for {username}, generating them now")
            missing_skills = process_missing_skills(extracted_skills, target_role)
            
            # Ensure we got valid missing skills
            if not missing_skills or len(missing_skills) == 0:
                logger.warning(f"Failed to generate missing skills for {username}, using fallback")
                # Generate some basic fallback skills to avoid null values
                missing_skills = get_default_skills_for_role(target_role, extracted_skills)
        
        # Validate missing skills - ensure it's not an error message
        error_indicators = ["sorry", "trouble", "try again", "error", "couldn't"]
        if any(any(indicator in skill.lower() for indicator in error_indicators) for skill in missing_skills):
            logger.warning(f"Missing skills contains error messages for {username}, using fallback")
            # Use fallback if we detected error messages in the missing skills
            missing_skills = get_default_skills_for_role(target_role, extracted_skills)
        
        # Clean resume text for SQL insertion
        cleaned_resume_text = resume_text.replace("'", "''")
        
        # Insert with optimized query using PARSE_JSON
        query = """
        INSERT INTO SKILLPATH_DB.PUBLIC.RESUMES 
        (id, user_name, resume_text, extracted_skills, target_role, missing_skills)
        SELECT %s, %s, %s, PARSE_JSON(%s), %s, PARSE_JSON(%s)
        """
        
        cursor.execute(
            query,
            (
                record_id,
                username,
                cleaned_resume_text,
                json.dumps(extracted_skills),
                target_role,
                json.dumps(missing_skills)
            )
        )
        
        conn.commit()
        logger.info(f"Successfully stored career analysis with missing skills for {username}")
        return record_id
        
    except Exception as e:
        logger.error(f"Error storing career analysis: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_career_transition_courses(target_role: str, missing_skills: List[str], limit: int = 6) -> Dict:
    """
    Get course recommendations for career transition with direct skill targeting.
    This is a streamlined version compared to the standard course service.
    
    Args:
        target_role (str): The target role
        missing_skills (list): List of missing skills to focus on
        limit (int): Maximum number of courses to return
        
    Returns:
        dict: Dictionary with course information
    """
    cursor = None
    conn = None
    
    try:
        # Validate missing_skills to prevent SQL errors
        valid_missing_skills = []
        if missing_skills and isinstance(missing_skills, list):
            # Filter out any non-string skills or skills containing problematic characters
            for skill in missing_skills:
                if isinstance(skill, str) and len(skill) > 0:
                    # Remove quotes and SQL-problematic characters
                    cleaned_skill = skill.replace("'", "").replace('"', "").replace(";", "").strip()
                    if cleaned_skill and len(cleaned_skill) > 2:
                        valid_missing_skills.append(cleaned_skill)
        
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Create optimized skills focus - only if we have valid skills
        skills_focus = ""
        if valid_missing_skills:
            # Take only top 3 skills for more focused results
            skills_str = ", ".join(valid_missing_skills[:3])
            skills_focus = f" Focus on courses that teach {skills_str}."
        
        # Sanitize target role
        safe_target_role = target_role.replace("'", "").replace('"', "").replace(";", "")
        
        # Use direct search query with improved level categorization
        query = f"""
        SELECT
          course.value:"COURSE_NAME"::string AS COURSE_NAME,
          course.value:"DESCRIPTION"::string AS DESCRIPTION,
          course.value:"SKILLS"::string AS SKILLS,
          course.value:"URL"::string AS URL,
          course.value:"LEVEL"::string AS LEVEL,
          course.value:"PLATFORM"::string AS PLATFORM,
          CASE
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%beginner%' THEN 'BEGINNER'
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%intermediate%' THEN 'INTERMEDIATE'
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%advanced%' THEN 'ADVANCED'
            -- For "All Levels" courses, initially categorize based on course name
            -- The actual distribution will happen in the post-processing
            WHEN LOWER(course.value:"LEVEL"::string) LIKE '%all%level%' 
              OR LOWER(course.value:"LEVEL"::string) LIKE '%all-level%' THEN 'ALL_LEVELS'
            -- For other uncategorized courses, use ADVANCED as default
            ELSE 'ADVANCED'
          END AS LEVEL_CATEGORY
        FROM
          TABLE(
            FLATTEN(
              INPUT => PARSE_JSON(
                SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                  'SKILLPATH_SEARCH_POC',
                  '{{
                    "query": "Show me the best courses for {safe_target_role} including beginner to advanced levels.{skills_focus}",
                    "columns": ["COURSE_NAME", "DESCRIPTION", "SKILLS", "URL", "LEVEL", "PLATFORM"],
                    "limit": {limit}
                  }}'
                )
              ):"results"
            )
          ) AS course
        WHERE
          course.value:"COURSE_NAME"::string IS NOT NULL
          AND course.value:"URL"::string IS NOT NULL
        ORDER BY
          LEVEL_CATEGORY;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Process results
        columns = [desc[0] for desc in cursor.description]
        courses = []
        
        for row in rows:
            course_dict = dict(zip(columns, row))
            courses.append(course_dict)
        
        # Distribute "ALL_LEVELS" courses among the three difficulty levels
        all_levels_courses = [c for c in courses if c.get("LEVEL_CATEGORY") == "ALL_LEVELS"]
        if all_levels_courses:
            # Count how many we have in each category already
            beginner_count = len([c for c in courses if c.get("LEVEL_CATEGORY") == "BEGINNER"])
            intermediate_count = len([c for c in courses if c.get("LEVEL_CATEGORY") == "INTERMEDIATE"])
            advanced_count = len([c for c in courses if c.get("LEVEL_CATEGORY") == "ADVANCED"])
            
            # Determine which levels need more courses
            level_counts = {
                "BEGINNER": beginner_count,
                "INTERMEDIATE": intermediate_count,
                "ADVANCED": advanced_count
            }
            
            # Sort levels by which needs the most courses
            sorted_levels = sorted(level_counts.items(), key=lambda x: x[1])
            
            # Distribute "ALL_LEVELS" courses to the categories that need them most
            for i, course in enumerate(all_levels_courses):
                # Try to make a smart assignment first based on course name
                course_name = course.get("COURSE_NAME", "").lower()
                skills = course.get("SKILLS", "").lower()
                description = course.get("DESCRIPTION", "").lower()
                
                # Check for beginner indicators
                beginner_indicators = ["intro", "beginning", "basic", "fundamental", "foundation", "start"]
                advanced_indicators = ["advanced", "expert", "mastery", "professional", "master"]
                
                if any(word in course_name for word in beginner_indicators):
                    course["LEVEL_CATEGORY"] = "BEGINNER"
                    level_counts["BEGINNER"] += 1
                elif any(word in course_name for word in advanced_indicators):
                    course["LEVEL_CATEGORY"] = "ADVANCED"
                    level_counts["ADVANCED"] += 1
                else:
                    # If no clear indicators in name, distribute by need
                    # Assign to the level with the fewest courses
                    sorted_levels = sorted(level_counts.items(), key=lambda x: x[1])
                    target_level = sorted_levels[0][0]
                    course["LEVEL_CATEGORY"] = target_level
                    level_counts[target_level] += 1
                
            # In case we still have no courses at a particular level
            for level in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]:
                if level_counts[level] == 0 and courses:
                    # Find the level with the most courses
                    max_level = max(level_counts.items(), key=lambda x: x[1])[0]
                    if level_counts[max_level] > 1:
                        # Move one course from max level to empty level
                        for course in courses:
                            if course.get("LEVEL_CATEGORY") == max_level:
                                course["LEVEL_CATEGORY"] = level
                                level_counts[level] += 1
                                level_counts[max_level] -= 1
                                break
        
        return {
            "count": len(courses),
            "courses": courses
        }
        
    except Exception as e:
        logger.error(f"Error getting career transition courses: {str(e)}")
        
        # Fall back to more basic courses - simulate "general" courses for the role
        basic_courses = get_fallback_courses(target_role)
        return {
            "count": len(basic_courses),
            "courses": basic_courses
        }
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

def get_fallback_courses(role: str) -> List[Dict]:
    """
    Returns error message when LLM fails.
    No course generation, only error message.
    
    Args:
        role (str): Target role
        
    Returns:
        list: Error message for user to try again later
    """
    # Return error message for any request
    return [{
        "COURSE_NAME": "Cannot process your request at this moment",
        "DESCRIPTION": "We're having trouble processing your request. Please try again later.",
        "SKILLS": "Error Processing Request",
        "URL": "",
        "PLATFORM": "",
        "LEVEL": "Error",
        "LEVEL_CATEGORY": "ERROR"
    }]

def format_transition_plan(username: str, current_skills: List[str], target_role: str, 
                          missing_skills: List[str], courses: List[Dict]) -> Dict[str, str]:
    """
    Format a career transition plan with recommended courses in the same style as learning path.
    
    Args:
        username (str): The username
        current_skills (list): Current skills from resume
        target_role (str): The target role
        missing_skills (list): Missing skills to develop
        courses (list): List of recommended courses
        
    Returns:
        dict: Dictionary with different sections of the formatted plan
    """
    # Categorize current skills using LLM instead of hardcoded keywords
    transferable_skills = []
    strong_skills = []
    
    try:
        # Use the ChatService to determine relevant skills for the role
        from backend.services.chat_service import ChatService
        chat_service = ChatService()
        
        # First get all current skills as a simple array
        current_skills_str = ", ".join(current_skills)
        
        # Create a prompt to categorize skills
        prompt = (
            f"You are a career advisor helping someone transition to a {target_role} role. "
            f"Analyze this list of their current skills: {current_skills_str}\n\n"
            f"Identify which skills are directly relevant/transferable to a {target_role} role. "
            f"Return ONLY a JSON array of the transferable skill names, nothing else."
        )
        
        # Get response from LLM
        success, response = chat_service.get_llm_response(prompt)
        
        if success:
            # Try to extract transferable skills from JSON
            import json
            import re
            
            json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            if json_match:
                try:
                    skills_json = f"[{json_match.group(1)}]"
                    transferable_from_llm = json.loads(skills_json)
                    if transferable_from_llm and isinstance(transferable_from_llm, list):
                        # Create a lowercase lookup for matching
                        transferable_lower = [s.lower() for s in transferable_from_llm if isinstance(s, str)]
                        
                        # Match with original skill names to preserve case
                        for skill in current_skills:
                            if skill.lower() in transferable_lower or any(t.lower() in skill.lower() for t in transferable_from_llm):
                                transferable_skills.append(skill)
                            else:
                                strong_skills.append(skill)
                except Exception as e:
                    logger.error(f"Error parsing transferable skills: {e}")
        
        # If LLM categorization failed, fall back to a simpler approach without hardcoded keywords
        if not transferable_skills and not strong_skills:
            raise Exception("LLM categorization failed")
            
    except Exception as e:
        logger.error(f"Error categorizing skills with LLM: {e}")
        # Simple fallback without hardcoded role-specific keywords
        # Just distribute skills evenly between categories
        transferable_skills = current_skills[:len(current_skills)//2]
        strong_skills = current_skills[len(current_skills)//2:]
    
    # Limit to top skills
    transferable_skills = transferable_skills[:8]
    strong_skills = strong_skills[:8]
    
    # Create skill assessment message
    skill_assessment = f"""
# 🔍 Your Skills Assessment for {target_role}

## 🌟 Transferable Skills for {target_role}
These skills from your background are directly relevant to your target role:

"""
    if transferable_skills:
        for skill in transferable_skills:
            skill_assessment += f"- **{skill}** ✅\n"
    else:
        skill_assessment += "- You have a strong foundation to build upon, but may need to develop more role-specific skills\n"
    
    skill_assessment += """
## 💪 Other Strong Skills
These additional skills from your background can complement your transition:

"""
    
    if strong_skills:
        for skill in strong_skills:
            skill_assessment += f"- {skill}\n"
    else:
        skill_assessment += "- Your existing skills will provide a valuable foundation for your transition\n"
    
    skill_assessment += """
## 📈 Key Skills to Develop
Based on your current profile, these critical skills will help you succeed in your target role:

"""
    
    for skill in missing_skills:
        skill_assessment += f"- **{skill}** ⭐ (High Priority)\n"
    
    # Create introduction for course recommendations
    intro = f"""
# 🚀 Your {target_role} Career Transition Path

Based on your background and the skills you need to develop, I've curated this learning path to help you transition into a **{target_role}** role successfully. This plan focuses on:

- Building on your existing expertise in {', '.join(transferable_skills[:3] if transferable_skills else ['your current field'])}
- Developing critical skills in {', '.join(missing_skills[:3])}
- Creating a strategic approach to your career transition

The courses below are organized into a structured learning path you can complete in 3-6 months.

---

"""
    
    # Format course recommendations in learning path style
    course_msg = ""
    
    if not courses:
        course_msg = "I couldn't find specific courses for your skill gaps. Consider searching for courses related to the skills mentioned above on platforms like Coursera, Udemy, or LinkedIn Learning."
        has_valid_courses = False
    else:
        # Group courses by level
        beginner_courses = [c for c in courses if c.get("LEVEL_CATEGORY") == "BEGINNER"]
        intermediate_courses = [c for c in courses if c.get("LEVEL_CATEGORY") == "INTERMEDIATE"]
        advanced_courses = [c for c in courses if c.get("LEVEL_CATEGORY") == "ADVANCED"]
        
        # Ensure we have at least some courses at each level
        # If we're missing a level completely, redistribute from others
        if not beginner_courses and (intermediate_courses or advanced_courses):
            # Take courses from other levels to fill beginner level
            source_courses = intermediate_courses if intermediate_courses else advanced_courses
            # Move up to 2 courses to beginner level
            courses_to_move = min(len(source_courses), 2)
            for i in range(courses_to_move):
                # Find courses with simplest names or descriptions for beginners
                best_match_idx = -1
                for idx, course in enumerate(source_courses):
                    name = course.get("COURSE_NAME", "").lower()
                    if "intro" in name or "beginner" in name or "fundamental" in name or "basic" in name:
                        best_match_idx = idx
                        break
                
                # If no ideal match found, just take the first one
                if best_match_idx == -1 and source_courses:
                    best_match_idx = 0
                
                if best_match_idx != -1:
                    course = source_courses.pop(best_match_idx)
                    course["LEVEL_CATEGORY"] = "BEGINNER"
                    beginner_courses.append(course)
        
        if not intermediate_courses and (beginner_courses or advanced_courses):
            # Take courses from other levels to fill intermediate level
            source_courses = beginner_courses if len(beginner_courses) > 2 else advanced_courses
            if source_courses:
                # Move up to 2 courses to intermediate level
                courses_to_move = min(len(source_courses), 2)
                for i in range(courses_to_move):
                    course = source_courses.pop(0)
                    course["LEVEL_CATEGORY"] = "INTERMEDIATE"
                    intermediate_courses.append(course)
        
        if not advanced_courses and (beginner_courses or intermediate_courses):
            # Take courses from other levels to fill advanced level
            source_courses = intermediate_courses if len(intermediate_courses) > 2 else beginner_courses
            if source_courses:
                # Move up to 2 courses to advanced level
                courses_to_move = min(len(source_courses), 2)
                for i in range(courses_to_move):
                    course = source_courses.pop()
                    course["LEVEL_CATEGORY"] = "ADVANCED"
                    advanced_courses.append(course)
        
        has_valid_courses = True
        
        # Beginner courses (Month 1-2)
        if beginner_courses:
            course_msg += f"# 📚 Beginner Level (Month 1-2)\n\n"
            for course in beginner_courses[:2]:
                course_msg += f"### {course.get('COURSE_NAME')}\n\n"
                
                # Format platform and level
                platform_text = ""
                if course.get('PLATFORM'):
                    platform_text = f"**🏢 Platform**: {course.get('PLATFORM')}"
                if course.get('LEVEL'):
                    if platform_text:
                        platform_text += f" | **📊 Level**: {course.get('LEVEL')}"
                    else:
                        platform_text = f"**📊 Level**: {course.get('LEVEL')}"
                
                course_msg += f"> {platform_text}\n\n"
                
                # Add description
                if course.get('DESCRIPTION'):
                    desc = course.get('DESCRIPTION')
                    course_msg += f"**What you'll learn**: {desc}\n\n"
                
                # Format skills
                if course.get('SKILLS'):
                    skills = course.get('SKILLS').split(', ')
                    course_msg += f"**Key skills**:\n\n"
                    for skill in skills:
                        course_msg += f"- {skill}\n"
                    course_msg += "\n"
                
                # Add URL
                if course.get('URL'):
                    course_msg += f"**[➡️ Enroll in this course]({course.get('URL')})**\n\n"
                
                course_msg += "---\n\n"
        
        # Intermediate courses (Month 3-4)
        if intermediate_courses:
            course_msg += f"# 🔄 Intermediate Level (Month 3-4)\n\n"
            for course in intermediate_courses[:2]:
                course_msg += f"### {course.get('COURSE_NAME')}\n\n"
                
                # Format platform and level
                platform_text = ""
                if course.get('PLATFORM'):
                    platform_text = f"**🏢 Platform**: {course.get('PLATFORM')}"
                if course.get('LEVEL'):
                    if platform_text:
                        platform_text += f" | **📊 Level**: {course.get('LEVEL')}"
                    else:
                        platform_text = f"**📊 Level**: {course.get('LEVEL')}"
                
                course_msg += f"> {platform_text}\n\n"
                
                # Add description
                if course.get('DESCRIPTION'):
                    desc = course.get('DESCRIPTION')
                    course_msg += f"**What you'll learn**: {desc}\n\n"
                
                # Format skills
                if course.get('SKILLS'):
                    skills = course.get('SKILLS').split(', ')
                    course_msg += f"**Key skills**:\n\n"
                    for skill in skills:
                        course_msg += f"- {skill}\n"
                    course_msg += "\n"
                
                # Add URL
                if course.get('URL'):
                    course_msg += f"**[➡️ Enroll in this course]({course.get('URL')})**\n\n"
                
                course_msg += "---\n\n"
        
        # Advanced courses (Month 5-6)
        if advanced_courses:
            course_msg += f"# 🔥 Advanced Level (Month 5-6)\n\n"
            for course in advanced_courses[:2]:
                course_msg += f"### {course.get('COURSE_NAME')}\n\n"
                
                # Format platform and level
                platform_text = ""
                if course.get('PLATFORM'):
                    platform_text = f"**🏢 Platform**: {course.get('PLATFORM')}"
                if course.get('LEVEL'):
                    if platform_text:
                        platform_text += f" | **📊 Level**: {course.get('LEVEL')}"
                    else:
                        platform_text = f"**📊 Level**: {course.get('LEVEL')}"
                
                course_msg += f"> {platform_text}\n\n"
                
                # Add description
                if course.get('DESCRIPTION'):
                    desc = course.get('DESCRIPTION')
                    course_msg += f"**What you'll learn**: {desc}\n\n"
                
                # Format skills
                if course.get('SKILLS'):
                    skills = course.get('SKILLS').split(', ')
                    course_msg += f"**Key skills**:\n\n"
                    for skill in skills:
                        course_msg += f"- {skill}\n"
                    course_msg += "\n"
                
                # Add URL
                if course.get('URL'):
                    course_msg += f"**[➡️ Enroll in this course]({course.get('URL')})**\n\n"
                
                course_msg += "---\n\n"
    
    # Generate career advice using LLM
    try:
        # Use the ChatService for dynamic, personalized career advice
        chat_service = ChatService()
        
        # Create a prompt to generate career advice
        career_advice_prompt = (
            f"You are a career advisor helping someone transition to a {target_role} role. "
            f"The candidate has the following skills already: {', '.join(current_skills[:10])}. "
            f"They need to develop these skills: {', '.join(missing_skills[:5])}. "
            f"Their most transferable skills for this role are: {', '.join(transferable_skills[:5] if transferable_skills else ['None identified'])}. "
            f"Provide a 5-step career transition strategy tailored to their situation in MARKDOWN format. "
            f"Include specific advice about: building skills, creating portfolio projects, adapting their resume, networking, "
            f"and practical next steps. Format as a professional career advice section with bullet points."
        )
        
        # Get advice from LLM
        success, llm_career_advice = chat_service.get_llm_response(career_advice_prompt)
        
        # Use the LLM-generated advice if successful
        if success and len(llm_career_advice) > 100:  # Ensure we got a substantial response
            # Add a title if not present
            if not llm_career_advice.strip().startswith("#"):
                career_advice = f"# 💼 Career Transition Strategy for {target_role}\n\n{llm_career_advice}"
            else:
                career_advice = llm_career_advice
        else:
            # If LLM fails, use a simple error message
            career_advice = f"""
# 💼 Career Transition Strategy 

Sorry, we're having trouble generating personalized career advice at this moment. Please try again later.
"""
    except Exception as e:
        logger.error(f"Error generating career advice with LLM: {e}")
        # Fallback to a simple error message
        career_advice = f"""
# 💼 Career Transition Strategy 

Sorry, we're having trouble generating personalized career advice at this moment. Please try again later.
"""
    
    return {
        "skill_assessment": skill_assessment,
        "introduction": intro,
        "course_recommendations": course_msg,
        "career_advice": career_advice,
        "has_valid_courses": has_valid_courses
    }

# NOTE: This functionality has been refactored to remove hardcoded career advice.
# Now the career advice is dynamically generated based on:
# 1. The target role (with role-specific guidance)
# 2. User's current skills (categorized by relevance)
# 3. Identified skill gaps (with prioritization)
# Additional improvements could include:
# 1. Moving formatting functions to ui_service.py for better separation of concerns
# 2. Creating a configuration system for customization of advice templates

