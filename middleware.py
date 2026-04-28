from fastapi import FastAPI, Request, Response
from typing import Callable, Awaitable
from database.database_config import SessionLocal
from utils import request_decode_jwt
import re
from logs import create_log
from loguru import logger
import time

#описание роутеров
routes_descriptions = {
    ("/student", "GET"): "Запросил доступные тесты из БД",
    ("/student/submit_test", "POST"): "Послал ответ на тест в БД",
    ("/admin/add_user", "POST"): "Запросил создание нового пользователя в БД",
    ("/admin/add_group", "POST"): "Запросил создание новой группы в БД",
    ("/teacher/add_test", "POST"): "Запросил создание нового тест в БД",
    ("/teacher/add_question", "POST"): "Запросил создание нового вопроса в БД",
    (r"/teacher/delete_test/(\d+)", "DELETE"): "Запросил удаление теста из БД id: {0}",
    (r"/teacher/delete_question/(\d+)", "DELETE"): "Запросил удаление из БД id: {0}"
}




def get_action_description(path: str, method: str) -> str:
    '''
    метод для получение описания для роутера
    '''
    for (pattern, route_method), description in routes_descriptions.items():
        if method != route_method:
            continue
        if r"(\d+)" in pattern:
            match = re.fullmatch(pattern, path)
            if match:
                return description.format(*match.groups())
        elif path == pattern:
            return description
        return f"Запрос на {path}"

def register_middlewares(app:FastAPI) -> None:
    @app.middleware('http')
    async def log_new_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        '''
        логика мидлваря
        нужен для записи логов в БД
        '''
        start_time = time.perf_counter()
        response = await call_next(request)
        path = request.url.path
        method = request.method
        status_code = response.status_code

        description = get_action_description(path,method)
        if description is not None:
            payload = request_decode_jwt(request)
            current_user_id = payload.get("sub") if payload else None
            db = SessionLocal()
            try:
                new_log = create_log(
                    user_id = int(current_user_id) if current_user_id else None,
                    method = method,
                    path = path,
                    status_code = status_code,
                    description = description
                )
                db.add(new_log)
                db.commit()
            except Exception as e:
                print(f"Ошибка при записи лога: {e}")
            finally:
                db.close()
        process_time = (time.perf_counter() - start_time)*1000
        logger.info(
            f"{request.method} | {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.2f}ms"
        )
        return response
        