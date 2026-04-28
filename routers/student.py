from datetime import datetime
from typing import Optional
from sqlalchemy import desc

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database.database_config import get_session
from database.models import Attempt, Question, Test, User
from routers.auth import get_current_user

router = APIRouter(prefix="/student", tags=["student"])


class TestSubmissionSchema(BaseModel):
    answer: dict[str, Optional[str]] = Field(...,description="Ввод ответа на тест")


def check_avalibity(group_id_test: int, group_id_user: int) -> bool:
    if group_id_test != group_id_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed"
        )


def check_max_attemp(user_id: int, test_id: int, max_attemp: int, db) -> bool:
    attemp = (
        db.query(Attempt)
        .filter(Attempt.user_id == user_id, Attempt.test_id == test_id)
        .count()
    )
    if attemp >= max_attemp:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Use all avilable attemp"
        )


def update_attempt(user_id: int, test_id: int, result: int, db):
    new_attempt = Attempt(
        user_id=user_id, test_id=test_id, result=result, date=datetime.utcnow()
    )
    db.add(new_attempt)
    db.commit()
    db.refresh(new_attempt)
    return {"detail": "okay"}


def get_tests(group_id, db):
    tests = (
        db.query(Test).filter(Test.group_id == group_id, Test.soft_delete != 1).all()
    )
    if not tests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
        )
    return tests


def get_test(id: int, db):
    test = db.query(Test).filter(Test.id == id, Test.soft_delete != 1).first()
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test not found"
        )
    return test


def get_questions(test_id: int, db):
    questions = (
        db.query(Question)
        .filter(Question.test_id == test_id, Question.soft_delete != 1)
        .all()
    )
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not find a question"
        )
    return questions


def get_attemps_to_user_id(id: int, db):
    attemps = (
        db.query(Attempt)
        .filter(Attempt.user_id == id)
        .order_by(desc(Attempt.result))
        .all()
    )
    if not attemps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempts not found"
        )
    return attemps


def get_attemps_to_user_and_attemp_id(user_id: int, attemp_id: int, db):
    attemps = (
        db.query(Attempt)
        .filter(Attempt.test_id == attemp_id, Attempt.user_id == user_id)
        .order_by(desc(Attempt.date))
        .all()
    )
    if not attemps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attemp not found"
        )
    return attemps


@router.get(
    "/test",
    summary="Получение доступных тестов",
    description="Получение доступных для пользователя тестов, исходя из его группы и совершенных попыток для тестов",
    
)
def avilable_test(
    current_user: User = Depends(get_current_user), db=Depends(get_session)
):
    tests = get_tests(current_user.group_id, db)
    result = []

    for test in tests:
        attempts = (
            db.query(Attempt)
            .filter(Attempt.user_id == current_user.id, Attempt.test_id == test.id)
            .count()
        )
        questions = (
            db.query(Question)
            .filter(Question.test_id == test.id, Question.soft_delete != 1)
            .all()
        )
        if test.soft_delete == 1:
            continue
        if not questions:
            continue
        if attempts >= test.max_attemp:
            continue
        result.append({"id": test.id, "title": test.title})
    return result


@router.get(
    "/result",
    summary="Результаты тестов",
    description="Отображение результатов тестов, с группировкой по максимальному баллу",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Нет доступных результов"}
    }
)
def result_all_test(
    current_user: User = Depends(get_current_user), db=Depends(get_session)
):
    result_map = {}
    attemps = get_attemps_to_user_id(current_user.id, db)
    for attemp in attemps:
        if attemp.test_id not in result_map:
            test = db.query(Test).filter(Test.id == attemp.test_id).first()
            result_map[attemp.test_id] = {
                "test_id": attemp.test_id,
                "название": test.title,
                "лучшая попытка": attemp.result,
            }
    return list(result_map.values())


@router.get(
    "/result/{id}",
    summary="Результаты одного теста",
    description="Просмотр истории результатов одного выбранного теста",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Нет доступных результов"}
    }
)
def result_single_test(
    id: int, current_user: User = Depends(get_current_user), db=Depends(get_session)
):
    result = []
    attemps = get_attemps_to_user_and_attemp_id(current_user.id, id, db)
    count = 1
    for attemp in attemps:
        result.append({"attemtp": count, "result": attemp.result, "date": attemp.date})
        count += 1
    return result


@router.get(
    "/test/{id}",
    summary="Начало теста",
    description="Вывод всех вопросов для выбранного теста",
    responses = {
        403: {"description": "Отказано в доступе"},
        404: {"description": "Нет доступных тестов"}
    }
)
def start_test(
    id: int, current_user: User = Depends(get_current_user), db=Depends(get_session)
):
    test = get_test(id, db)
    check_max_attemp(current_user.id, test.id, test.max_attemp, db)
    check_avalibity(test.group_id, current_user.group_id)
    questions = get_questions(test.id, db)
    question_list = [
        {"id": question.id, "description": question.description}
        for question in questions
        if question.soft_delete != 1
    ]
    return {"id": test.id, "title": test.title, "questions": question_list}


@router.post(
    "/submit_test/{id}",
    summary="Отправка ответа на тест",
    description="Проверка введеных пользователем ответов, с дальнейшим расчетом количества баллов и записи попытки в базу данных",responses = {
        403: {"description": "Отказано в доступе"},
    }
)
def submit_test(
    id: int,
    submission: TestSubmissionSchema,
    current_user: User = Depends(get_current_user),
    db=Depends(get_session),
):
    test = get_test(id, db)
    questions = get_questions(test.id, db)
    check_avalibity(test.group_id, current_user.group_id)
    score = 0
    for question in questions:
        if question.soft_delete == 1:
            continue
        if question.answer == submission.answer.get(str(question.id)):
            score += question.point
    update_attempt(current_user.id, id, score, db)
    return {"status": "ok", "score": score}
