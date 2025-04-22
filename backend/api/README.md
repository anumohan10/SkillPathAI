# SkillPathAI Backend API

This directory contains the FastAPI implementation for the SkillPathAI backend services.

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

2. Make sure your .env file is correctly set up in the backend directory.

## Running the API Server

From the root directory of the project, run:

```bash
# Go to the backend directory
cd backend

# Run the FastAPI app
python -m api.main
```

The API will start running at http://localhost:8000

## API Documentation

Once the server is running, you can access the auto-generated API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- POST `/auth/signup` - Create a new user account
- POST `/auth/login` - Log in with existing credentials

### Recommendations
- POST `/recommendations/courses` - Get course recommendations for a target role
- GET `/recommendations/skills/top/{role}` - Get top skills for a specific role

### User Input
- POST `/user-input/resume` - Upload and process a resume file
- POST `/user-input/resume/text` - Submit resume as text
- POST `/user-input/career-transition` - Submit career transition information
- POST `/user-input/learning-path` - Generate a learning path
- POST `/user-input/chat-history` - Save user chat history
- POST `/user-input/skill-ratings/store` - Store skill ratings and learning path data
- POST `/user-input/career-question` - Answer career-related questions
- POST `/user-input/resume/extract` - Extract text from a resume file (PDF/DOCX)
- POST `/user-input/skills/extract` - Extract skills from resume text using LLM
- POST `/user-input/skills/extract-regex` - Extract skills from resume text using regex
- POST `/user-input/skills/missing` - Process missing skills for a target role
- POST `/user-input/career-analysis/store` - Store career analysis data
- POST `/user-input/career-courses` - Get career transition courses
- POST `/user-input/transition-plan` - Format transition plan

## Request/Response Models

### Authentication
```python
class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    name: str
    username: str
    email: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
```

### Recommendations
```python
class RoleCourseRequest(BaseModel):
    role: str
    limit: Optional[int] = 5
    user_id: Optional[int] = None

class Course(BaseModel):
    COURSE_NAME: str
    DESCRIPTION: str
    SKILLS: str
    URL: str
    LEVEL: Optional[str] = None
    PLATFORM: Optional[str] = None
    LEVEL_CATEGORY: Optional[str] = None
```

### Resume Data
```python
class ResumeData(BaseModel):
    user_id: str
    resume_text: str
    target_role: Optional[str] = None
```

### Career Transition
```python
class CareerTransitionData(BaseModel):
    user_id: str
    current_role: str
    target_role: str
    experience_years: int
    education_level: str
    preferred_learning_style: Optional[str] = None
    time_commitment: Optional[str] = None
```

### Learning Path
```python
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
```

### Chat
```python
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatHistoryData(BaseModel):
    user_name: str
    chat_history: list
    timestamp: Optional[str] = None

class CareerQuestionRequest(BaseModel):
    question: str
    user_context: dict
```

### Resume Extraction
```python
class ResumeExtractResponse(BaseModel):
    success: bool
    text: str
    message: Optional[str] = None
```

### Skills Extraction
```python
class SkillsExtractRequest(BaseModel):
    resume_text: str

class SkillsExtractResponse(BaseModel):
    success: bool
    skills: List[str]
    message: Optional[str] = None
```

### Missing Skills
```python
class MissingSkillsRequest(BaseModel):
    extracted_skills: List[str]
    target_role: str

class MissingSkillsResponse(BaseModel):
    success: bool
    missing_skills: List[str]
    message: Optional[str] = None
```

### Career Analysis
```python
class CareerAnalysisRequest(BaseModel):
    username: str
    resume_text: str
    extracted_skills: List[str]
    target_role: str
    missing_skills: List[str]

class CareerAnalysisResponse(BaseModel):
    success: bool
    resume_id: Optional[str] = None
    message: Optional[str] = None
```

### Career Courses
```python
class CareerCoursesRequest(BaseModel):
    target_role: str
    missing_skills: List[str]
    limit: Optional[int] = 6

class CareerCoursesResponse(BaseModel):
    success: bool
    courses: List[Dict[str, Any]]
    count: int
    message: Optional[str] = None
```

### Transition Plan
```python
class TransitionPlanRequest(BaseModel):
    username: str
    current_skills: List[str]
    target_role: str
    missing_skills: List[str]
    courses: List[Dict[str, Any]]

class TransitionPlanResponse(BaseModel):
    success: bool
    introduction: str
    skill_assessment: str
    course_recommendations: str
    career_advice: str
    has_valid_courses: bool
    message: Optional[str] = None
```

## Migration from Direct Function Calls

When converting frontend components to use the API:

1. Import the requests library: `import requests`
2. Set the API URL (consider using an environment variable): `API_URL = "http://localhost:8000"`
3. Replace direct function calls with API requests:

```python
# Before
result = backend_function(param1, param2)

# After
response = requests.post(f"{API_URL}/endpoint", json={"param1": param1, "param2": param2})
result = response.json()
```

4. Add error handling for API requests:

```python
try:
    response = requests.post(f"{API_URL}/endpoint", json={"param1": param1, "param2": param2})
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("result")
        else:
            logger.warning(f"API returned failure: {data.get('message')}")
            return None
    else:
        logger.error(f"API error: {response.status_code}")
        return None
except Exception as e:
    logger.error(f"Error calling API: {str(e)}")
    return None
```

5. For file uploads, use the `files` parameter:

```python
files = {"file": (file.name, file, file.type)}
response = requests.post(f"{API_URL}/upload", files=files)
``` 