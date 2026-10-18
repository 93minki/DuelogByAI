from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.auth.deps import CurrentUser, SessionDep
from app.auth.security import create_token, hash_password, verify_password
from app.config import get_settings
from app.models import User
from app.schemas import Credentials, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.cookie_name,
        create_token(user.id),
        max_age=settings.jwt_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(body: Credentials, response: Response, session: SessionDep) -> User:
    exists = await session.scalar(select(User.id).where(User.email == body.email))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 가입된 이메일입니다.")
    user = User(email=body.email, password_hash=hash_password(body.password))
    session.add(user)
    await session.commit()
    _set_auth_cookie(response, user)
    return user


@router.post("/login", response_model=UserOut)
async def login(body: Credentials, response: Response, session: SessionDep) -> User:
    user = await session.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다.")
    _set_auth_cookie(response, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(get_settings().cookie_name, path="/")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> User:
    return user
