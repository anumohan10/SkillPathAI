#!/bin/bash

# Set default values for environment variables
export SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT:-"your_account"}
export SNOWFLAKE_USER=${SNOWFLAKE_USER:-"your_user"}
export SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD:-"your_password"}
export SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE:-"your_warehouse"}
export SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE:-"your_database"}
export SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA:-"your_schema"}

# Function to check if a port is in use
check_port() {
    if lsof -i:$1 >/dev/null 2>&1; then
        echo "Port $1 is already in use. Please free up the port and try again."
        exit 1
    fi
}

# Check if required ports are available
check_port 8501
check_port 8000

# Build and start the containers
echo "Building and starting containers..."
docker-compose -f docker/docker-compose.yml up --build -d

# Check if containers are running
if [ $? -eq 0 ]; then
    echo "Containers started successfully!"
    echo "Frontend is available at: http://localhost:8501"
    echo "Backend API is available at: http://localhost:8000"
else
    echo "Failed to start containers. Please check the logs for more information."
    exit 1
fi

# Function to handle cleanup on script exit
cleanup() {
    echo "Stopping containers..."
    docker-compose -f docker/docker-compose.yml down
}

# Set up trap to catch script termination
trap cleanup EXIT

# Keep the script running
echo "Press Ctrl+C to stop the containers..."
while true; do
    sleep 1
done 