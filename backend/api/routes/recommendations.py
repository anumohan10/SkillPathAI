from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from backend.services.skill_service import  get_top_skills_for_role
# from backend.services.course_service import get_courses_for_skills

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)

class SkillRecommendationRequest(BaseModel):
    user_id: str
    current_skills: List[str]
    target_role: str

class SkillRecommendationResponse(BaseModel):
    missing_skills: List[str]
    recommended_skills: List[str]

class CourseRecommendationRequest(BaseModel):
    skills: List[str]
    limit: Optional[int] = 5

class Course(BaseModel):
    COURSE_NAME: str
    DESCRIPTION: str
    SKILLS: str
    URL: str
    LEVEL: Optional[str] = None
    PLATFORM: Optional[str] = None
    LEVEL_CATEGORY: Optional[str] = None


class RoleCourseRequest(BaseModel):
    role: str
    limit: Optional[int] = 5
    user_id: Optional[int] = None

# @router.post("/skills", response_model=SkillRecommendationResponse)
# def get_skill_recommendations_api(request: SkillRecommendationRequest):
#     try:
#         recommendations = get_skill_recommendations(
#             request.user_id,
#             request.current_skills,
#             request.target_role
#         )
#         return recommendations
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error getting skill recommendations: {str(e)}"
#         )

@router.post("/courses", response_model=List[Course])
def get_courses_recommendations_for_role(request: RoleCourseRequest):
    """
    Get course recommendations for a specific role
    """
    try:
        from backend.services.course_service import get_course_recommendations
        
        # Get course recommendations from the service
        courses = get_course_recommendations(request.role, request.user_id)
        
        # Convert DataFrame to list of dictionaries
        
        
        return courses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting course recommendations for role {request.role}: {str(e)}"
        )

@router.get("/skills/top/{role}")
def get_top_skills(role: str):
    """
    Get the top skills for a specific role
    """
    try:
        # Get top skills from the service
        skills = get_top_skills_for_role(role)
        
        if skills:
            return {
                "success": True,
                "role": role,
                "skills": skills
            }
        else:
            return {
                "success": False,
                "role": role,
                "message": f"No skills found for role: {role}",
                "skills": []
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting top skills for role {role}: {str(e)}"
        )
