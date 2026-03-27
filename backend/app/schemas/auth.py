from pydantic import BaseModel, EmailStr

from app.schemas.user import UserReadWithTenant


class RegisterRequest(BaseModel):
    naziv_klinike: str
    vrsta: str = "ordinacija"
    email: EmailStr
    password: str
    ime: str
    prezime: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserReadWithTenant | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
