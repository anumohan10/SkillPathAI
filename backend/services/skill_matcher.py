import re
from typing import List, Dict, Any

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills from resume text using regex pattern matching.
    This is a basic implementation - in production, you'd want to use NLP.
    """
    # Common skills dictionary with categories
    skills_dict = {
        "Programming Languages": [
            "Python", "Java", "JavaScript", "C\\+\\+", "C#", "Ruby", "PHP", "Swift", "Kotlin", 
            "TypeScript", "Go", "Rust", "Scala", "Perl", "R", "MATLAB"
        ],
        "Web Development": [
            "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask",
            "Spring Boot", "ASP.NET", "jQuery", "Bootstrap", "Tailwind", "WordPress"
        ],
        "Databases": [
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Oracle", "SQLite", "Redis", "Cassandra",
            "DynamoDB", "Elasticsearch", "MariaDB", "Firebase"
        ],
        "Cloud & DevOps": [
            "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "Git", "GitHub",
            "CI/CD", "Terraform", "Ansible", "Chef", "Puppet", "Nginx", "Apache"
        ],
        "Data Science": [
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Analysis",
            "Pandas", "NumPy", "SciPy", "Scikit-learn", "TensorFlow", "PyTorch", "Keras",
            "Data Visualization", "Tableau", "Power BI", "Statistics"
        ],
        "Business Skills": [
            "Project Management", "Product Management", "Agile", "Scrum", "Leadership",
            "Communication", "Presentation", "Negotiation", "Customer Service", "Sales",
            "Marketing", "Business Analysis", "Strategic Planning"
        ]
    }
    
    # Flatten the skills list
    all_skills = [skill for category in skills_dict.values() for skill in category]
    
    # Extract skills
    extracted_skills = []
    for skill in all_skills:
        # Look for word boundaries to avoid partial matches
        pattern = r'\b' + skill + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            extracted_skills.append(skill)
    
    return extracted_skills

def get_job_requirements(role: str) -> Dict[str, List[str]]:
    """
    Dynamically get required skills for a given role using Snowflake Cortex.
    No hardcoded roles or skills.
    
    Args:
        role (str): The target role to get skill requirements for
        
    Returns:
        dict: Dictionary with "essential" and "preferred" skill lists
    """
    # Import here to avoid circular import
    from backend.database import get_snowflake_connection
    from backend.services.chat_service import ChatService
    
    try:
        # Try to use ChatService for getting skill requirements
        chat_service = ChatService()
        
        prompt = (
            f"You are a career expert in 2025. For a {role} position, identify two categories of required skills:\n"
            f"1. Essential skills (must-have skills) - list 5 specific skills\n"
            f"2. Preferred skills (nice-to-have skills) - list 5 specific skills\n\n"
            f"Return your answer as a JSON object with 'essential' and 'preferred' arrays. "
            f"Don't include any explanation, just return the JSON."
        )
        
        response = chat_service.get_llm_response(prompt)
        
        # Try to parse JSON response
        try:
            import json
            import re
            
            # Try to find JSON-like structure with regex
            json_pattern = r'\{.*?"essential".*?"preferred".*?\}'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                skills_json = json_match.group(0)
                skills_data = json.loads(skills_json)
                
                # Validate expected format
                if 'essential' in skills_data and 'preferred' in skills_data:
                    if isinstance(skills_data['essential'], list) and isinstance(skills_data['preferred'], list):
                        return skills_data
            
            # If we can't find structured JSON, try fallback query
            return query_for_skills(role)
            
        except Exception as e:
            # If JSON parsing fails, try our query-based approach
            return query_for_skills(role)
            
    except Exception as e:
        # Fallback to database query if chat service fails
        return query_for_skills(role)

def query_for_skills(role: str) -> Dict[str, List[str]]:
    """
    Use Snowflake query to get role requirements without hardcoding.
    
    Args:
        role (str): The target role
        
    Returns:
        dict: Skills categorized as essential and preferred
    """
    try:
        from backend.database import get_snowflake_connection
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Use Snowflake Cortex to search for role requirements
        query = f"""
        SELECT PARSE_JSON(
            SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                'SKILLPATH_SEARCH_POC',
                '{{
                    "query": "What are the essential and preferred skills for a {role} role in 2025?",
                    "columns": ["skill_category", "skill_name"],
                    "limit": 20
                }}'
            )
        )['results'] as results;
        """
        
        cursor.execute(query)
        result = cursor.fetchone()[0]
        
        # Process results
        essential_skills = []
        preferred_skills = []
        
        if result and isinstance(result, list):
            for item in result:
                if 'skill_category' in item and 'skill_name' in item:
                    category = item['skill_category'].lower() if item['skill_category'] else ''
                    skill = item['skill_name']
                    
                    if skill and isinstance(skill, str):
                        if 'essential' in category or 'required' in category or 'must' in category:
                            essential_skills.append(skill)
                        elif 'preferred' in category or 'nice' in category or 'optional' in category:
                            preferred_skills.append(skill)
                        else:
                            # If category is unclear, consider it essential
                            essential_skills.append(skill)
        
        # If no skills found, use an empty list but don't hardcode
        return {
            "essential": essential_skills[:5],  # Limit to 5 skills
            "preferred": preferred_skills[:5]   # Limit to 5 skills
        }
        
    except Exception as e:
        # If all else fails, return empty lists without hardcoding
        return {
            "essential": [],
            "preferred": []
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def match_skills(extracted_skills: List[str], target_role: str) -> Dict[str, Any]:
    """
    Match extracted skills with required skills for the target role.
    Returns analysis of matching and missing skills.
    """
    # Convert all skills to lowercase for case-insensitive matching
    normalized_skills = [skill.lower() for skill in extracted_skills]
    
    # Get job requirements
    job_reqs = get_job_requirements(target_role)
    
    # Analyze skill match
    essential_skills = job_reqs.get("essential", [])
    preferred_skills = job_reqs.get("preferred", [])
    
    # Check which skills are present/missing
    matching_essential = [skill for skill in essential_skills 
                         if any(skill.lower() == s.lower() for s in normalized_skills)]
    
    matching_preferred = [skill for skill in preferred_skills 
                         if any(skill.lower() == s.lower() for s in normalized_skills)]
    
    missing_essential = [skill for skill in essential_skills 
                        if skill not in matching_essential]
    
    missing_preferred = [skill for skill in preferred_skills 
                        if skill not in matching_preferred]
    
    # Calculate match percentages
    essential_match_pct = (len(matching_essential) / len(essential_skills) * 100) if essential_skills else 0
    preferred_match_pct = (len(matching_preferred) / len(preferred_skills) * 100) if preferred_skills else 0
    overall_match_pct = ((len(matching_essential) + len(matching_preferred)) / 
                        (len(essential_skills) + len(preferred_skills)) * 100) if (essential_skills or preferred_skills) else 0
    
    # Return comprehensive analysis
    return {
        "extracted_skills": extracted_skills,
        "essential_skills": essential_skills,
        "preferred_skills": preferred_skills,
        "matching_essential": matching_essential,
        "matching_preferred": matching_preferred,
        "missing_essential": missing_essential,
        "missing_preferred": missing_preferred,
        "match_percentages": {
            "essential": round(essential_match_pct, 1),
            "preferred": round(preferred_match_pct, 1),
            "overall": round(overall_match_pct, 1)
        },
        "recommendations": generate_skill_recommendations(missing_essential, missing_preferred, target_role)
    }

def generate_skill_recommendations(missing_essential: List[str], missing_preferred: List[str], target_role: str) -> str:
    """
    Generate learning recommendations based on missing skills.
    """
    recommendations = f"## Career Transition Path to {target_role}\n\n"
    
    # Prioritize essential skills
    if missing_essential:
        recommendations += "### Critical Skills to Develop:\n"
        for skill in missing_essential:
            recommendations += f"- **{skill}**: This is an essential skill for {target_role} roles.\n"
    
    # Then recommend preferred skills
    if missing_preferred:
        recommendations += "\n### Secondary Skills to Consider:\n"
        for skill in missing_preferred[:3]:  # Limit to top 3
            recommendations += f"- **{skill}**: This will enhance your profile for {target_role} positions.\n"
    
    # Learning resources (this would ideally be skill-specific in a full implementation)
    recommendations += "\n### Recommended Learning Resources:\n"
    recommendations += "- **Online Courses**: Platforms like Coursera, Udemy, and edX offer courses in these areas.\n"
    recommendations += "- **Projects**: Build a portfolio showcasing your new skills.\n"
    recommendations += "- **Certifications**: Industry certifications can validate your expertise.\n"
    recommendations += "- **Networking**: Join communities and attend events related to your target role.\n"
    
    return recommendations