"""RBAC dependencies for FastAPI routes (Section 56/87).

Roles:
  ADMIN      - full access, including user management and audit logs
  RESEARCHER - can create/approve projects, hypotheses, experiments
  VIEWER     - read-only access

Every mutating endpoint declares its minimum required role explicitly;
there is no implicit "authenticated == authorized" assumption.
"""

from typing import Iterable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.security.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*roles: Iterable[Role]):
    allowed = set(roles)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not permitted to perform this action",
            )
        return user

    return dependency


require_admin = require_roles(Role.ADMIN)
require_researcher = require_roles(Role.ADMIN, Role.RESEARCHER)
require_any = require_roles(Role.ADMIN, Role.RESEARCHER, Role.VIEWER)
