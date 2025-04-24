# SkillPathAI Docker Setup

This document provides instructions for running the SkillPathAI application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Snowflake account credentials

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd SkillPathAI
   ```

2. Create a `.env` file based on the `.env.example` template:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file with your Snowflake credentials:
   ```
   # Snowflake Connection
   SNOWFLAKE_ACCOUNT=your_account
   SNOWFLAKE_USER=your_user
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_WAREHOUSE=your_warehouse
   SNOWFLAKE_DATABASE=your_database
   SNOWFLAKE_SCHEMA=your_schema
   ```

## Running the Application

1. Build and start the containers:
   ```
   docker-compose up -d
   ```

2. Access the application:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000

3. To stop the application:
   ```
   docker-compose down
   ```

## Development

For development, you can use the volume mounts to make changes to the code without rebuilding the containers:

1. Make changes to the code in the `frontend` or `backend` directories
2. The changes will be reflected in the running containers

## Troubleshooting

- Check the logs:
  ```
  docker-compose logs -f
  ```

- Rebuild the containers:
  ```
  docker-compose up -d --build
  ```

- Check container status:
  ```
  docker-compose ps
  ``` 