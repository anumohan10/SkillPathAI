from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
import json

router = APIRouter(
    prefix="/user-input",
    tags=["User Input"]
)

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

class LearningPathRequest(BaseModel):
    user_id: str
    target_role: str
    current_skills: List[str]
    learning_style: Optional[str] = None
    time_commitment: Optional[str] = None

class ChatHistoryData(BaseModel):
    user_name: str
    chat_history: list
    timestamp: Optional[str] = None

class LearningPathData(BaseModel):
    name: str
    target_role: str
    top_skills: List[str]
    skill_ratings: dict
    record_id: Optional[str] = None

class CareerQuestionRequest(BaseModel):
    question: str
    user_context: dict

@router.post("/resume", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Upload and process a resume file
    """
    try:
        content = await file.read()
        # This would process the resume content through your service
        # For example:
        # result = process_resume(content, user_id)
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
    """
    Submit resume as text
    """
    try:
        # This would process the resume text through your service
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

@router.post("/career-transition")
def submit_career_transition_data(data: CareerTransitionData):
    """
    Submit career transition information
    """
    try:
        # This would process the career transition data through your service
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

@router.post("/learning-path")
def generate_learning_path(request: LearningPathRequest):
    """
    Generate a learning path based on user's target role and skills
    """
    try:
        # This would generate a learning path through your service
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

@router.post("/chat-history")
def save_chat_history(data: ChatHistoryData):
    """
    Save user chat history
    """
    try:
        from backend.database import save_chat_history
        
        # Convert chat_history to JSON string if it's not already
        chat_history_str = json.dumps(data.chat_history) if isinstance(data.chat_history, list) else data.chat_history
        
        # Save to database
        flag, message = save_chat_history(
            user_name=data.user_name,
            chat_history=chat_history_str,
            cur_timestamp=data.timestamp
        )
        if flag:
            return {
                "message": message,
                "user_name": data.user_name
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
    """
    Store learning path data
    """
    try:
        from backend.services.learning_path_service import store_learning_path
        
        # Convert courses list to DataFrame if present
        path_data = data.model_dump()
        
        # Store learning path
        record_id = store_learning_path(path_data)
        
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

@router.post("/career-question")
def answer_career_question(request: CareerQuestionRequest):
    """
    Answer a career-related question using the chat service
    """
    try:
        from backend.services.chat_service import ChatService
        
        # Initialize chat service
        chat_service = ChatService()
        
        # Get response from chat service
        flag, response = chat_service.answer_career_question(
            request.question, 
            request.user_context
        )
        if flag:
            return {
                "success": flag,
                "response": response
            }
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
