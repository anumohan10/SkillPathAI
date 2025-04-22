from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
import json
from backend.database import get_snowflake_connection
from backend.services.chat_service import ChatService
from backend.services.learning_path_service import store_learning_path
import logging
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
    chat_history: str  # instead of List[ChatMessage]
    cur_timestamp: str
    source_page: str
    role: str

class LearningPathRequest(BaseModel):
    user_id: str
    target_role: str
    current_skills: List[str]
    learning_style: Optional[str] = None
    time_commitment: Optional[str] = None

class LearningPathData(BaseModel):
    name: str
    target_role: str
    top_skills: List[str]
    skill_ratings: dict
    record_id: Optional[str] = None

class CareerQuestionRequest(BaseModel):
    question: str
    user_context: dict

# -------------------- Resume Upload Endpoints --------------------

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

@router.post("/skill-ratings/store")
def store_skill_ratings_endpoint(data: LearningPathData):
    try:
        path_data = data.model_dump()
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

# -------------------- Chat History --------------------

@router.post("/chat-history")
def save_chat_history(data: ChatHistoryRequest):
    try:
        logger.info(f"🛠 Saving chat for: {data.user_name} | Source: {data.source_page} | Role: {data.role}")
        logger.info(f"History length: {len(data.chat_history)}")

        conn = get_snowflake_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Could not connect to database")

        cur = conn.cursor()
        insert_query = """
            INSERT INTO chat_history (user_name, chat_history, cur_timestamp, source_page, role)
            VALUES (%s, %s, %s, %s, %s);
        """
        cur.execute(insert_query, (
            data.user_name,
            json.dumps([msg.dict() for msg in data.chat_history]),
            data.cur_timestamp,
            data.source_page,
            data.role
        ))
        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ Chat saved to Snowflake.")
        return {"message": "Chat history saved successfully"}

    except Exception as e:
        logger.error(f"❌ Error saving chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/chat-history/recent", response_model=List[ChatHistoryResponse])
def fetch_recent_chats(user_name: str, limit: int = Query(5, ge=1, le=20)):
    try:
        conn = get_snowflake_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Could not connect to database")

        cur = conn.cursor()
        cur.execute("""
            SELECT chat_history, cur_timestamp, source_page, role
            FROM chat_history
            WHERE user_name = %s
            ORDER BY cur_timestamp DESC
            LIMIT %s
        """, (user_name, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        logging.info("Data retireved:", rows[:5])
        
        result = []
        for chat_json, timestamp, source, role in rows:
            try:
                # Parse stringified list of dicts
                # messages = json.loads(chat_json) if isinstance(chat_json, str) else chat_json
                # if isinstance(messages, str):  # Handle double-encoding
                #     messages = json.loads(messages)

                result.append(ChatHistoryResponse(
                    user_name=user_name,
                    chat_history=chat_json,
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
