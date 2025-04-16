"""
A connection pool implementation for Snowflake connections.
This helps manage database connections more efficiently and avoid connection issues.
"""

import logging
import threading
import time
from typing import Dict, Optional, Any
from backend.database import get_snowflake_connection

logger = logging.getLogger(__name__)

class ConnectionPool:
    """
    A simple connection pool for Snowflake connections that helps
    manage connections and avoid connection exhaustion issues.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement as singleton to ensure only one pool exists"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConnectionPool, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the connection pool once"""
        if self._initialized:
            return
            
        self._connections = {}
        self._in_use = {}
        self._max_connections = 5
        self._timeout = 30  # seconds
        self._connection_ttl = 300  # 5 minutes max lifetime for a connection
        self._initialized = True
        logger.info(" ConnectionPool initialized")
    
    def get_connection(self) -> Any:
        """
        Get a connection from the pool or create a new one if needed.
        
        Returns:
            Snowflake connection object
        """
        with self._lock:
            # First, clean up any stale connections
            self._cleanup_stale_connections()
            
            # Check if we have any available connections
            for conn_id, conn in self._connections.items():
                if conn_id not in self._in_use:
                    logger.debug(f"Reusing existing connection {conn_id}")
                    self._in_use[conn_id] = time.time()
                    return conn
            
            # If we've reached max connections, wait for one to be released
            if len(self._connections) >= self._max_connections:
                logger.warning(f"Connection pool full ({len(self._connections)}/{self._max_connections}). Waiting for available connection.")
                return self._wait_for_connection()
            
            # Create a new connection
            try:
                conn = get_snowflake_connection()
                if not conn:
                    raise Exception("Failed to get Snowflake connection")
                
                conn_id = id(conn)
                self._connections[conn_id] = conn
                self._in_use[conn_id] = time.time()
                logger.debug(f"Created new connection {conn_id}")
                return conn
            except Exception as e:
                logger.error(f"Error creating connection: {str(e)}")
                raise
    
    def release_connection(self, conn: Any) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            conn: The connection to release
        """
        if not conn:
            return
            
        conn_id = id(conn)
        with self._lock:
            if conn_id in self._in_use:
                del self._in_use[conn_id]
                logger.debug(f"Released connection {conn_id}")
            else:
                logger.warning(f"Connection {conn_id} not found in in_use list")
    
    def close_all_connections(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for conn_id, conn in list(self._connections.items()):
                try:
                    conn.close()
                    logger.debug(f"Closed connection {conn_id}")
                except Exception as e:
                    logger.error(f"Error closing connection {conn_id}: {str(e)}")
                    
            self._connections.clear()
            self._in_use.clear()
            logger.info("Closed all connections in the pool")
    
    def _wait_for_connection(self) -> Optional[Any]:
        """
        Wait for a connection to become available.
        
        Returns:
            Snowflake connection object or None if timeout
        """
        start_time = time.time()
        while time.time() - start_time < self._timeout:
            # Release the lock temporarily to allow other threads to release connections
            self._lock.release()
            time.sleep(0.1)  # Short sleep to prevent CPU spinning
            self._lock.acquire()
            
            # Try to find an available connection
            for conn_id, conn in self._connections.items():
                if conn_id not in self._in_use:
                    logger.debug(f"Found available connection {conn_id} after waiting")
                    self._in_use[conn_id] = time.time()
                    return conn
        
        # If we get here, we timed out
        logger.error("Timed out waiting for connection")
        raise TimeoutError("Timed out waiting for database connection")
    
    def _cleanup_stale_connections(self) -> None:
        """Close and remove connections that have been alive too long."""
        current_time = time.time()
        conn_creation_times = {
            conn_id: self._in_use.get(conn_id, current_time - self._connection_ttl - 1)
            for conn_id in list(self._connections.keys())
        }
        
        for conn_id, creation_time in conn_creation_times.items():
            # If connection is too old or has been in use too long
            if current_time - creation_time > self._connection_ttl:
                try:
                    conn = self._connections[conn_id]
                    conn.close()
                    logger.debug(f"Closed stale connection {conn_id}")
                except Exception as e:
                    logger.error(f"Error closing stale connection {conn_id}: {str(e)}")
                
                # Remove from pool
                self._connections.pop(conn_id, None)
                self._in_use.pop(conn_id, None)