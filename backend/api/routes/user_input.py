from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import uuid4
import json
import logging
from backend.services.chat_service import ChatService
# from backend.database import save_chat_history, store_skill_ratings
from backend.services.resume_parser import extract_text

from backend.services.career_transition_service import (
    process_missing_skills, 
    store_career_analysis, 
    get_career_transition_courses, 
    format_transition_plan
)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/user-input",
    tags=["User Input"]
)

# -------------------- Pydantic Models --------------------

class ResumeData(BaseModel):
    user_id: str
    resume_text: str
    target_role: Optional[str] = None

class CareerTransitionData(BaseModel):
    user_id: str
    current_role: str
    target_role: str
    experience_years: int
    education_level: str
    preferred_learning_style: Optional[str] = None
    time_commitment: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatHistoryRequest(BaseModel):
    user_name: str
    chat_history: List[ChatMessage]
    cur_timestamp: str
    source_page: str
    role: str  # now mandatory

class ChatHistoryResponse(BaseModel):
    user_name: str
    state_data: str  # instead of List[ChatMessage]
    cur_timestamp: str
    source_page: str
    role: str

class LearningPathRequest(BaseModel):
    user_id: str
    target_role: str
    current_skills: List[str]
    learning_style: Optional[str] = None
    time_commitment: Optional[str] = None

class SessionStateData(BaseModel):
    user_name: str
    session_state: str
    timestamp: str
    source_page: str
    role: str

class LearningPathData(BaseModel):
    name: str
    target_role: str
    top_skills: List[str]
    skill_ratings: dict
    record_id: Optional[str] = None

class CareerQuestionRequest(BaseModel):
    question: str
    user_context: dict

class ResumeExtractResponse(BaseModel):
    """Response model for resume text extraction."""
    success: bool
    text: str
    message: Optional[str] = None

class SkillsExtractRequest(BaseModel):
    """Request model for skills extraction."""
    resume_text: str

class SkillsExtractResponse(BaseModel):
    """Response model for skills extraction."""
    success: bool
    skills: List[str]
    message: Optional[str] = None

class MissingSkillsRequest(BaseModel):
    """Request model for missing skills analysis."""
    extracted_skills: List[str]
    target_role: str

class MissingSkillsResponse(BaseModel):
    """Response model for missing skills analysis."""
    success: bool
    missing_skills: List[str]
    message: Optional[str] = None

class CareerAnalysisRequest(BaseModel):
    """Request model for career analysis storage."""
    username: str
    resume_text: str
    extracted_skills: List[str]
    target_role: str
    missing_skills: List[str]

class CareerAnalysisResponse(BaseModel):
    """Response model for career analysis storage."""
    success: bool
    resume_id: Optional[str] = None
    message: Optional[str] = None

class CareerCoursesRequest(BaseModel):
    """Request model for career transition courses."""
    target_role: str
    missing_skills: List[str]
    limit: Optional[int] = 6

class CareerCoursesResponse(BaseModel):
    """Response model for career transition courses."""
    success: bool
    courses: List[Dict[str, Any]]
    count: int
    message: Optional[str] = None

class TransitionPlanRequest(BaseModel):
    """Request model for transition plan formatting."""
    username: str
    current_skills: List[str]
    target_role: str
    missing_skills: List[str]
    courses: List[Dict[str, Any]]

class TransitionPlanResponse(BaseModel):
    """Response model for transition plan formatting."""
    success: bool
    introduction: str
    skill_assessment: str
    course_recommendations: str
    career_advice: str
    has_valid_courses: bool
    message: Optional[str] = None

@router.post("/resume", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    try:
        content = await file.read()
        return {
            "message": "Resume uploaded successfully",
            "file_name": file.filename,
            "user_id": user_id,
            "resume_id": str(uuid4())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume: {str(e)}"
        )

@router.post("/resume/text")
def submit_resume_text(data: ResumeData):
    try:
        return {
            "message": "Resume processed successfully",
            "user_id": data.user_id,
            "resume_id": str(uuid4()),
            "target_role": data.target_role
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume text: {str(e)}"
        )

# -------------------- Career Transition --------------------

@router.post("/career-transition")
def submit_career_transition_data(data: CareerTransitionData):
    try:
        return {
            "message": "Career transition data processed successfully",
            "user_id": data.user_id,
            "current_role": data.current_role,
            "target_role": data.target_role
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing career transition data: {str(e)}"
        )

# -------------------- Learning Path --------------------

@router.post("/learning-path")
def generate_learning_path(request: LearningPathRequest):
    try:
        return {
            "message": "Learning path generated successfully",
            "user_id": request.user_id,
            "target_role": request.target_role,
            "path_id": str(uuid4())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating learning path: {str(e)}"
        )

@router.post("/save-session-state")
def save_session_state(data: SessionStateData):
    """
    Save user session state
    """
    try:
        from backend.database import save_session_state
        
        # Convert session_state to JSON string if it's not already
        session_state_str = json.dumps(data.session_state) if isinstance(data.session_state, list) else data.session_state
        
        # Save to database
        flag, message = save_session_state(
            user_name=data.user_name,
            session_state=session_state_str,
            cur_timestamp=data.timestamp,
            source_page= data.source_page,
            role= data.role
        )
        if flag:
            return {
                "message": message,
                "user_name": data.user_name,
                "source_page": data.source_page,
                "target_role": data.target_role
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving chat history: {message}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving chat history: {str(e)}"
        )

@router.post("/skill-ratings/store")
def store_skill_ratings_endpoint(data: LearningPathData):
    try:
        path_data = data.model_dump()
        record_id = store_career_analysis(path_data)
        if record_id:
            return {
                "success": True,
                "message": "Learning path stored successfully",
                "record_id": record_id
            }
        else:
            return {
                "success": False,
                "message": "Learning path stored, but no ID was returned",
                "record_id": None
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing learning path: {str(e)}"
        )


@router.get("/chat-history/recent", response_model=List[ChatHistoryResponse])
def fetch_recent_chats(user_name: str, limit: int = Query(5, ge=1, le=20)):
    try:
        from backend.database import retrieve_session_state
        rows = retrieve_session_state(user_name, limit)
        
        logging.info("Data retrieved:", rows[:5])
        
        result = []
        for state_data, timestamp, source, role in rows:
            try:
                # Parse stringified list of dicts
                # messages = json.loads(chat_json) if isinstance(chat_json, str) else chat_json
                # if isinstance(messages, str):  # Handle double-encoding
                #     messages = json.loads(messages)

                result.append(ChatHistoryResponse(
                    user_name=user_name,
                    state_data=state_data,
                    cur_timestamp=str(timestamp),
                    source_page=source,
                    role=role
                ))
            except Exception as e:
                logger.warning(f"Skipping invalid chat record: {e}")
                continue

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# -------------------- Career Questions --------------------

@router.post("/career-question")
def answer_career_question(request: CareerQuestionRequest):
    try:
        chat_service = ChatService()
        flag, response = chat_service.answer_career_question(
            request.question,
            request.user_context
        )
        if flag:
            return {"success": True, "response": response}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error answering your question: {response}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error answering your question: {str(e)}"
        )

@router.post("/resume/extract", response_model=ResumeExtractResponse)
async def extract_resume_text(file: UploadFile = File(...)):
    """Extract text from a resume file (PDF or DOCX)."""
    try:
        # Check file type
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Extract text from the file
        extracted_text = extract_text(file)
        
        # Check if extraction was successful
        if not extracted_text or len(extracted_text) < 50:
            return ResumeExtractResponse(
                success=False,
                text="",
                message="Could not extract enough text from the file. Please try a different file."
            )
        
        # Return successful response
        return ResumeExtractResponse(
            success=True,
            text=extracted_text,
            message="Text extracted successfully"
        )
    except Exception as e:
        logging.error(f"Error extracting text from resume: {str(e)}")
        return ResumeExtractResponse(
            success=False,
            text="",
            message="Sorry, we're having trouble processing your resume. Please try again later."
        )

@router.post("/skills/extract", response_model=SkillsExtractResponse)
async def extract_skills_endpoint(request: SkillsExtractRequest):
    """Extract skills from resume text using LLM."""
    try:
        # Initialize chat service
        chat_service = ChatService()
        
        # Extract skills using LLM
        extracted_skills = chat_service.extract_skills(request.resume_text)
        
        if not extracted_skills:
            return SkillsExtractResponse(
                success=False,
                skills=[],
                message="Could not extract skills from the resume text."
            )
        
        return SkillsExtractResponse(
            success=True,
            skills=extracted_skills,
            message="Skills extracted successfully"
        )
    except Exception as e:
        logging.error(f"Error extracting skills: {str(e)}")
        return SkillsExtractResponse(
            success=False,
            skills=[],
            message="Sorry, we're having trouble extracting skills at the moment. Please try again later."
        )

@router.post("/skills/extract-regex", response_model=SkillsExtractResponse)
async def extract_skills_regex_endpoint(request: SkillsExtractRequest):
    """Returns error message as we're removing regex-based extraction."""
    # We're no longer using regex-based extraction
    return SkillsExtractResponse(
        success=False,
        skills=[],
        message="Cannot process your request at this moment. Please try again later."
    )

@router.post("/skills/missing", response_model=MissingSkillsResponse)
async def process_missing_skills_endpoint(request: MissingSkillsRequest):
    """Process missing skills for a target role."""
    try:
        # Process missing skills
        missing_skills = process_missing_skills(
            request.extracted_skills, 
            request.target_role
        )
        
        if not missing_skills:
            return MissingSkillsResponse(
                success=False,
                missing_skills=[],
                message="Could not identify missing skills at this time. Please try again later."
            )
            
        # Check if the response contains an error message
        error_indicators = ["sorry", "trouble", "try again", "error", "couldn't"]
        for skill in missing_skills:
            if any(indicator in skill.lower() for indicator in error_indicators):
                return MissingSkillsResponse(
                    success=False,
                    missing_skills=[],
                    message="Sorry, we're having trouble analyzing skill gaps at the moment. Please try again later."
                )
        
        return MissingSkillsResponse(
            success=True,
            missing_skills=missing_skills,
            message="Missing skills identified successfully"
        )
    except Exception as e:
        logging.error(f"Error processing missing skills: {str(e)}")
        return MissingSkillsResponse(
            success=False,
            missing_skills=[],
            message="Sorry, we're having trouble analyzing skill gaps at the moment. Please try again later."
        )

@router.post("/career-analysis/store", response_model=CareerAnalysisResponse)
async def store_career_analysis_endpoint(request: CareerAnalysisRequest):
    """Store career analysis data."""
    try:
        # Ensure missing_skills is not empty
        if not request.missing_skills or len(request.missing_skills) == 0:
            # Try to generate missing skills if not provided
            missing_skills = process_missing_skills(
                request.extracted_skills, 
                request.target_role
            )
            if missing_skills and len(missing_skills) > 0:
                request.missing_skills = missing_skills
                
        # Store career analysis with missing skills
        resume_id = store_career_analysis(
            username=request.username,
            resume_text=request.resume_text,
            extracted_skills=request.extracted_skills,
            target_role=request.target_role,
            missing_skills=request.missing_skills
        )
        
        if not resume_id:
            return CareerAnalysisResponse(
                success=False,
                message="Failed to store career analysis data. Please try again later."
            )
        
        return CareerAnalysisResponse(
            success=True,
            resume_id=resume_id,
            message="Career analysis stored successfully with missing skills"
        )
    except Exception as e:
        logging.error(f"Error storing career analysis: {str(e)}")
        return CareerAnalysisResponse(
            success=False,
            message="Sorry, we're having trouble storing your career analysis. Please try again later."
        )

@router.post("/career-courses", response_model=CareerCoursesResponse)
async def get_career_transition_courses_endpoint(request: CareerCoursesRequest):
    """Get career transition courses based on missing skills."""
    try:
        # Validate missing skills input
        if not request.missing_skills or len(request.missing_skills) == 0:
            # Try to get the latest resume entry for this target role to find missing skills
            # This would require the username, which we don't have in this endpoint
            # For now, return an error message recommending the proper flow
            return CareerCoursesResponse(
                success=False,
                courses=[],
                count=0,
                message="No missing skills provided. Please analyze your resume first to identify skill gaps."
            )
            
        # Get career transition courses based on missing skills
        courses_result = get_career_transition_courses(
            target_role=request.target_role,
            missing_skills=request.missing_skills,
            limit=request.limit
        )
        
        if not courses_result or courses_result.get("count", 0) == 0:
            return CareerCoursesResponse(
                success=False,
                courses=[],
                count=0,
                message="No courses found for your missing skills. Please try with different skills or a different target role."
            )
        
        return CareerCoursesResponse(
            success=True,
            courses=courses_result.get("courses", []),
            count=courses_result.get("count", 0),
            message="Courses recommended successfully based on your missing skills"
        )
    except Exception as e:
        logging.error(f"Error getting career transition courses: {str(e)}")
        return CareerCoursesResponse(
            success=False,
            courses=[],
            count=0,
            message="Sorry, we're having trouble finding courses for you right now. Please try again later."
        )

@router.post("/transition-plan", response_model=TransitionPlanResponse)
async def format_transition_plan_endpoint(request: TransitionPlanRequest):
    """Format transition plan."""
    try:
        # Format transition plan
        transition_plan = format_transition_plan(
            username=request.username,
            current_skills=request.current_skills,
            target_role=request.target_role,
            missing_skills=request.missing_skills,
            courses=request.courses
        )
        
        return TransitionPlanResponse(
            success=True,
            introduction=transition_plan.get("introduction", ""),
            skill_assessment=transition_plan.get("skill_assessment", ""),
            course_recommendations=transition_plan.get("course_recommendations", ""),
            career_advice=transition_plan.get("career_advice", ""),
            has_valid_courses=transition_plan.get("has_valid_courses", False),
            message="Transition plan formatted successfully"
        )
    except Exception as e:
        logging.error(f"Error formatting transition plan: {str(e)}")
        return TransitionPlanResponse(
            success=False,
            introduction="",
            skill_assessment="",
            course_recommendations="",
            career_advice="",
            has_valid_courses=False,
            message="Sorry, we're having trouble generating your transition plan. Please try again later."
        )
        
class ResumeCoursesRequest(BaseModel):
    """Request model for getting courses based on resume missing skills."""
    username: str
    target_role: Optional[str] = None
    limit: Optional[int] = 6

@router.post("/resume-courses", response_model=CareerCoursesResponse)
async def get_resume_courses_endpoint(request: ResumeCoursesRequest):
    """Get course recommendations based on missing skills from the most recent resume."""
    try:
        from backend.database import get_latest_resume_missing_skills
        
        # Get missing skills from the most recent resume
        missing_skills = get_latest_resume_missing_skills(
            username=request.username,
            target_role=request.target_role
        )
        
        if not missing_skills:
            return CareerCoursesResponse(
                success=False,
                courses=[],
                count=0,
                message="No missing skills found in your resume. Please analyze your resume first."
            )
        
        # Get career transition courses based on missing skills
        courses_result = get_career_transition_courses(
            target_role=request.target_role,
            missing_skills=missing_skills,
            limit=request.limit
        )
        
        if not courses_result or courses_result.get("count", 0) == 0:
            return CareerCoursesResponse(
                success=False,
                courses=[],
                count=0,
                message="No courses found for your missing skills. Please try with a different target role."
            )
        
        return CareerCoursesResponse(
            success=True,
            courses=courses_result.get("courses", []),
            count=courses_result.get("count", 0),
            message=f"Courses recommended successfully based on your resume's missing skills for {request.target_role}"
        )
    except Exception as e:
        logging.error(f"Error getting courses from resume: {str(e)}")
        return CareerCoursesResponse(
            success=False,
            courses=[],
            count=0,
            message="Sorry, we're having trouble finding courses for you right now. Please try again later."
        )
