# File: frontend/ui_service.py
import logging
import pandas as pd

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
    if courses_df.empty:
        return f"I couldn't find specific courses for {target_role} at this time. Please check with your administrator about updating the course database.", False
    
    course_msg = f"# Data Engineer Learning Path\n\n"
    levels = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
    has_valid_courses = False
    
    for level in levels:
        level_courses = courses_df[courses_df["LEVEL_CATEGORY"] == level]
        
        if not level_courses.empty:
            level_title_added = False
            
            for _, course in level_courses.iterrows():
                # Check if this course has valid data (not None)
                if (course['COURSE_NAME'] and 
                    str(course['COURSE_NAME']).lower() != 'none' and
                    course['URL'] and 
                    str(course['URL']).lower() != 'none'):
                    
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
                    
                    course_msg += f"### {course['COURSE_NAME']}\n\n"
                    
                    # Format platform and level more prominently using markdown
                    platform_text = ""
                    # Add platform if available
                    if 'PLATFORM' in course and course['PLATFORM'] and str(course['PLATFORM']).lower() != 'none':
                        platform_text = f"**🏢 Platform**: {course['PLATFORM']}"
                    
                    # Add level information
                    if course['LEVEL'] and str(course['LEVEL']).lower() != 'none':
                        if platform_text:
                            platform_text += f" | **📊 Level**: {course['LEVEL']}"
                        else:
                            platform_text = f"**📊 Level**: {course['LEVEL']}"
                    
                    # Add the platform/level info using markdown formatting
                    course_msg += f"> {platform_text}\n\n"
                    
                    # Add description with better formatting using bullet points for long descriptions
                    if course['DESCRIPTION'] and str(course['DESCRIPTION']).lower() != 'none':
                        desc = course['DESCRIPTION']
                        # Format longer descriptions into a more readable format
                        if len(desc) > 300:
                            # Split into paragraphs for better reading
                            paragraphs = []
                            current_para = ""
                            words = desc.split()
                            for word in words:
                                if len(current_para) + len(word) < 80:  # Line length
                                    current_para += " " + word if current_para else word
                                else:
                                    paragraphs.append(current_para)
                                    current_para = word
                            if current_para:
                                paragraphs.append(current_para)
                                
                            # Create a nicely formatted description
                            course_msg += f"**What you'll learn**:\n\n"
                            for para in paragraphs:
                                course_msg += f"- {para}\n"
                            course_msg += "\n"
                        else:
                            course_msg += f"**What you'll learn**: {desc}\n\n"
                    
                    # Format skills as a bullet list for better readability
                    if course['SKILLS'] and str(course['SKILLS']).lower() != 'none':
                        skills = course['SKILLS'].split(', ')
                        course_msg += f"**Key skills**:\n\n"
                        # Organize into 2-3 skills per line for a cleaner look
                        skill_groups = []
                        current_group = []
                        for skill in skills:
                            if len(', '.join(current_group + [skill])) < 80:  # Keep lines reasonable length
                                current_group.append(skill)
                            else:
                                skill_groups.append(current_group)
                                current_group = [skill]
                        if current_group:
                            skill_groups.append(current_group)
                        
                        # Add skill groups as bullet points
                        for group in skill_groups:
                            course_msg += f"- {', '.join(group)}\n"
                        course_msg += "\n"
                    
                    # Add URL with better styling using markdown
                    if course['URL'] and str(course['URL']).lower() != 'none':
                        course_msg += f"**[➡️ Enroll in this course]({course['URL']})**\n\n"
                    
                    # Add separator between courses
                    course_msg += "---\n\n"
                    has_valid_courses = True
    
    return course_msg, has_valid_courses

def format_introduction(target_role, skill_ratings):
    """
    Format the introduction for the learning path.
    
    Args:
        target_role (str): The target role for the learning path
        skill_ratings (dict): Dictionary of skill ratings
        
    Returns:
        str: A markdown-formatted introduction
    """
    intro_text = f"""
# 🚀 Your Personalized Data Engineering Learning Path

Based on your current skill assessment, I've curated courses that will help you advance your career as a **{target_role}**. These recommendations focus on strengthening your skills in:

"""
    # Add skills that need improvement with emoji indicators
    for skill, rating in skill_ratings.items():
        if rating <= 2:
            intro_text += f"- **{skill}** ⭐ (Prioritize)\n"
        elif rating <= 3:
            intro_text += f"- **{skill}** ⭐⭐ (Focus area)\n"
    
    intro_text += """
The learning path is organized from beginner to advanced courses, designed for completion within 6 months. Each course is chosen to address specific skill gaps and help you build a comprehensive foundation in data engineering.

---

"""
    return intro_text

def format_career_advice():
    """
    Format career advice for after completing the learning path.
    
    Returns:
        str: A markdown-formatted career advice message
    """
    return """
# 💼 Next Steps After Completing Your Learning Path

Once you've completed the courses in your learning path, consider these steps to advance your career:

1. **Build a portfolio** - Create 2-3 data engineering projects demonstrating your skills with cloud platforms, data pipelines, and big data technologies
2. **Get certified** - Pursue relevant certifications like Google Cloud Professional Data Engineer or AWS Data Analytics Specialty
3. **Join communities** - Connect with other data professionals on forums like Stack Overflow, Reddit's r/dataengineering, or Meetup groups
4. **Contribute to open source** - Participate in data engineering open source projects to gain recognition

Do you have any questions about your learning path or career next steps?
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