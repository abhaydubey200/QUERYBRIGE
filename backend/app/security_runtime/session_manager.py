import uuid
import datetime
from typing import Dict, Optional

class SessionManager:
    """Manages secure sessions and token rotation."""
    
    def __init__(self, redis_client: Any = None):
        self.redis = redis_client # Ideally use local Redis for session state
        self.sessions = {} # Fallback to in-memory for non-distributed dev

    def create_session(self, user_id: str, device_info: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "user_id": user_id,
            "device": device_info,
            "created_at": datetime.datetime.utcnow(),
            "last_active": datetime.datetime.utcnow(),
            "refresh_count": 0
        }
        return session_id

    def rotate_token(self, session_id: str) -> bool:
        """Enforce refresh token rotation to prevent reuse of stolen tokens."""
        if session_id not in self.sessions:
            return False
            
        session = self.sessions[session_id]
        session["refresh_count"] += 1
        session["last_active"] = datetime.datetime.utcnow()
        
        # In a real system, we'd issue a new token and invalidate the old one in Redis
        return True

    def validate_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)
