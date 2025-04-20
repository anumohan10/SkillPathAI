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
- POST `/recommendations/skills` - Get skill recommendations for a target role
- POST `/recommendations/courses` - Get course recommendations for specified skills

### Search
- POST `/search` - Search across courses, skills, and jobs

### User Input
- POST `/user-input/resume` - Upload and process a resume file
- POST `/user-input/resume/text` - Submit resume as text
- POST `/user-input/career-transition` - Submit career transition information
- POST `/user-input/learning-path` - Generate a learning path

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

4. Add error handling for API requests 