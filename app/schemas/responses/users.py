from pydantic import UUID4, BaseModel, Field


class UserResponse(BaseModel):
    email: str = Field(..., example="john.doe@example.com")
    username: str = Field(..., example="john.doe")
    uuid: UUID4 = Field(..., example="a3b8f042-1e16-4f0a-a8f0-421e16df0a2f")

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    id: int = Field(..., example=1)
    uuid: UUID4 = Field(..., example="a3b8f042-1e16-4f0a-a8f0-421e16df0a2f")
    username: str = Field(..., example="john.doe")
    email: str = Field(..., example="john.doe@example.com")
    is_admin: bool = Field(..., example=False)
    is_active: bool = Field(..., example=True)

    class Config:
        from_attributes = True
