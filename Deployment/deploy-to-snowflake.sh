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

# Format Snowflake account identifier
# Remove any existing .snowflakecomputing.com suffix
SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT%.snowflakecomputing.com}
# Remove any existing https:// prefix
SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT#https://}
# Remove any existing http:// prefix
SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT#http://}

# Convert database and schema names to lowercase
SNOWFLAKE_DATABASE_LOWER=$(echo "${SNOWFLAKE_DATABASE}" | tr '[:upper:]' '[:lower:]')
SNOWFLAKE_SCHEMA_LOWER=$(echo "${SNOWFLAKE_SCHEMA}" | tr '[:upper:]' '[:lower:]')

# Build Docker images
echo "Building Docker images..."
docker build -t skillpathai-frontend -f docker/Dockerfile.frontend .
docker build -t skillpathai-backend -f docker/Dockerfile.backend .

# Tag images for Snowflake Container Registry
echo "Tagging images for Snowflake Container Registry..."
docker tag skillpathai-frontend ${SNOWFLAKE_ACCOUNT}.registry.snowflakecomputing.com/${SNOWFLAKE_DATABASE_LOWER}/${SNOWFLAKE_SCHEMA_LOWER}/skillpath_repo/frontend:latest
docker tag skillpathai-backend ${SNOWFLAKE_ACCOUNT}.registry.snowflakecomputing.com/${SNOWFLAKE_DATABASE_LOWER}/${SNOWFLAKE_SCHEMA_LOWER}/skillpath_repo/backend:latest

# Login to Snowflake Container Registry
echo "Logging in to Snowflake Container Registry..."
if ! echo "${SNOWFLAKE_PASSWORD}" | docker login ${SNOWFLAKE_ACCOUNT}.registry.snowflakecomputing.com -u ${SNOWFLAKE_USER} --password-stdin; then
  echo "Error: Failed to login to Snowflake Container Registry. Please check:"
  echo "1. Your Snowflake account has Container Services enabled"
  echo "2. Your account identifier is correct (current: ${SNOWFLAKE_ACCOUNT})"
  echo "3. Your credentials are correct"
  exit 1
fi

# Push images to Snowflake Container Registry
echo "Pushing images to Snowflake Container Registry..."
docker push ${SNOWFLAKE_ACCOUNT}.registry.snowflakecomputing.com/${SNOWFLAKE_DATABASE_LOWER}/${SNOWFLAKE_SCHEMA_LOWER}/skillpath_repo/frontend:latest
docker push ${SNOWFLAKE_ACCOUNT}.registry.snowflakecomputing.com/${SNOWFLAKE_DATABASE_LOWER}/${SNOWFLAKE_SCHEMA_LOWER}/skillpath_repo/backend:latest

# Deploy to Snowflake Container Services
echo "Deploying to Snowflake Container Services..."
snowsql -a ${SNOWFLAKE_ACCOUNT} -u ${SNOWFLAKE_USER} -w ${SNOWFLAKE_WAREHOUSE} -d ${SNOWFLAKE_DATABASE} -s ${SNOWFLAKE_SCHEMA} -f "$(dirname "$0")/deploy-to-snowflake.sql"

echo "Deployment completed successfully!" 