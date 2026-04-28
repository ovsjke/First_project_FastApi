from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from database.database_config import get_session
from database.models import User
from utils import check_password, jwt_decode, jwt_encode

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_session)):
    """
    Метод для получения экземпляра текущего юзера из заголовка JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Токен неверный или истек",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = jwt_decode(token)
    if isinstance(payload, str) or payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    summary="Авторизация",
    description="Авторизаця пользователя по логину и паролю",
)
def auth_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_session)
):
    user = db.query(User).filter(User.login == form_data.username).first()
    if (
        not user
        or user.soft_delete
        or not check_password(user.password, form_data.password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Неверный логин или пароль: {form_data.username}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = jwt_encode(user_id=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}
