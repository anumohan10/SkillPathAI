# File: frontend/ui_service.py
import logging
import pandas as pd
from typing import List, Dict, Any

# Set up logger
logger = logging.getLogger(__name__)

def format_course_message(courses_df, target_role):
    """
    Format course recommendations as a markdown message for the UI.
    
    Args:
        courses_df (DataFrame): DataFrame containing course recommendations
        target_role (str): The target role for the learning path
        
    Returns:
        str: A markdown-formatted message for display in the UI
        bool: Whether valid courses were found
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Add detailed debugging for all courses
    logger.info("=== COURSE DATA DEBUG START ===")
    logger.info(f"Target role: {target_role}")
    
    try:
        # Convert DataFrame to records for easier debugging
        if isinstance(courses_df, pd.DataFrame):
            courses_records = courses_df.to_dict('records')
            logger.info(f"DataFrame has {len(courses_records)} records")
            
            # Check level categories - focus on what we're looking for
            advanced_courses = [c for c in courses_records if c.get('LEVEL_CATEGORY') == 'ADVANCED']
            logger.info(f"Found {len(advanced_courses)} ADVANCED courses in data")
            if advanced_courses:
                for i, course in enumerate(advanced_courses):
                    logger.info(f"ADVANCED course {i+1}: {course.get('COURSE_NAME', 'No name')}")
        else:
            logger.warning(f"courses_df is not a DataFrame: {type(courses_df)}")
    except Exception as e:
        logger.error(f"Error during debug logging: {e}")
    
    logger.info("=== COURSE DATA DEBUG END ===")
    
    # Debug logging to see what we're working with
    logger.info(f"Formatting courses: DataFrame has {len(courses_df)} rows")
    logger.info(f"DataFrame columns: {list(courses_df.columns)}")
    
    if courses_df.empty:
        return f"I couldn't find specific courses for {target_role} at this time. Please check with your administrator about updating the course database.", False
    
    course_msg = f"# 📋 Learning Path\n\n"
    levels = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
    has_valid_courses = False
    
    # Normalize column names to handle case sensitivity issues
    # Create a mapping of lowercase column names to actual column names
    column_map = {col.lower(): col for col in courses_df.columns}
    
    # Handle common column name variations
    level_category_col = column_map.get('level_category', column_map.get('levelcategory', 'LEVEL_CATEGORY'))
    course_name_col = column_map.get('course_name', column_map.get('coursename', 'COURSE_NAME'))
    url_col = column_map.get('url', 'URL')
    platform_col = column_map.get('platform', 'PLATFORM')
    level_col = column_map.get('level', 'LEVEL')
    description_col = column_map.get('description', 'DESCRIPTION')
    skills_col = column_map.get('skills', 'SKILLS')
    
    # Log what column names we're using
    logger.info(f"Using columns: level_category={level_category_col}, course_name={course_name_col}, url={url_col}")
    
    # Check if critical columns are present
    if level_category_col not in courses_df.columns:
        logger.warning(f"LEVEL_CATEGORY column not found in DataFrame! Available columns: {list(courses_df.columns)}")
        # If level_category is missing, assign all courses to BEGINNER level
        courses_df['LEVEL_CATEGORY'] = 'BEGINNER'
        level_category_col = 'LEVEL_CATEGORY'
    
    if course_name_col not in courses_df.columns or url_col not in courses_df.columns:
        logger.warning(f"Critical columns missing! course_name or URL not found")
        return f"I retrieved courses but couldn't properly format them due to missing data. Please try again later.", False
    
    # Process each level
    for level in levels:
        try:
            level_courses = courses_df[courses_df[level_category_col] == level]
            
            if not level_courses.empty:
                logger.info(f"Found {len(level_courses)} courses for level {level}")
                # Log the actual course details for debugging
                for i, (_, course) in enumerate(level_courses.iterrows()):
                    logger.info(f"Level {level} - Course {i+1}: {course.get(course_name_col, 'No Name')} [{course.get(level_category_col, 'No Category')}]")
                level_title_added = False
                
                for _, course in level_courses.iterrows():
                    # Check if this course has valid data (not None)
                    course_name = str(course.get(course_name_col, ""))
                    course_url = str(course.get(url_col, ""))
                    
                    if (course_name and course_name.lower() != 'none' and 
                        course_url and course_url.lower() != 'none'):
                        
                        if not level_title_added:
                            if level == "BEGINNER":
                                course_msg += f"# 📚 {level.title()} Level (Month 1-2)\n\n"
                            elif level == "INTERMEDIATE":
                                course_msg += f"# 🔄 {level.title()} Level (Month 3-4)\n\n"
                            elif level == "ADVANCED":
                                course_msg += f"# 🔥 {level.title()} Level (Month 5-6)\n\n"
                            else:
                                course_msg += f"# {level.title()} Level\n\n"
                            level_title_added = True
                        
                        course_msg += f"### {course_name}\n\n"
                        
                        # Format platform and level more prominently using markdown
                        platform_text = ""
                        # Add platform if available
                        platform = course.get(platform_col, "")
                        if platform and str(platform).lower() != 'none':
                            platform_text = f"**🏢 Platform**: {platform}"
                        
                        # Add level information
                        course_level = course.get(level_col, "")
                        if course_level and str(course_level).lower() != 'none':
                            if platform_text:
                                platform_text += f" | **📊 Level**: {course_level}"
                            else:
                                platform_text = f"**📊 Level**: {course_level}"
                        
                        # Add the platform/level info using markdown formatting
                        if platform_text:
                            course_msg += f"> {platform_text}\n\n"
                        
                        # Add description with better formatting
                        description = course.get(description_col, "")
                        if description and str(description).lower() != 'none':
                            course_msg += f"**What you'll learn**:\n\n{description}\n\n"
                        
                        # Format skills as a bullet list for better readability
                        skills = course.get(skills_col, "")
                        if skills and str(skills).lower() != 'none':
                            try:
                                skill_list = skills.split(', ')
                                course_msg += f"**Key skills**:\n\n"
                                for skill in skill_list[:10]:  # Limit to 10 skills to avoid overwhelming
                                    course_msg += f"- {skill}\n"
                                course_msg += "\n"
                            except Exception as e:
                                logger.error(f"Error formatting skills: {e}")
                        
                        # Add URL with better styling using markdown
                        course_msg += f"**[➡️ Enroll in this course]({course_url})**\n\n"
                        
                        # Add separator between courses
                        course_msg += "---\n\n"
                        has_valid_courses = True
        except Exception as e:
            logger.error(f"Error processing level {level}: {e}")
            continue
    
    if not has_valid_courses:
        # If we had courses but couldn't format them properly
        if not courses_df.empty:
            logger.warning("No valid courses could be formatted despite having data")
            # Try a simplified approach as fallback
            try:
                course_msg += "# 📚 Course Recommendations\n\n"
                for _, course in courses_df.iterrows():
                    # Just try to show the bare minimum
                    course_name = str(course.get(course_name_col, "Unknown Course"))
                    course_url = course.get(url_col, "")
                    
                    course_msg += f"### {course_name}\n\n"
                    if course_url:
                        course_msg += f"**[➡️ Enroll in this course]({course_url})**\n\n"
                    course_msg += "---\n\n"
                
                has_valid_courses = True
            except Exception as e:
                logger.error(f"Error in fallback course formatting: {e}")
                course_msg = f"I'm having trouble formatting courses for {target_role}. Please try again later."
                has_valid_courses = False
    
    logger.info(f"Finished formatting courses. Has valid courses: {has_valid_courses}")
    return course_msg, has_valid_courses

def format_introduction(target_role, skill_ratings=None, missing_skills=None):
    """
    Format the introduction for the learning path or career transition.
    Supports both skill ratings or missing skills.
    
    Args:
        target_role (str): The target role for the learning path
        skill_ratings (dict, optional): Dictionary of skill ratings (for learning path)
        missing_skills (list, optional): List of missing skills (for career transition)
        
    Returns:
        str: A markdown-formatted introduction
    """
    if skill_ratings:
        # Standard learning path introduction based on skill assessments
        intro_text = f"""
# 🚀 Your Personalized Learning Path

Based on your current skill assessment, I've curated courses that will help you advance your career as a **{target_role}**. These recommendations focus on strengthening your skills in:

"""
        # Add skills that need improvement with star ratings matching the actual rating
        for skill, rating in skill_ratings.items():
            if rating <= 3:  # Focus on skills that need improvement
                # Add filled stars equal to the rating and empty stars to complete 5 stars
                filled_stars = "★" * rating
                empty_stars = "☆" * (5 - rating)
                priority_text = "(Prioritize)" if rating <= 2 else "(Focus area)"
                intro_text += f"- **{skill}** {filled_stars}{empty_stars} {priority_text}\n"
        
        intro_text += """
The learning path is organized from beginner to advanced courses, designed for completion within 6 months. Each course is chosen to address specific skill gaps and help you build a comprehensive foundation in this field.

---

"""
    
    elif missing_skills:
        # Career transition introduction based on missing skills
        intro_text = f"""
# 🚀 Your {target_role} Career Transition Path

Based on the skills identified in your resume and the requirements for a **{target_role}** role, I've curated courses to help you bridge your skill gaps. These recommendations focus on developing these critical skills:

"""
        # Add missing skills with priority indicators
        for i, skill in enumerate(missing_skills):
            priority = "⭐⭐⭐" if i < 3 else "⭐⭐" if i < 5 else "⭐"
            intro_text += f"- **{skill}** {priority}\n"
            
        intro_text += """
The learning path is organized from beginner to advanced courses, designed for completion within 3-6 months. Each course is chosen to help you build the specific skills needed for your career transition.

---

"""
    
    else:
        # Generic introduction if neither skill_ratings nor missing_skills provided
        intro_text = f"""
# 🚀 Your {target_role} Learning Path

I've curated a selection of courses to help you develop the key skills needed for a successful career as a **{target_role}**. These recommendations cover the essential competencies for this role.

The learning path is organized from beginner to advanced courses, designed for completion within 3-6 months.

---

"""
    
    return intro_text


def format_career_advice(target_role=None, skill_ratings=None):
    """
    Generate career advice using LLM for a learning path.
    
    Args:
        target_role (str, optional): The target role for the learning path
        skill_ratings (dict, optional): Dictionary of skill ratings
        
    Returns:
        str: A markdown-formatted career advice message
    """
    try:
        from backend.services.chat_service import ChatService
        chat_service = ChatService()
        
        # Create a prompt to generate career advice
        role_info = f"for a {target_role} role" if target_role else "for your chosen career path"
        
        # Include skill information if available
        skill_info = ""
        if skill_ratings:
            # Get top skills and their ratings
            skill_items = list(skill_ratings.items())
            top_skills = [f"{skill} (rating: {rating}/5)" for skill, rating in skill_items[:5]]
            skill_info = f"Your current top skills are: {', '.join(top_skills)}. "
        
        # Build the prompt
        career_advice_prompt = (
            f"You are a career advisor helping someone develop their skills {role_info}. "
            f"{skill_info}"
            f"Provide 4-5 concrete next steps they should take after completing their learning path. "
            f"Include advice about building a portfolio, certifications, joining communities, and gaining practical experience. "
            f"Format your response in Markdown with a title and bullet points. Keep it concise but specific."
        )
        
        # Get advice from LLM
        success, llm_career_advice = chat_service.get_llm_response(career_advice_prompt)
        
        # Use the LLM-generated advice if successful
        if success and len(llm_career_advice) > 100:  # Ensure we got a substantial response
            # Add a title if not present
            if not llm_career_advice.strip().startswith("#"):
                career_advice = f"# 💼 Next Steps After Completing Your Learning Path\n\n{llm_career_advice}"
            else:
                career_advice = llm_career_advice
            return career_advice
            
        # Fallback for when LLM fails
        return """
# 💼 Next Steps After Completing Your Learning Path

Sorry, we're having trouble generating personalized career advice at this moment. Please try again later.
"""
        
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating career advice with LLM: {e}")
        
        # Return error message
        return """
# 💼 Next Steps After Completing Your Learning Path

Sorry, we're having trouble generating personalized career advice at this moment. Please try again later.
"""

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
    # Use simple division to categorize skills without hardcoded keywords
    # Just split skills evenly between transferable and other strong skills
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
                    # Format longer descriptions into a more readable format
                    if len(desc) > 300:
                        # Simple approach: Use complete description and break it into reasonable chunks
                        words = desc.split()
                        sentences = []
                        current_sentence = []
                        current_length = 0
                        
                        for word in words:
                            # If adding this word doesn't make the line too long
                            if current_length + len(word) + 1 <= 80:  # +1 for the space
                                current_sentence.append(word)
                                current_length += len(word) + 1
                            else:
                                # This line is full, start a new one
                                if current_sentence:
                                    sentences.append(" ".join(current_sentence))
                                current_sentence = [word]
                                current_length = len(word)
                                
                        # Add the last sentence if there is one
                        if current_sentence:
                            sentences.append(" ".join(current_sentence))
                            
                        # Create a paragraph-style description instead of bullet points
                        course_msg += f"**What you'll learn**:\n\n"
                        course_msg += f"{desc}\n\n"
                    else:
                        course_msg += f"**What you'll learn**:\n\n{desc}\n\n"
                
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
                    # Format longer descriptions into a more readable format
                    if len(desc) > 300:
                        # Simple approach: Use complete description and break it into reasonable chunks
                        words = desc.split()
                        sentences = []
                        current_sentence = []
                        current_length = 0
                        
                        for word in words:
                            # If adding this word doesn't make the line too long
                            if current_length + len(word) + 1 <= 80:  # +1 for the space
                                current_sentence.append(word)
                                current_length += len(word) + 1
                            else:
                                # This line is full, start a new one
                                if current_sentence:
                                    sentences.append(" ".join(current_sentence))
                                current_sentence = [word]
                                current_length = len(word)
                                
                        # Add the last sentence if there is one
                        if current_sentence:
                            sentences.append(" ".join(current_sentence))
                            
                        # Create a paragraph-style description instead of bullet points
                        course_msg += f"**What you'll learn**:\n\n"
                        course_msg += f"{desc}\n\n"
                    else:
                        course_msg += f"**What you'll learn**:\n\n{desc}\n\n"
                
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
                    # Format longer descriptions into a more readable format
                    if len(desc) > 300:
                        # Simple approach: Use complete description and break it into reasonable chunks
                        words = desc.split()
                        sentences = []
                        current_sentence = []
                        current_length = 0
                        
                        for word in words:
                            # If adding this word doesn't make the line too long
                            if current_length + len(word) + 1 <= 80:  # +1 for the space
                                current_sentence.append(word)
                                current_length += len(word) + 1
                            else:
                                # This line is full, start a new one
                                if current_sentence:
                                    sentences.append(" ".join(current_sentence))
                                current_sentence = [word]
                                current_length = len(word)
                                
                        # Add the last sentence if there is one
                        if current_sentence:
                            sentences.append(" ".join(current_sentence))
                            
                        # Create a paragraph-style description instead of bullet points
                        course_msg += f"**What you'll learn**:\n\n"
                        course_msg += f"{desc}\n\n"
                    else:
                        course_msg += f"**What you'll learn**:\n\n{desc}\n\n"
                
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