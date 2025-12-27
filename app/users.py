import uuid
from typing import Optional
from fastapi import Depends,Request
from fastapi_users import BaseUserManager,FastAPIUsers,UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy
)
from fastapi_users.db import SQLAlchemyUserDatabase
from app.db import User, get_user_db
from dotenv import load_dotenv
import os

load_dotenv()

SECRET=os.getenv("JWT_SECRET")

class UserManager(UUIDIDMixin,BaseUserManager[User,uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
            print(f"User {user.id} has registered")
    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        print(f"User {user.id} has forgot their password. Reset token:{token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        print(f"Verification requested for user {user.id}. Verification token:{token}")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)