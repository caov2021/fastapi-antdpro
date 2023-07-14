from typing import Callable

from fastapi import APIRouter, Depends

from app.controllers import AuthController, UserController
from app.models.user import User, UserPermission
from app.schemas.extras.token import Token
from app.schemas.requests.users import (
    LoginUserRequest,
    RegisterUserRequest,
    UpdateUserRequest,
    AddUserRequest,
)
from app.schemas.responses.users import UserResponse, UserDetailResponse
from core.exceptions import NotFoundException
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired
from core.fastapi.dependencies.current_user import get_current_user
from core.fastapi.dependencies.permissions import Permissions

user_router = APIRouter()


@user_router.post("/register", status_code=201)
async def register_user(
    register_user_request: RegisterUserRequest,
    auth_controller: AuthController = Depends(Factory().get_auth_controller),
) -> UserResponse:
    return await auth_controller.register(
        email=register_user_request.email,
        password=register_user_request.password,
        username=register_user_request.username,
    )


@user_router.post("/login")
async def login(
    login_user_request: LoginUserRequest,
    auth_controller: AuthController = Depends(Factory().get_auth_controller),
) -> Token:
    return await auth_controller.login(email=login_user_request.email, password=login_user_request.password)


@user_router.get("/me", dependencies=[Depends(AuthenticationRequired)])
def get_user(
    user: User = Depends(get_current_user),
) -> UserDetailResponse:
    return user


@user_router.get("/", dependencies=[Depends(AuthenticationRequired)])
async def get_users(
    user_controller: UserController = Depends(Factory().get_user_controller),
    assert_access: Callable = Depends(Permissions(UserPermission.READ)),
) -> list[UserDetailResponse]:
    users = await user_controller.get_all()

    assert_access(resource=users)
    return users


@user_router.post("/", status_code=201, dependencies=[Depends(AuthenticationRequired)])
async def add_user(
    add_user_request: AddUserRequest,
    user_controller: UserController = Depends(Factory().get_user_controller),
) -> UserDetailResponse:
    return await user_controller.create(attributes=dict(add_user_request.model_dump()))


@user_router.get("/{user_id}", dependencies=[Depends(AuthenticationRequired)])
async def get_user_by_id(
    user_id: int,
    user_controller: UserController = Depends(Factory().get_user_controller),
    assert_access: Callable = Depends(Permissions(UserPermission.READ)),
) -> UserDetailResponse:
    user = await user_controller.get_by_id(id_=user_id)

    assert_access(resource=user)
    return user


@user_router.put("/{user_id}", dependencies=[Depends(AuthenticationRequired)])
async def update_user_info_by_id(
    user_id: int,
    update_user_request: UpdateUserRequest,
    user_controller: UserController = Depends(Factory().get_user_controller),
    assert_access: Callable = Depends(Permissions(UserPermission.EDIT)),
) -> UserResponse:
    user = await user_controller.get_by_id(user_id)
    if not user:
        raise NotFoundException(f"User not found!")

    assert_access(resource=user)
    return await user_controller.update_by_id(id_=user_id, attributes=update_user_request.model_dump())


@user_router.delete("/{user_id}", dependencies=[Depends(AuthenticationRequired)])
async def delete_user_by_id(
    user_id: int,
    user_controller: UserController = Depends(Factory().get_user_controller),
    assert_access: Callable = Depends(Permissions(UserPermission.DELETE)),
) -> bool:
    del_user = await user_controller.get_by_id(user_id)
    if not del_user:
        raise NotFoundException(f"User (id={user_id}) not found!")
    assert_access(resource=del_user)
    return await user_controller.delete(del_user)
