from typing import List
from enum import Enum
from fastapi import HTTPException, Depends
from app.models.models import User
from app.api.endpoints.auth import get_current_user

class Role(str, Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    ANALYST = "analyst"
    VIEWER = "viewer"

class RBAC:
    """
    Enterprise Role Based Access Control middleware.
    """
    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        # In a real app, User model would have a 'role' field
        # For now, we'll check if the user exists and default to ADMIN for the first user
        # or implement a simple check if the field exists
        user_role = getattr(current_user, "role", Role.VIEWER)
        
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return True

# Predefined role dependencies
admin_only = RBAC([Role.ADMIN])
engineer_plus = RBAC([Role.ADMIN, Role.ENGINEER])
analyst_plus = RBAC([Role.ADMIN, Role.ENGINEER, Role.ANALYST])
