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
    Get required skills for a given role.
    In production, this would connect to a database or API.
    """
    # Define job requirements for common roles
    job_requirements = {
        "Data Scientist": {
            "essential": ["Python", "SQL", "Machine Learning", "Statistics", "Data Analysis"],
            "preferred": ["TensorFlow", "PyTorch", "Pandas", "NumPy", "Data Visualization"]
        },
        "Software Engineer": {
            "essential": ["Python", "Java", "JavaScript", "Git", "Algorithms"],
            "preferred": ["Docker", "Kubernetes", "AWS", "CI/CD", "React", "Angular"]
        },
        "Full Stack Developer": {
            "essential": ["HTML", "CSS", "JavaScript", "Node.js", "SQL"],
            "preferred": ["React", "Angular", "Vue", "MongoDB", "Express", "Django"]
        },
        "Data Analyst": {
            "essential": ["SQL", "Excel", "Data Analysis", "Data Visualization"],
            "preferred": ["Python", "R", "Tableau", "Power BI", "Statistics"]
        },
        "DevOps Engineer": {
            "essential": ["Linux", "Docker", "Kubernetes", "CI/CD", "Cloud"],
            "preferred": ["AWS", "Azure", "Terraform", "Ansible", "Monitoring"]
        },
        "Product Manager": {
            "essential": ["Product Management", "Agile", "Communication", "Strategic Planning"],
            "preferred": ["Technical Background", "UX", "Data Analysis", "Market Research"]
        },
        "UX Designer": {
            "essential": ["User Research", "UI Design", "Wireframing", "Prototyping"],
            "preferred": ["Figma", "Sketch", "Adobe XD", "User Testing", "HTML/CSS"]
        },
        "AI Engineer": {
            "essential": ["Python", "Machine Learning", "Deep Learning", "Math"],
            "preferred": ["TensorFlow", "PyTorch", "NLP", "Computer Vision", "MLOps"]
        }
    }
    
    # Handle case when role is not in our predefined list
    if role not in job_requirements:
        # Return a generic template with empty lists
        return {
            "essential": [],
            "preferred": []
        }
    
    return job_requirements[role]

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