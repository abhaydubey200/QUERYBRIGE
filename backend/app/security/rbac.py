from fastapi import Request, HTTPException, Depends
from app.security.auth import get_current_user
from app.models.models import User
from typing import List
import enum

class Role(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    ANALYST = "analyst"
    VIEWER = "viewer"

class RBACManager:
    """
    Enterprise Role-Based Access Control Manager.
    """
    PERMISSIONS = {
        "connections:create": [Role.ADMIN, Role.ENGINEER],
        "connections:delete": [Role.ADMIN],
        "query:execute": [Role.ADMIN, Role.ENGINEER, Role.ANALYST],
        "dashboard:create": [Role.ADMIN, Role.ENGINEER, Role.ANALYST],
        "ai:use": [Role.ADMIN, Role.ENGINEER, Role.ANALYST],
        "system:settings": [Role.ADMIN]
    }

    @staticmethod
    def check_permission(user: User, permission: str):
        allowed_roles = RBACManager.PERMISSIONS.get(permission, [])
        if user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=403, 
                detail=f"Missing permission: {permission}. Required roles: {[r.value for r in allowed_roles]}"
            )

def require_permission(permission: str):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        RBACManager.check_permission(current_user, permission)
        return current_user
    return permission_checker
