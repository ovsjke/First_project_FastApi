from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database.database_config import get_session
from database.models import Group, Question, Test, User, Attempt
from routers.auth import get_current_user

from sqlalchemy import desc


class AddOrEditTestSchema(BaseModel):
    title: str = Field(...,description="Описание теста")
    max_attemp: int = Field(default=1, description="Максимальное количество попыток")


class AddOrEditQuestionSchema(BaseModel):
    test_id: int = Field(...,description="К какому id теста привязан вопрос")
    description: str = Field(...,description="Описание вопроса")
    point: float = Field(..., gt=0, le=1,description="Количество баллов за ответ")
    answer: str = Field(...,description="Правильный ответ на тест")


router = APIRouter(prefix="/teacher", tags=["teacher"])


def get_test_to_test_id(test_id: int, db):
    test = db.query(Test).filter(Test.id == test_id, Test.soft_delete != 1).first()
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
        )
    return test


def get_group_to_group_id(group_id: int, db):
    group = db.query(Group).filter(Group.id == group_id, Group.soft_delete != 1).first()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    return group


def check_test_id_to_user_id(test_id: int, user_id: int, db):

    test = get_test_to_test_id(test_id, db)
    group = get_group_to_group_id(test.group_id, db)
    if group.teacher_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User Not Have a Right"
        )


def check_role(role: str):
    if role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User Not Have a Right"
        )


def get_groups_to_user_id(user_id: int, db):
    groups = (
        db.query(Group)
        .filter(Group.teacher_id == user_id, Group.soft_delete != 1)
        .all()
    )
    if not groups:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    return groups


def get_group_to_user_id(user_id: int, db):
    group = (
        db.query(Group)
        .filter(Group.teacher_id == user_id, Group.soft_delete != 1)
        .first()
    )
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    return group


def get_tests_to_group_id(group_id, db):
    tests = (
        db.query(Test).filter(Test.group_id == group_id, Test.soft_delete != 1).all()
    )
    if not tests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
        )
    return tests


def get_attemps_desc(attemp_id: int, db):
    attemps = (
        db.query(Attempt)
        .filter(Attempt.test_id == attemp_id)
        .order_by(Attempt.user_id, desc(Attempt.result))
        .all()
    )
    if not attemps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attemps not found"
        )
    return attemps


def get_question(question_id: int, db):
    question = (
        db.query(Question)
        .filter(Question.id == question_id, Question.soft_delete != 1)
        .first()
    )
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="question not found"
        )
    return question


@router.post("/add_test",
    summary="Добавить тест тестов",
    description="Добавление нового теста с описанием  максимальным количеством попыток",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Нет доступных результов"}
    })
def add_test(
    add_test: AddOrEditTestSchema,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    check_role(current_user.role)
    groups = get_groups_to_user_id(current_user.id, db)
    for group in groups:
        test = Test(
            title=add_test.title, group_id=group.id, max_attemp=add_test.max_attemp
        )
        db.add(test)
    db.commit()
    return {"message": "ok"}


@router.get(
    "/result",
    summary="Результаты тестов",
    description="Просмотр результатов тестирования студентов",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Нет доступных результов"}
    }
)
def all_test(current_user: User = Depends(get_current_user), db=Depends(get_session)):
    check_role(current_user.role)
    test_list = []
    group = get_group_to_user_id(current_user.id, db)
    tests = get_tests_to_group_id(group.id, db)
    for test in tests:
        test_list.append(
            {"id": test.id, "title": test.title, "attempt": test.max_attemp}
        )
    return test_list


@router.get("/result/{test_id}",
    summary="Результаты тестов",
    description="Просмотр результатов тестирования одного теста",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Нет доступных результов"}
    })
def result_single_test(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    result_attemp = []
    check_role(current_user.role)
    check_test_id_to_user_id(test_id, current_user.id, db)
    attemps = get_attemps_desc(test_id, db)
    for attemp in attemps:
        result_attemp.append(
            {
                "id": attemp.id,
                "user_id": attemp.user_id,
                "result": attemp.result,
                "date": attemp.date,
            }
        )
    return result_attemp


@router.post(
    "/add_question",
    summary="Добавление нового теста",
    description="Создание нового теста с вводов описания, правильного ответа и количества баллов",
    responses = {
        403: {"description": "Отказано в доступе"},
    }
)
def add_question(
    question: AddOrEditQuestionSchema,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    check_role(current_user.role)
    check_test_id_to_user_id(question.test_id, current_user.id, db)
    question = Question(
        test_id=question.test_id,
        description=question.description,
        point=question.point,
        answer=question.answer,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.put(
    "/edit_test/{test_id}",
    summary="Изменений теста",
    description="Измненеий теста по указанному id: название и количество попыток",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Тест не найден"}
    }
)
def edit_test(
    test_id: int,
    new_data_test: AddOrEditTestSchema,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    check_test_id_to_user_id(test_id, current_user.id, db)
    check_role(current_user.role)
    test = get_test_to_test_id(test_id, db)
    test.title = new_data_test.title
    test.max_attemp = new_data_test.max_attemp
    db.commit()
    return {"message": "Test edit successfully"}


@router.put(
    "/edit_question/{question_id}",
    summary="Изменений вопроса",
    description="Измненеий теста по указанному id: описание, принадлежность к тесту, правильный ответ и количество баллов",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Вопрос не найден"}
    }
)
def edit_question(
    question_id: int,
    new_question_data: AddOrEditQuestionSchema,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    check_role(current_user.role)
    question = get_question(question_id, db)
    check_test_id_to_user_id(new_question_data.test_id, current_user.id, db)
    question.test_id = new_question_data.test_id
    question.description = new_question_data.description
    question.point = new_question_data.point
    question.answer = new_question_data.answer
    db.commit()
    return {"message": "Question edit successfully"}


@router.delete(
    "/delete_test/{test_id}",
    summary="Удаление теста",
    description="Удаление теста по указанному id. Удаление происходит логически путем изменений флага soft_delete",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Тест не найден"}
    }
)
def delete_test(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    check_role(current_user.role)
    check_test_id_to_user_id(test_id, current_user.id, db)
    test = get_test_to_test_id(test_id, db)
    test.soft_delete = 1
    db.commit()
    return {"message": "Test deleted successfully"}


@router.delete(
    "/delete_question/{question_id}",
    summary="Удаление вопроса",
    description="Удаление вопроса по указанному id. Удаление происходит логически путем изменений флага soft_delete",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Вопрос не найден"}
    }
)
def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    question = get_question(question_id, db)
    check_role(current_user.role)
    check_test_id_to_user_id(question.test_id, current_user.id, db)
    question.soft_delete = 1
    db.commit()
    return {"message": "Question deleted successfully"}
