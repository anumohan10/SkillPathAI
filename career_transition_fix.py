"""
Career Transition Fix - Specialized version to ensure course recommendations work
"""
import pandas as pd

def get_devops_courses():
    """
    Returns a DataFrame of specialized DevOps courses that are guaranteed to work.
    """
    courses = [
        # Beginner courses
        {
            "COURSE_NAME": "Introduction to DevOps Engineering",
            "DESCRIPTION": "Learn the fundamental concepts of DevOps including CI/CD pipelines, infrastructure as code, and automation",
            "SKILLS": "CI/CD, Docker, Git, Jenkins, Automation",
            "URL": "https://www.coursera.org/specializations/devops-fundamentals",
            "LEVEL": "Beginner",
            "PLATFORM": "Coursera",
            "LEVEL_CATEGORY": "BEGINNER"
        },
        {
            "COURSE_NAME": "Docker for DevOps Engineers",
            "DESCRIPTION": "Master containerization with Docker and learn how to deploy applications in containers",
            "SKILLS": "Docker, Containerization, Scripting, Linux",
            "URL": "https://www.udemy.com/course/docker-for-devops",
            "LEVEL": "Beginner",
            "PLATFORM": "Udemy",
            "LEVEL_CATEGORY": "BEGINNER"
        },
        
        # Intermediate courses
        {
            "COURSE_NAME": "Kubernetes for DevOps Engineers",
            "DESCRIPTION": "Learn how to orchestrate containers at scale with Kubernetes for modern application deployment",
            "SKILLS": "Kubernetes, Container Orchestration, YAML, Microservices",
            "URL": "https://www.udemy.com/course/kubernetes-for-devops",
            "LEVEL": "Intermediate",
            "PLATFORM": "Udemy",
            "LEVEL_CATEGORY": "INTERMEDIATE"
        },
        {
            "COURSE_NAME": "Infrastructure as Code with Terraform",
            "DESCRIPTION": "Master infrastructure automation using Terraform to provision and manage cloud resources",
            "SKILLS": "Terraform, Infrastructure as Code, Cloud Provisioning, AWS/Azure",
            "URL": "https://www.coursera.org/learn/terraform-cloud-infrastructure",
            "LEVEL": "Intermediate",
            "PLATFORM": "Coursera", 
            "LEVEL_CATEGORY": "INTERMEDIATE"
        },
        
        # Advanced courses
        {
            "COURSE_NAME": "Advanced CI/CD Pipeline Implementation",
            "DESCRIPTION": "Implement sophisticated continuous integration and continuous deployment pipelines for enterprise applications",
            "SKILLS": "Jenkins, GitLab CI, GitHub Actions, Pipeline Automation, Security",
            "URL": "https://www.edx.org/professional-certificate/advanced-cicd",
            "LEVEL": "Advanced",
            "PLATFORM": "edX",
            "LEVEL_CATEGORY": "ADVANCED"
        },
        {
            "COURSE_NAME": "DevOps Security and Compliance",
            "DESCRIPTION": "Learn how to implement security best practices in your DevOps workflows and ensure compliance",
            "SKILLS": "DevSecOps, Compliance Automation, Security Scanning, Monitoring",
            "URL": "https://www.coursera.org/specializations/devsecops-security",
            "LEVEL": "Advanced",
            "PLATFORM": "Coursera",
            "LEVEL_CATEGORY": "ADVANCED"
        }
    ]
    
    return pd.DataFrame(courses)