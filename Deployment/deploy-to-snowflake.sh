#!/bin/bash

# Exit on error
set -e

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found. Please create one with your Snowflake credentials."
  exit 1
fi

# Load environment variables
source .env

# Check if required environment variables are set
required_vars=("SNOWFLAKE_ACCOUNT" "SNOWFLAKE_USER" "SNOWFLAKE_PASSWORD" "SNOWFLAKE_WAREHOUSE" "SNOWFLAKE_DATABASE" "SNOWFLAKE_SCHEMA" "SNOWFLAKE_ROLE")
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: $var is not set in .env file."
    exit 1
  fi
done

# Build Docker images
echo "Building Docker images..."
docker build -t skillpathai-frontend -f Dockerfile .
docker build -t skillpathai-backend -f Dockerfile .

# Tag images for Snowflake Container Registry
echo "Tagging images for Snowflake Container Registry..."
docker tag skillpathai-frontend ${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/skillpathai/frontend:latest
docker tag skillpathai-backend ${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/skillpathai/backend:latest

# Login to Snowflake Container Registry
echo "Logging in to Snowflake Container Registry..."
echo "${SNOWFLAKE_PASSWORD}" | docker login ${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com -u ${SNOWFLAKE_USER} --password-stdin

# Push images to Snowflake Container Registry
echo "Pushing images to Snowflake Container Registry..."
docker push ${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/skillpathai/frontend:latest
docker push ${SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/skillpathai/backend:latest

# Deploy to Snowflake Container Services
echo "Deploying to Snowflake Container Services..."
snowsql -a ${SNOWFLAKE_ACCOUNT} -u ${SNOWFLAKE_USER} -w ${SNOWFLAKE_WAREHOUSE} -d ${SNOWFLAKE_DATABASE} -s ${SNOWFLAKE_SCHEMA} -f deploy-to-snowflake.sql

echo "Deployment completed successfully!" 