-- Create a compute pool for the containers
CREATE COMPUTE POOL IF NOT EXISTS skillpathai_pool
  MIN_NODES = 1
  MAX_NODES = 3
  INSTANCE_FAMILY = CPU_X64_XS;

-- Create a service for the backend
CREATE SERVICE IF NOT EXISTS skillpathai_backend
  IN COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU
  SPECIFICATION_FILE = 'snowflake-container-config.yml'
  MIN_INSTANCES = 1
  MAX_INSTANCES = 3;

-- Create a service for the frontend
CREATE SERVICE IF NOT EXISTS skillpathai_frontend
  IN COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU
  SPECIFICATION_FILE = 'snowflake-container-config.yml'
  MIN_INSTANCES = 1
  MAX_INSTANCES = 3;

-- Start the services
ALTER SERVICE skillpathai_backend RESUME;
ALTER SERVICE skillpathai_frontend RESUME;

-- Get the service URLs
SELECT SYSTEM$GET_SERVICE_URL('skillpathai_backend');
SELECT SYSTEM$GET_SERVICE_URL('skillpathai_frontend'); 