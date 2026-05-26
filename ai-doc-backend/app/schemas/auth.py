from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    company_name: str = Field(default="", max_length=128)
    phone: str = Field(default="", max_length=32)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginByCodeRequest(BaseModel):
    access_code: str = Field(..., min_length=1, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    username: str
    company_name: str

    class Config:
        from_attributes = True
