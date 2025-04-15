# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- Frontend: `cd frontend && streamlit run main.py`
- Backend: `cd backend && python main.py`
- Tests: `python -m pytest tests/`
- Single Test: `python -m pytest tests/test_file.py::test_function`

## Code Style Guidelines
- **Imports**: Standard library first, third-party next, local modules last
- **Formatting**: 4-space indentation, 79-character line length
- **Types**: Type hints encouraged for function parameters and returns
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Use try/except blocks with specific exception types
- **Logging**: Use the `logging` module with appropriate log levels
- **Documentation**: Docstrings for functions/classes using triple quotes
- **Database**: Always close connections in finally blocks
- **Streamlit**: Use session_state for persistent storage between reruns
- **Snowflake**: Use PARSE_JSON for array/object columns in SQL queries