"""
Session Manager with Redis and File-based Storage Support
Handles session persistence for multi-user concurrent access
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import Redis, fall back gracefully
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using file-based sessions")


class SessionManager:
    """
    Manages user sessions with Redis (preferred) or file-based storage (fallback).

    Usage:
        manager = SessionManager(redis_url=os.getenv('REDIS_URL'))
        manager.save_session(session_id, data)
        data = manager.load_session(session_id)
    """

    def __init__(self, redis_url: Optional[str] = None, file_folder: Path = Path('/tmp/sessions')):
        """
        Initialize session manager with Redis or file-based storage.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
            file_folder: Fallback folder for file-based sessions
        """
        self.redis_client = None
        self.file_folder = file_folder
        self.storage_type = 'file'  # Default to file-based

        # Try to connect to Redis if URL provided
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False,  # We'll handle JSON encoding
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                self.storage_type = 'redis'
                logger.info(f"✓ Connected to Redis: {redis_url.split('@')[0]}@***")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
                logger.warning("Falling back to file-based sessions")
                self.redis_client = None

        # Set up file-based storage folder if using files
        if self.storage_type == 'file':
            self.file_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using file-based sessions: {self.file_folder}")

    def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Save session data.

        Args:
            session_id: Unique session identifier
            data: Session data dictionary

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_data = json.dumps(data)

            if self.storage_type == 'redis' and self.redis_client:
                # Store in Redis with 24-hour expiration
                self.redis_client.setex(
                    f"session:{session_id}",
                    24 * 60 * 60,  # 24 hours in seconds
                    json_data
                )
                logger.debug(f"Session {session_id[:8]}... saved to Redis")
            else:
                # Store in file
                session_file = self.file_folder / f"{session_id}.json"
                with open(session_file, 'w') as f:
                    f.write(json_data)
                logger.debug(f"Session {session_id[:8]}... saved to {session_file}")

            return True

        except Exception as e:
            logger.error(f"Failed to save session {session_id[:8]}...: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data.

        Args:
            session_id: Unique session identifier

        Returns:
            dict: Session data if found, None otherwise
        """
        try:
            if self.storage_type == 'redis' and self.redis_client:
                # Load from Redis
                json_data = self.redis_client.get(f"session:{session_id}")
                if json_data:
                    return json.loads(json_data)
                else:
                    logger.debug(f"Session {session_id[:8]}... not found in Redis")
                    return None
            else:
                # Load from file
                session_file = self.file_folder / f"{session_id}.json"
                if not session_file.exists():
                    logger.debug(f"Session {session_id[:8]}... not found at {session_file}")
                    return None

                with open(session_file, 'r') as f:
                    return json.load(f)

        except Exception as e:
            logger.error(f"Failed to load session {session_id[:8]}...: {e}")
            return None

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if session exists, False otherwise
        """
        if self.storage_type == 'redis' and self.redis_client:
            return bool(self.redis_client.exists(f"session:{session_id}"))
        else:
            return (self.file_folder / f"{session_id}.json").exists()

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.storage_type == 'redis' and self.redis_client:
                self.redis_client.delete(f"session:{session_id}")
            else:
                session_file = self.file_folder / f"{session_id}.json"
                if session_file.exists():
                    session_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id[:8]}...: {e}")
            return False

    def get_storage_type(self) -> str:
        """Get the current storage backend type."""
        return self.storage_type
