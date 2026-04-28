from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator

from database.database_config import get_session
from database.models import Group, User
from routers.auth import get_current_user
from utils import set_password


class AddUserSchema(BaseModel):
    role: Literal["admin", "teacher", "student"] = Field(...,description= "Выбор роли пользователя")
    login: str = Field(..., min_length=3, max_length=15,description="Указание роли пользователя")
    password: str = Field(..., min_length=4,description="Установка пароля")
    group_id: int | None = None 

    @field_validator("login") 
    @classmethod
    def validate_login(cls, value):
        if " " in value:
            raise ValueError("Login should not contain spaces")
        return value

    @model_validator(mode="after")
    def validate_password(self):
        if self.login == self.password:
            raise ValueError("Password should not be the same as login")
        return self


class AddGroupSchema(BaseModel): 
    name: str = Field(...,description="Название группы")
    teacher_id: int = Field(...,description="id учителя, за которым закреплена группа")


def check_role(role: str):
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not have a rights"
        )


def existing_user(login: str, db):
    existing_user = db.query(User).filter(User.login == login).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User does exist"
        )


def get_user(id: int, db):
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_group(id: int, db):
    group = db.query(Group).filter(Group.id == id).first()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    return group


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/add_user",
    summary="Добавление Пользователя",
    description="Создание нового пользователя: установка логина и пароля",
    responses = {
        403: {"description": "Отказано в доступе"},
        409: {"description": "Пользователь уже существует"}
    }
)
def add_user(
    setting_user: AddUserSchema,
    current_user=Depends(get_current_user),
    db=Depends(get_session),
):
    check_role(current_user.role)
    existing_user(setting_user.login, db)
    hash_password = set_password(setting_user.password)
    new_user = User(
        role=setting_user.role,
        login=setting_user.login,
        password=hash_password,
        group_id=setting_user.group_id if setting_user.role == "student" else 0,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User added successfully"}


@router.post(
    "/add_group",
    summary="Добавление новой группы",
    description="Добавление новой группы. Названия могут быть не уникальны",
    responses = {
        403: {"description": "Отказано в доступе"},
    }
)
def add_group(
    setting_group: AddGroupSchema,
    current_user=Depends(get_current_user),
    db=Depends(get_session),
):
    check_role(current_user.role)
    new_group = Group(name=setting_group.name, teacher_id=setting_group.teacher_id)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return {"message": "Group added successfully"}


@router.delete(
    "/delete_user/{id}",
    summary="Удаление пользователя",
    description="Удаление пользователя по переданному id. Удаление логическое, с помощью флага soft_delete в БД",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Пользователь не найден"}
    }
)
def delete_user(
    id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_session),
):
    check_role(current_user.role)
    user = get_user(id, db)
    user.soft_delete = 1
    db.commit()
    return {"message": "User deleted successfully"}


@router.delete(
    "/delete_group/{id}",
    summary="Удаление группы",
    description="Удаление группы по переданному id. Удаление логическое, с помощью флага soft_delete в БД",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Группа не найдена"}
    }
)
def delete_group(
    id: int, current_user=Depends(get_current_user), db=Depends(get_session)
):
    check_role(current_user.role)
    group = get_group(id, db)
    group.soft_delete = 1
    db.commit()
    return {"message": "Group deleted successfully"}
