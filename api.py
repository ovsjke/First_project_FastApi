from fastapi import FastAPI, HTTPException
from routers import auth
from routers import teacher
from middleware import register_middlewares
from exception import global_http_exception_handler
from routers import student
from routers import admin


def create_app():
    '''
    подключение модулей к приложению
    '''
    app = FastAPI(
        title = "LMS System",
        description= "Система управления тестирования"
    )
    app.include_router(admin.router)
    app.include_router(teacher.router)
    app.include_router(auth.router)
    app.include_router(student.router)
    app.add_exception_handler(HTTPException, global_http_exception_handler)
    register_middlewares(app)
    return app

