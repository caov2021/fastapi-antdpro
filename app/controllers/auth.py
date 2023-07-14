from pydantic import EmailStr

from app.models import User
from app.repositories import UserRepository
from app.schemas.extras.token import Token
from core.controller import BaseController
from core.database import Propagation, Transactional
from core.exceptions import BadRequestException, UnauthorizedException
from core.security import JWTHandler, PasswordHandler


class AuthController(BaseController[User]):
    def __init__(self, user_repository: UserRepository):
        super().__init__(model=User, repository=user_repository)
        self.user_repository = user_repository

    @Transactional(propagation=Propagation.REQUIRED)
    async def register(self, email: EmailStr, password: str, username: str) -> User:
        # Check if user exists with email
        user = await self.user_repository.get_by_email(email)

        if user:
            raise BadRequestException("User already exists with this email")

        # Check if user exists with username
        user = await self.user_repository.get_by_username(username)

        if user:
            raise BadRequestException("User already exists with this username")

        password = PasswordHandler.hash(password)

        return await self.user_repository.create(
            {
                "email": email,
                "password": password,
                "username": username,
            }
        )

    @Transactional(propagation=Propagation.REQUIRED)
    async def change_password(self, username: str, old_password: str, new_password: str) -> User:
        user = await self.user_repository.get_by_username(username)

        if not user:
            raise BadRequestException("User does not exist!")

        if not PasswordHandler.verify(user.password, old_password):
            raise BadRequestException("Old password is incorrect!")

        if PasswordHandler.verify(user.password, new_password):
            raise BadRequestException("New password can't be the same as the old one!")

        user.password = PasswordHandler.hash(new_password)
        return user

    async def login(self, email: EmailStr, password: str) -> Token:
        user = await self.user_repository.get_by_email(email)

        if not user:
            raise BadRequestException(f"User `{email}` does not exist!")

        if not PasswordHandler.verify(user.password, password):
            raise BadRequestException("User Password is incorrect, please try again!")

        if not user.is_active:
            raise BadRequestException("User is not active, please contact the administrator!")

        return Token(
            access_token=JWTHandler.encode(payload={"user_id": user.id}),
            refresh_token=JWTHandler.encode(payload={"sub": "refresh_token"}),
        )

    @staticmethod
    async def refresh_token(access_token: str, refresh_token: str) -> Token:
        token = JWTHandler.decode(access_token)
        refresh_token = JWTHandler.decode(refresh_token)
        if refresh_token.get("sub") != "refresh_token":
            raise UnauthorizedException("Invalid refresh token")

        return Token(
            access_token=JWTHandler.encode(payload={"user_id": token.get("user_id")}),
            refresh_token=JWTHandler.encode(payload={"sub": "refresh_token"}),
        )
