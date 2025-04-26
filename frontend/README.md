# SkillPathAI Frontend

## Overview
SkillPathAI Frontend is a Streamlit-based web application that provides a user-friendly interface for career transition and skill development. The application features a modern, responsive design with a focus on user experience and seamless navigation.

## Features
- **Authentication System**
  - User Login
  - User Registration
  - Password Recovery
  - Secure Session Management

- **Dashboard**
  - Personalized user dashboard
  - Career transition insights
  - Learning path recommendations
  - Progress tracking

- **Career Transition Tools**
  - Career path analysis
  - Skill gap assessment
  - Transition planning
  - Job market insights

- **Learning Path Management**
  - Course recommendations
  - Skill development tracking
  - Progress monitoring
  - Personalized learning plans

## Project Structure
```
frontend/
├── assets/           # Static assets (images, icons)
├── components/       # Reusable UI components
├── logs/            # Application logs
├── .streamlit/      # Streamlit configuration
├── auth_page.py     # Authentication pages
├── career_transition_page.py  # Career transition features
├── courses_page.py  # Course management
├── dashboard.py     # Main dashboard logic
├── dashboard_page.py # Dashboard UI
├── guidance_hub_page.py # Guidance and support
├── learning_path_page.py # Learning path management
├── main.py         # Application entry point
├── profile_page.py # User profile management
├── styles.css      # Custom styling
└── ui_formatter.py # UI formatting utilities
```

## Technical Stack
- **Framework**: Streamlit
- **Styling**: Custom CSS
- **Authentication**: Session-based
- **Logging**: Python logging module
- **File Structure**: Modular design with separate components

## Getting Started

### Prerequisites
- Python 3.7+
- Streamlit
- Required packages (see requirements.txt)

### Installation
1. Clone the repository
2. Navigate to the frontend directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
```bash
streamlit run main.py
```

## Key Components

### Authentication System
The application implements a secure authentication system with:
- Login page
- Signup page
- Password recovery
- Session management

### Dashboard
The main dashboard provides:
- User overview
- Career insights
- Learning progress
- Quick access to features

### Career Transition
Features include:
- Career path analysis
- Skill assessment
- Transition planning
- Market insights

### Learning Path
Comprehensive learning management with:
- Course recommendations
- Progress tracking
- Skill development
- Personalized plans

## Styling
The application uses a custom CSS file (`styles.css`) for consistent styling across all pages. The design follows modern UI/UX principles with:
- Responsive layouts
- Clean typography
- Consistent color scheme
- Intuitive navigation

## Logging
The application implements comprehensive logging:
- Error tracking
- User actions
- System events
- Debug information

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

