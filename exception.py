from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from database.database_config import SessionLocal
from logs import create_log
from utils import request_decode_jwt
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

async def global_http_exception_handler(request: Request, exc: HTTPException):
    '''
    обработчик ошибок
    '''
    payload = request_decode_jwt(request)
    user_id = int(payload.get("sub")) if payload else None
    db = SessionLocal()
    try:
        error_log = create_log(
            user_id = user_id,
            method = request.method,
            path = request.url.path,
            status_code = exc.status_code,
            description = f"Error: {exc.detail}"
        )
        db.add(error_log)
        db.commit()
    except SQLAlchemyError:
        logger.exception("DB commit error")
        db.rollback()
    except Exception as e:
        logger.exception(f"Invalid Error {e}")
    finally:
        db.close()
    logger.error(f"Error: {request.method} {request.url.path}, {exc.status_code}")
    return JSONResponse(
        status_code= exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code
        }
    )