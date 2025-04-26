# File: frontend/ui_formatter.py
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
    if courses_df.empty:
        return f"I couldn't find specific courses for {target_role} at this time. Please check with your administrator about updating the course database.", False
    
    course_msg = f"# {target_role} Learning Path\n\n"
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
                    
                    # Add description with better formatting using paragraphs
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
                                course_msg += f"{para}\n\n"
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
# 🚀 Your Personalized Learning Path

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

1. **Build a portfolio** - Create 2-3  projects demonstrating your skills 
2. **Get certified** - Pursue relevant certifications
3. **Join communities** - Connect with other professionalson forums 
4. **Contribute to open source** - Participate in  events to gain recognition

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