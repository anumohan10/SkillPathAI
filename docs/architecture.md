# SkillPathAI System Architecture

## 1. High-Level System Overview

```
[User Interface Layer] ←→ [Application Layer] ←→ [Data Layer]
```

## 2. Component Architecture

### A. Frontend Layer (Streamlit)
```
├── Main Application (main.py)
├── Authentication (auth.py)
├── UI Components
│   ├── Dashboard (dashboard.py, dashboard_page.py)
│   ├── Career Transition (career_transition_page.py)
│   ├── Learning Path (learning_path_page.py)
│   ├── Courses (courses_page.py)
│   ├── Profile (profile_page.py)
│   └── Guidance Hub (guidance_hub_page.py)
├── UI Services (ui_formatter.py)
└── Assets & Styling
    ├── CSS (styles.css)
    └── Static Assets (assets/)
```

### B. Backend Layer (FastAPI)
```
├── API Routes
│   ├── User Input (/api/routes/user_input.py)
│   └── Recommendations (/api/routes/recommendations.py)
├── Services
│   ├── Chat Service
│   ├── Resume Parser
│   ├── Skill Matcher
│   └── Career Transition Service
└── Database Interface (database.py)
```

### C. ETL Layer
```
├── Extract
├── Transform
├── Load
└── Cortex Queries
```

## 3. Data Flow Architecture

```
[User] → [Frontend UI] → [Backend API] → [Services] → [Database]
```

### A. Career Transition Flow
```
1. User Input
   ├── Name Collection
   ├── Resume Upload
   └── Target Role Selection

2. Data Processing
   ├── Resume Text Extraction
   ├── Skill Extraction
   └── Missing Skills Analysis

3. Recommendation Generation
   ├── Course Matching
   ├── Learning Path Creation
   └── Transition Plan Generation

4. Results Display
   ├── Skill Assessment
   ├── Course Recommendations
   └── Career Advice
```

## 4. Integration Points

### A. Frontend-Backend Communication
```
[Streamlit UI] ←→ [FastAPI Endpoints] ←→ [Service Layer]
```

### B. Data Storage
```
[Services] ←→ [Database] ←→ [ETL Pipeline]
```

## 5. Key Features

### A. Authentication & Authorization
- User authentication
- Session management
- Role-based access

### B. Career Analysis
- Resume parsing
- Skill extraction
- Gap analysis
- Course recommendations

### C. Learning Management
- Personalized learning paths
- Course tracking
- Progress monitoring

### D. User Interface
- Interactive chat interface
- Dashboard visualization
- Progress tracking
- Course recommendations

## 6. Technical Stack

### A. Frontend
- Streamlit
- Python
- CSS
- Markdown

### B. Backend
- FastAPI
- Python
- SQL Database
- LLM Integration

### C. Data Processing
- ETL Pipeline
- Data Transformation
- Query Processing

## 7. Security Architecture

```
[User] → [Authentication] → [Authorization] → [API Gateway] → [Services]
```

## 8. Monitoring & Logging

```
[Application Logs] → [Logging Service] → [Monitoring Dashboard]
```

## 9. Error Handling

```
[Error Detection] → [Error Logging] → [Error Recovery] → [User Notification]
```

## 10. Scalability Considerations

### A. Horizontal Scaling
- API Services
- Database
- ETL Processes

### B. Vertical Scaling
- Frontend Server
- Backend Services
- Database Server

## How to Use This Architecture with Lucid

1. Create boxes for each major component
2. Draw arrows to show data flow and relationships
3. Group related components into layers
4. Add color coding for different types of components
5. Include icons for different services and technologies

The architecture follows a modern microservices pattern with clear separation of concerns and well-defined interfaces between components. It's designed to be scalable, maintainable, and extensible while providing a robust platform for career transition and learning path management. 