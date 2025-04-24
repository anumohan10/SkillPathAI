#!/bin/bash

# Function to display help
function show_help {
    echo "SkillPathAI Docker Helper Script"
    echo ""
    echo "Usage: ./docker-run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build the Docker images"
    echo "  start       Start the containers"
    echo "  stop        Stop the containers"
    echo "  restart     Restart the containers"
    echo "  logs        Show the logs"
    echo "  status      Show the status of the containers"
    echo "  clean       Remove all containers and images"
    echo "  help        Show this help message"
    echo ""
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Process commands
case "$1" in
    build)
        echo "Building Docker images..."
        docker-compose build
        ;;
    start)
        echo "Starting containers..."
        docker-compose up -d
        ;;
    stop)
        echo "Stopping containers..."
        docker-compose down
        ;;
    restart)
        echo "Restarting containers..."
        docker-compose restart
        ;;
    logs)
        echo "Showing logs..."
        docker-compose logs -f
        ;;
    status)
        echo "Container status:"
        docker-compose ps
        ;;
    clean)
        echo "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        ;;
    help|*)
        show_help
        ;;
esac 