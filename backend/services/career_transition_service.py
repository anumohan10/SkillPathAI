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
        
        # Create a more targeted prompt with specific guidance
        prompt = (
            f"You are a career counselor in 2025 specializing in {target_role} career transitions. "
            f"The candidate has the following skills from their resume: {', '.join(extracted_skills[:20])}. "
            f"Given their current skills and the requirements of a {target_role} role in 2025:\n\n"
            f"1. What are the 5-7 MOST CRUCIAL technical skills they're missing?\n"
            f"2. Focus on specific technologies, tools, and methodologies rather than general abilities\n"
            f"3. Prioritize skills that would have the highest impact in landing a {target_role} job\n\n"
            f"Return ONLY a JSON array of specific skill names, with NO explanations or additional text."
        )
        
        # Use a more comprehensive approach to get better results
        flag, response = chat_service.get_llm_response(prompt)
        
        # Check if response contains an error message
        if "having trouble" in response or "sorry" in response.lower() or "I can't" in response:
            # Make a second attempt with a simpler, more direct prompt
            simple_prompt = (
                f"List the top 5 most important technical skills needed for a {target_role} position in 2025 "
                f"that are not in this list: {', '.join(extracted_skills[:15])}. "
                f"Return only a JSON array."
            )
            
            response = chat_service.get_llm_response(simple_prompt)
            
            # If still getting errors, use role-specific defaults
            if "having trouble" in response or "sorry" in response.lower() or "I can't" in response:
                return get_default_skills_for_role(target_role)
        
        # Extract JSON list from response
        import re
        json_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
        
        if json_match:
            try:
                skills_json = f"[{json_match.group(1)}]"
                skills = json.loads(skills_json)
                if skills and isinstance(skills, list) and len(skills) > 0:
                    return skills
                else:
                    # Invalid or empty skills list
                    return get_default_skills_for_role(target_role)
            except json.JSONDecodeError:
                # JSON parsing failed
                return get_default_skills_for_role(target_role)
        else:
            # Try line-by-line parsing as fallback
            skills = []
            for line in response.split('\n'):
                line = line.strip(' "\',-.')
                if line and len(line) > 3 and not line.startswith('[') and not line.endswith(']'):
                    skills.append(line)
            
            if skills:
                return skills[:5]  # Limit to 5 skills
            else:
                return get_default_skills_for_role(target_role)
            
    except Exception as e:
        logger.error(f"Error identifying missing skills: {str(e)}")
        return get_default_skills_for_role(target_role)

def get_default_skills_for_role(role: str) -> List[str]:
    """
    Get default skills for a role when LLM processing fails.
    
    Args:
        role (str): The target role
        
    Returns:
        list: Default skills based on role
    """
    role_lower = role.lower()
    
    if any(word in role_lower for word in ["system", "systems"]):
        return ["Systems Architecture", "Technical Documentation", "Performance Optimization", 
                "Project Management", "Integration Testing"]
                
    elif any(word in role_lower for word in ["data", "scientist", "analyst"]):
        return ["Statistical Modeling", "Data Visualization", "SQL", 
                "Machine Learning", "Data Engineering"]
                
    elif any(word in role_lower for word in ["software", "developer"]):
        return ["System Design", "API Development", "Testing Practices", 
                "DevOps Skills", "Code Optimization"]
                
    elif "engineer" in role_lower:
        return ["System Architecture", "Technical Documentation", "Performance Optimization", 
                "Security Practices", "Project Management"]
                
    else:
        return ["Technical Skills", "Project Management", "Industry Knowledge", 
                "Communication", "Problem Solving"]

def store_career_analysis(username: str, resume_text: str, extracted_skills: List[str], 
                          target_role: str, missing_skills: List[str] = None) -> str:
    """
    Store career transition analysis in the database with optimized approach.
    
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
        if not missing_skills:
            missing_skills = process_missing_skills(extracted_skills, target_role)
        
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
        logger.info(f"Successfully stored career analysis for {username}")
        return record_id
        
    except Exception as e:
        logger.error(f"Error storing career analysis: {str(e)}")
        return None
    finally:
        cursor.close()
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
    Get fallback courses when database query fails.
    
    Args:
        role (str): Target role
        
    Returns:
        list: List of course dictionaries
    """
    role_lower = role.lower()
    
    # Default common platforms
    platforms = ["Coursera", "Udemy", "edX"]
    
    # Basic course structure
    courses = []
    
    # Create fallback courses based on role
    if "data" in role_lower or "scientist" in role_lower or "analyst" in role_lower:
        courses = [
            {
                "COURSE_NAME": "Data Science Fundamentals",
                "DESCRIPTION": "Learn the key concepts and tools for data science and machine learning",
                "SKILLS": "Python, Statistics, Data Visualization, Machine Learning",
                "URL": "https://www.coursera.org/specializations/data-science-fundamentals",
                "LEVEL": "Beginner",
                "PLATFORM": "Coursera",
                "LEVEL_CATEGORY": "BEGINNER"
            },
            {
                "COURSE_NAME": "Advanced Machine Learning",
                "DESCRIPTION": "Master advanced machine learning techniques and algorithms",
                "SKILLS": "Deep Learning, Statistical Models, Feature Engineering",
                "URL": "https://www.coursera.org/specializations/advanced-machine-learning",
                "LEVEL": "Advanced",
                "PLATFORM": "Coursera",
                "LEVEL_CATEGORY": "ADVANCED"
            }
        ]
    elif "system" in role_lower or "systems" in role_lower:
        courses = [
            {
                "COURSE_NAME": "Systems Design and Architecture",
                "DESCRIPTION": "Learn essential concepts in designing and implementing complex systems",
                "SKILLS": "Architecture Patterns, System Integration, Documentation",
                "URL": "https://www.udemy.com/course/system-design-architecture",
                "LEVEL": "Intermediate",
                "PLATFORM": "Udemy",
                "LEVEL_CATEGORY": "INTERMEDIATE"
            },
            {
                "COURSE_NAME": "Systems Engineering Fundamentals",
                "DESCRIPTION": "Master the principles of systems engineering and project management",
                "SKILLS": "Requirements Analysis, System Testing, Project Management",
                "URL": "https://www.edx.org/learn/systems-engineering",
                "LEVEL": "Beginner",
                "PLATFORM": "edX",
                "LEVEL_CATEGORY": "BEGINNER"
            }
        ]
    elif "software" in role_lower or "developer" in role_lower or "engineer" in role_lower:
        courses = [
            {
                "COURSE_NAME": "Software Engineering Principles",
                "DESCRIPTION": "Master essential software engineering concepts and practices",
                "SKILLS": "Software Design, Testing, CI/CD, Version Control",
                "URL": "https://www.udemy.com/course/software-engineering-principles",
                "LEVEL": "Beginner to Intermediate",
                "PLATFORM": "Udemy",
                "LEVEL_CATEGORY": "BEGINNER"
            },
            {
                "COURSE_NAME": "Advanced Software Architecture",
                "DESCRIPTION": "Learn advanced principles of software architecture and design patterns",
                "SKILLS": "Design Patterns, System Architecture, Scalability",
                "URL": "https://www.coursera.org/learn/software-architecture",
                "LEVEL": "Advanced",
                "PLATFORM": "Coursera",
                "LEVEL_CATEGORY": "ADVANCED"
            }
        ]
    else:
        # Generic courses for any role
        courses = [
            {
                "COURSE_NAME": f"Essential Skills for {role}",
                "DESCRIPTION": f"Develop the core competencies needed for a successful career as a {role}",
                "SKILLS": "Technical Skills, Communication, Problem Solving",
                "URL": "https://www.coursera.org/professional-certificates",
                "LEVEL": "Beginner",
                "PLATFORM": "Coursera",
                "LEVEL_CATEGORY": "BEGINNER"
            },
            {
                "COURSE_NAME": f"Advanced {role} Masterclass",
                "DESCRIPTION": f"Take your {role} skills to the next level with industry best practices",
                "SKILLS": "Advanced Techniques, Industry Knowledge, Specialization",
                "URL": "https://www.udemy.com/courses/professional-development",
                "LEVEL": "Advanced",
                "PLATFORM": "Udemy",
                "LEVEL_CATEGORY": "ADVANCED"
            }
        ]
    
    return courses

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
    # Categorize current skills by relevance to target role
    transferable_skills = []
    strong_skills = []
    
    # Identify some key terms for the target role to categorize skills
    role_keywords = []
    if "data" in target_role.lower():
        role_keywords = ["data", "sql", "analysis", "analytics", "visualization", "python", "statistics"]
    elif "system" in target_role.lower() or "systems" in target_role.lower():
        role_keywords = ["system", "architecture", "engineering", "integration", "design", "documentation"]
    elif "software" in target_role.lower() or "developer" in target_role.lower():
        role_keywords = ["software", "development", "code", "programming", "api", "testing"]
    elif "engineer" in target_role.lower():
        role_keywords = ["engineering", "technical", "design", "architecture", "development", "system"]
    
    # Categorize skills
    for skill in current_skills:
        if any(keyword in skill.lower() for keyword in role_keywords):
            transferable_skills.append(skill)
        else:
            strong_skills.append(skill)
    
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
    
    # Format career advice similar to learning path
    career_advice = f"""
# 💼 Career Transition Strategy for {target_role}

Follow this step-by-step roadmap to maximize your chances of a successful career transition:

1. **Build transferable skills** - Focus first on {', '.join(missing_skills[:3])} through the recommended courses above
2. **Create a transition portfolio** - Develop 2-3 projects that showcase your new {target_role} skills while leveraging your existing expertise in {', '.join(transferable_skills[:2] if transferable_skills else ['your field'])}
3. **Bridge your experience** - Reframe your resume to highlight how your background in {strong_skills[0] if strong_skills else 'your current role'} is relevant to {target_role} positions
4. **Network strategically** - Connect with current {target_role}s on LinkedIn and professional communities to understand the industry's needs
5. **Target transitional roles** - Look for hybrid positions that value both your existing expertise and your new skills

With dedicated effort on this plan, most career changers can successfully transition within 3-6 months.

Do you have any questions about your career transition plan?
"""
    
    return {
        "skill_assessment": skill_assessment,
        "introduction": intro,
        "course_recommendations": course_msg,
        "career_advice": career_advice,
        "has_valid_courses": has_valid_courses
    }

# TODO: Refactor this function to remove hardcoded career advice.
# This should be moved to a configuration file or database to make it:
# 1. Role-specific (currently only shows data engineering advice)
# 2. Easier to update without code changes
# 3. Potentially personalized based on user's skill assessment
# 4. Maybe format_transition_plan() needs to be moved to ui_service.py since it's not a service function.

